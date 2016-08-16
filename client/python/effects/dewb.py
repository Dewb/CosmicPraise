from __future__ import division
from itertools import chain, islice, imap
import color_utils
import time
import random


colormath_support = True
try:
    from colormath.color_objects import *
    from colormath.color_conversions import convert_color
except ImportError:
    colormath_support = False

from math import pi, sqrt, cos, sin, atan2, log
twopi = 2 * pi

__all__ = ["spotStrobe", "spotColor", "demoEffect", "alignTestEffect", "verySimpleExampleEffect"]

def spotStrobe(tower, state, speed=0.0):
   frames = int(speed * 120) + 2
   color = (0, 0, 0)
   if state.frame % frames < frames/2:
      color = (1, 1, 1)
   for pixel in tower.spotlight:
      tower.set_pixel_rgb(pixel, color)

def spotColor(tower, state, chroma = 0.0, luma=1.0):
   for pixel in tower.spotlight:
      tower.set_pixel(pixel, chroma, luma)

def scaledRGBTupleToHSL(s):
    rgb = sRGBColor(s[0], s[1], s[2], True)
    return convert_color(rgb, HSLColor)
    
def HSLToScaledRGBTuple(hsl):
    return convert_color(hsl, sRGBColor).get_value_tuple()

def cartesianToCylinderDistanceSquared(x0, y0, z0, r1, theta1, z1):
    x1 = r1 * cos(theta1)
    y1 = r1 * sin(theta1)
    v = (x1 - x0, y1 - y0, z1 - z0)
    return v[0] * v[0] + v[1] * v[1] + v[2] * v[2];

class CosmicRay(object):
    def __init__(self):
        self.theta = random.random() * pi * 2
        self.z = 14.5;
        self.velocity = -(2.8 + random.random() * 1.8)
        self.rotation = 1.2 * random.random() * (1 if random.random() > 0.5 else -1);
        self.size = 0.05 + 0.05 * random.random()
        self.lastUpdate = time.time()

    def tick(self):
        delta = time.time() - self.lastUpdate
        self.lastUpdate += delta

        self.z += self.velocity * delta;
        self.theta = (self.theta + self.rotation * delta) % (2 * pi)


rays = []

def updateRays(events, frame_time):

    while len(events):
        e = events.pop()
        rays.append(CosmicRay())

    for ray in rays:
        ray.tick()
        if ray.z < 0:
            rays.remove(ray)

def miami_color(t, pixel, random_values, accum):
    # hue-restricted, faster version of miami.py from OPC samples
    # make moving stripes for x, y, and z
    x, y, z, theta, r, xr, yr = pixel['coord']
    y += color_utils.scaled_cos(x - 0.2*z, offset=0, period=1, minn=0, maxx=0.6)
    z += color_utils.scaled_cos(x, offset=0, period=1, minn=0, maxx=0.3)
    x += color_utils.scaled_cos(y - z, offset=0, period=1.5, minn=0, maxx=0.2)

    # make x, y, z -> r, g, b sine waves
    r = color_utils.scaled_cos(y, offset=t / 16, period=2.5, minn=0, maxx=1)
    g = color_utils.scaled_cos(z, offset=t / 16, period=2.5, minn=0, maxx=1)
    b = color_utils.scaled_cos(-x, offset=t / 16, period=2.5, minn=0, maxx=1)
    r, g, b = color_utils.contrast((r, g, b), 0.5, 1.4)

    clampdown = (r + g + b)/2
    clampdown = color_utils.remap(clampdown, 0.4, 0.5, 0, 1)
    clampdown = color_utils.clamp(clampdown, 0, 1)
    clampdown *= 0.8
    r *= clampdown
    g *= clampdown
    b *= clampdown

    g = g * 0.1 + 0.8 * (b + 0.2 * r) / 2 

    return (r, g, b)

def demoEffect(tower, state):
    
    updateRays(state.events, state.time)

    for pixel in tower:
        x, y, z, theta, r, xr, yr = pixel['coord']
        light = 0

        for ray in rays:
            d = cartesianToCylinderDistanceSquared(xr, yr, z, 1.0, ray.theta, ray.z)
            if d < ray.size:
                light += (ray.size - d) / ray.size

        rgb = miami_color(state.time, pixel, None, None)

        color = (rgb[0] + light, rgb[1] + light, rgb[2] + light)
        tower.set_pixel_rgb(pixel, color)
    if colormath_support:
        for pixel in tower:
            hsl = scaledRGBTupleToHSL(tower.get_pixel_rgb(pixel))
            hsl.hsl_s = 0.7
            hsl.hsl_l = 0.3 + 0.4 * hsl.hsl_l
            hsl.hsl_h = 320 + 40 * hsl.hsl_h / 360;
            tower.set_pixel_rgb(pixel, HSLToScaledRGBTuple(hsl))
    else:
        for pixel in tower:
            tower.set_pixel(pixel, (state.time % 30) / 30, 1.0)


def alignTestEffect(tower, state, speed = 12):
    t = state.time

    angle = (t * pi/speed) % (2.0 * pi)
    arcwidth = pi/3.0
    for pixel in tower:
        theta = pixel['theta']

        delta = abs(theta - angle)

        if delta > pi:
            delta = 2.0 * pi - delta

        color = (0, 0, 127)

        #if False: 
        if colormath_support:
            if delta < arcwidth:
                p = delta / arcwidth
                c = HSLColor(360.0 * (1 - p), 1.0, 0.5)
                color = HSLToScaledRGBTuple(c)
            tower.set_pixel_rgb(pixel, color)
        else:
           c = 1.0
           if delta < arcwidth:
                c = delta / arcwidth
           tower.set_pixel(pixel, c, 1.0)

def verySimpleExampleEffect(tower, state):
    for pixel in tower:
        #print str(pixel['x']) + ',' + str(pixel['y']) + ',' + str(pixel['z'])
        print pixel['index']
        tower.set_pixel(pixel, 0, 1.0)


