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

__all__ = ["demoEffect", "alignTestEffect", "simpleExampleEffect", "radialExampleEffect", "anotherSimpleExampleEffect", "wheelSpinEffect"]


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
    y += color_utils.scaled_cos(x - 0.2*z, offset=0, period=10, minn=0, maxx=0.6)
    z += color_utils.scaled_cos(x, offset=0, period=10, minn=0, maxx=0.3)
    x += color_utils.scaled_cos(y - z, offset=0, period=15, minn=0, maxx=0.2)

    # make x, y, z -> r, g, b sine waves
    r = color_utils.scaled_cos(y, offset=t / 8, period=12.5, minn=0, maxx=1)
    g = color_utils.scaled_cos(z, offset=t / 6, period=12.5, minn=0, maxx=1)
    b = color_utils.scaled_cos(-x, offset=t / 4, period=12.5, minn=0, maxx=1)
    r, g, b = color_utils.contrast((r, g, b), 0.5, 1.4)

    #clampdown = (r + g + b)/2
    #clampdown = color_utils.remap(clampdown, 0.4, 0.5, 0, 1)
    #clampdown = color_utils.clamp(clampdown, 0, 1)
    #clampdown *= 0.8
    #r *= clampdown
    #g *= clampdown
    #b *= clampdown

    g = g * 0.1 + 0.8 * (b + 0.2 * r) / 2 

    return (r, g, b)

def demoEffect(system, state):
    
    updateRays(state.events, state.time)

    for pixel in system:
        x, y, z, theta, r, xr, yr = pixel['coord']
        light = 0

        for ray in rays:
            d = cartesianToCylinderDistanceSquared(xr, yr, z, 1.0, ray.theta, ray.z)
            if d < ray.size:
                light += (ray.size - d) / ray.size

        rgb = miami_color(state.time, pixel, None, None)

        color = (rgb[0] + light, rgb[1] + light, rgb[2] + light)
        system.set_pixel_rgb(pixel, color)


def alignTestEffect(system, state, speed = 6):
    t = state.time

    angle = (t * pi/speed) % (2.0 * pi)
    arcwidth = pi/6.0
    for pixel in system:
        theta = pixel['theta']

        delta = abs(theta - angle)

        if delta > pi:
            delta = 2.0 * pi - delta

        v = random.random() * 0.55
        color = (v + 0.25 * random.random() + 0.1, v + 0.125 * random.random(), 0)

        #if False: 
        if colormath_support:
            if delta < arcwidth:
                p = delta / arcwidth
                c = HSLColor(70 - 60 * (1 - p), 1.0, 0.5)
                color = HSLToScaledRGBTuple(c)
            system.set_pixel_rgb(pixel, color)
        else:
           c = 1.0
           if delta < arcwidth:
                c = delta / arcwidth
           system.set_pixel(pixel, c, 1.0)

def simpleExampleEffect(system, state):
    # make the wheel blue
    for pixel in system.wheel:
        system.set_pixel_rgb(pixel, (0, 0, 1))
    # make the ceiling red
    for pixel in system.ceiling:
        system.set_pixel_rgb(pixel, (1, 0, 0))
    # fade the doors from blue to red
    height = 15.0
    for pixel in system.doors:
        s = pixel['z'] / height
        system.set_pixel_rgb(pixel, (s, 0, (1 - s)))
    # run a yellow line across the ceiling strips
    n = int(state.time % 5)
    for pixel in system.ceiling_strip(n):
        system.set_pixel_rgb(pixel, (1, 1, 0))

def anotherSimpleExampleEffect(system, state):
    for pixel in system:
        system.set_pixel(pixel, ((pixel['z'] * 2 + pixel['y'] + 3 * state.time) % 8) / 8, 0.75)

def radialExampleEffect(system, state):
    for pixel in system:
        system.set_pixel(pixel, 0.5, (pixel['r'] / 4.0 - state.time) % 1.0)

def scaleTuple(tpl, scalar):
    return [i * scalar for i in tpl]

def wheelSpinEffect(system, state):
    for pixel in system:
        x, y, z, theta, r, xr, yr = pixel['coord']
        pos = state.wheel_position
        
        intensity = color_utils.scaled_cos(theta, offset=pos / (2 * pi), period=pi / 4, minn=-1, maxx=1)
      
        #color1 = (0.1, 1.0, 0.3)
        #color2 = (0.1, 0.4, 0.9)
        #color = scaleTuple(color1, intensity) if intensity > 0 else scaleTuple(color2, abs(intensity))

        #system.set_pixel_rgb(pixel, color)

        colorA = color_utils.scaled_cos(state.time / 288, offset=0, minn=0, maxx=1)
        colorB = 1 - colorA
        color = colorA if intensity > 0 else colorB

        system.set_pixel(pixel, color, abs(intensity))