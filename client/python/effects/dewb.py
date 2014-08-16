from __future__ import division
from itertools import chain, islice, imap
import color_utils
import time
import random
from colormath.color_objects import *
from colormath.color_conversions import convert_color
from math import pi, sqrt, cos, sin, atan2, log
twopi = 2 * pi

__all__ = ["demoEffect", "alignTestEffect", "addressOrderTest", "verySimpleExampleEffect", "simpleExampleEffect", "lightningTest", "diamondTest"]


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

    for pixel in tower.railing:
        hsl = scaledRGBTupleToHSL(tower.get_pixel_rgb(pixel))
        hsl.hsl_s = 0.7
        hsl.hsl_l = 0.3 + 0.4 * hsl.hsl_l
        hsl.hsl_h = 320 + 40 * hsl.hsl_h / 360;
        tower.set_pixel_rgb(pixel, HSLToScaledRGBTuple(hsl))
        
    for pixel in tower.base:
        hsl = scaledRGBTupleToHSL(tower.get_pixel_rgb(pixel))
        hsl.hsl_s = 0.7
        hsl.hsl_l = 0.3 + 0.4 * hsl.hsl_l
        hsl.hsl_h = 280 + 60 * hsl.hsl_h / 360;
        tower.set_pixel_rgb(pixel, HSLToScaledRGBTuple(hsl))
        

def alignTestEffect(tower, state):
    t = state.time

    angle = (t * pi/12.0) % (2.0 * pi)
    arcwidth = pi/12.0
    for pixel in tower:
        theta = pixel['theta']

        delta = abs(theta - angle)

        if delta > pi:
            delta = 2.0 * pi - delta

        color = (0, 0, 127)

        if delta < arcwidth:
            p = delta / arcwidth
            c = HSLColor(360.0 * (1 - p), 1.0, 0.5)
            color = HSLToScaledRGBTuple(c)
    
        tower.set_pixel_rgb(pixel, color)

def addressOrderTest(tower, state):

    # test all the complete tower diagonal generators
    count = len(list(tower.diagonals_index(1)))
    t = state.time 
    diagonal_t = state.time * 3
    direction = int((t % 96) / 24)
    generatorFn = None

    if direction == 0:
        generatorFn = lambda x: tower.counter_clockwise_index(x) if x < 12 else tower.clockwise_index(x-12)
    elif direction == 1:
        generatorFn = lambda x: tower.counter_clockwise_index_bottom(x) if x < 12 else tower.clockwise_index_bottom(x-12)
    elif direction == 2:
        generatorFn = tower.diagonals_index
    elif direction == 3:
        generatorFn = tower.diagonals_index_bottom

    n = int(diagonal_t % 24)
    for x in range(n + 1):
        if x == n:
            for ii, pixel in enumerate(generatorFn(x)):
                if ii / count < diagonal_t % 1:
                    tower.set_pixel_rgb(pixel, (1.0, 0, 0))
        elif x < n:
            for pixel in generatorFn(x):
                tower.set_pixel_rgb(pixel, (0, 0, 1.0))

    # test railing and base
    for ii, (rail_pixel, base_pixel) in enumerate(zip(tower.railing, tower.base)):
        b = 0.4 if t % 2 < 1 else 0
        if ii / 24 < t % 1:
            tower.set_pixel_rgb(rail_pixel, (0.0, 0, b))
            tower.set_pixel_rgb(base_pixel, (0.0, 0, b))
        else:
            tower.set_pixel_rgb(rail_pixel, (0.0, 0, 0.4 - b))
            tower.set_pixel_rgb(base_pixel, (0.0, 0, 0.4 - b))

    # test roofline
    count = len(list(tower.roofline))
    for ii, pixel in enumerate(tower.roofline):
        if ii / count < t % 1:
            tower.set_pixel_rgb(pixel, (1.0, 0, 0))

    # test spire
    n = int(t % 16)
    for x in range(16):
        if x == n:
            for ii, pixel in enumerate(tower.spire_ring(x)):
                if ii/30 < t % 1:
                    tower.set_pixel_rgb(pixel, (1.0, 0, 0))
        elif x < n:
            for pixel in tower.spire_ring(x):
                tower.set_pixel_rgb(pixel, (0, 0, 1.0))

    # test spotlight
    for pixel in tower.spotlight:
        tower.set_pixel_rgb(pixel, (1, 1, 1) if state.time % 0.155 < .03 else (0, 0, 0))


def verySimpleExampleEffect(tower, state):
    for pixel in tower:
        tower.set_pixel(pixel, pixel['theta'] / twopi, state.time % 0.5)

def simpleExampleEffect(tower, state):
    # make the base blue
    for pixel in tower.base:
        tower.set_pixel_rgb(pixel, (0, 0, 1))
    # make the railing red
    for pixel in tower.railing:
        tower.set_pixel_rgb(pixel, (1, 0, 0))
    # fade the tower middle from blue to red
    tower_height = 15.0
    for pixel in tower.middle:
        s = pixel['z'] / tower_height
        tower.set_pixel_rgb(pixel, (s, 0, (1 - s)))
    # and spin a yellow line clockwise around the clockwise tower diagonals
    n = int(state.time % 12)
    for pixel in tower.clockwise_index(n):
        tower.set_pixel_rgb(pixel, (1, 1, 0))
    # make the roofline, and spire flash green
    for pixel in chain(tower.roofline, tower.spire):
        tower.set_pixel_rgb(pixel, (0, state.time % 1, 0))


def lightningTest(tower, state):
    speed = 5

    if state.time % 1/speed < 0.01:
        state.accumulator = int(random.random() * 24)

    start = state.accumulator
    if state.time % 0.125 > 0.05:
        for pixel in tower.lightning(start, state.random_values[(int(state.time * speed)) % 10000]):
            tower.set_pixel_rgb(pixel, (1, 1, 1))
        for pixel in tower.lightning(start, state.random_values[(int(state.time * speed) + 1) % 10000]):
            tower.set_pixel_rgb(pixel, (1, 1, 1))
        for pixel in tower.lightning(start, state.random_values[(int(state.time * speed)+ 2) % 10000]):
            tower.set_pixel_rgb(pixel, (1, 1, 1))
    
def diamondTest(tower, state):
    '''
    for k in range(24):
        for bit, pixel in enumerate(islice(tower.diagonals_index(k), 5, 12)):
            tower.set_pixel_rgb(pixel, (255, 0, 0) if k & 1<<bit else (0, 0, 60))
    '''
    for pixel in tower.diamonds_even:
        tower.set_pixel_rgb(pixel, (0, 0, 0.5))
    for pixel in tower.diamonds_even_shifted:
        tower.set_pixel_rgb(pixel, (0, 0.25, 0.25))

    for pixel in tower.diamond(int((state.time * 4) % 12), 1):
        tower.set_pixel_rgb(pixel, (1, 1, 0))
    for pixel in tower.diamond(int((state.time * 4) % 12), 3):
        tower.set_pixel_rgb(pixel, (0, 1, 1))

