from __future__ import division
from itertools import chain, islice, imap
import color_utils
import time
import random
from colormath.color_objects import *
from colormath.color_conversions import convert_color
from math import pi, sqrt, cos, sin, atan2, log
twopi = 2 * pi

__all__ = ["barberRingEffect"]


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

things = dict()

def barberRingEffect(tower, state):

    # STATIC EFFECT VARIABLES #
    rotating_freq = - 4 # SPEED (negative is upwards barber pole)
    twisting_ratio = 3 # HOW MUCH IT TWISTS
    color_minimize = .2 # WHAT IS THE MAX CHROMA VALUE THE EFFECT REACHES (scales the range)
    static_brightness = .1 # THE LUMA

    # COSMIC RAY RESPONSE VARIABLES #
    ring_thickness = 1 # in z
    ring_speed = 2 # downward (cannot just make this negative)
    ring_fade_exponent = 0.5 # 0 < x <= 1 . Lower number is quicker fade

    if 'spireZBoundary' not in things:
        things['spireZBoundary'] = (9999, -9999)
        for pixel in tower.spire:
            x, y, z, theta, r, xr, yr = pixel['coord']
            things['spireZBoundary'] = (min(things['spireZBoundary'][0], z), max(things['spireZBoundary'][1], z))

    if 'middleZBoundary' not in things:
        things['middleZBoundary'] = (9999, -9999)
        for pixel in tower.middle:
            x, y, z, theta, r, xr, yr = pixel['coord']
            things['middleZBoundary'] = (min(things['middleZBoundary'][0], z), max(things['middleZBoundary'][1], z))
    for pixel in tower:
        x, y, z, theta, r, xr, yr = pixel['coord']
        chroma = color_minimize * (((2 * theta + rotating_freq * state.time + twisting_ratio * z) % (2 * twopi) - twopi) / twopi)
        luma = static_brightness
        tower.set_pixel(pixel, chroma, luma)
    for t, p in state.events:
        event_time = time.time() - t
        if event_time + 1 < things['spireZBoundary'][1]:
            for pixel in tower: #chain(tower.spire, tower.roofline, tower.railing, tower.middle):
                x, y, z, theta, r, xr, yr = pixel['coord']
                position = - (z - things['spireZBoundary'][1]) # downwards. z - things['middleZBoundary'][0] would be upwards
                phase = position - ring_speed * event_time + ring_thickness
                if 0 < phase < ring_thickness:
                    chroma = abs((2 * phase / ring_thickness) - 1)
                    luma = chroma ** ring_fade_exponent # fade in and out
                    tower.set_pixel(pixel, chroma, luma)
