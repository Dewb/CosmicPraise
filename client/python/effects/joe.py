from __future__ import division
from itertools import chain, islice, imap
import color_utils
import time
import random
from colormath.color_objects import *
from colormath.color_conversions import convert_color
from math import pi, sqrt, cos, sin, atan2, log
twopi = 2 * pi

__all__ = ["ringEffect"]


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

def ringEffect(tower, state):

    # STATIC EFFECT VARIABLES #
    rotating_freq = - 4 # SPEED (negative is upwards barber pole)
    twisting_ratio = 3 # HOW MUCH IT TWISTS
    color_minimize = .2 # WHAT IS THE MAX CHROMA VALUE THE EFFECT REACHES (scales the range)
    static_brightness = .1 # THE LUMA

    # COSMIC RAY RESPONSE VARIABLES #
    ring_thickness = .4 # in z



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
        if event_time + 1 < things['middleZBoundary'][1]:
            for pixel in tower.middle:
                x, y, z, theta, r, xr, yr = pixel['coord']
                position_on_middle = z - things['middleZBoundary'][0]
                # print position_on_middle
                phase = position_on_middle - 2 * event_time
                if 0 < phase < ring_thickness:
                    chroma = abs((2 * phase / ring_thickness) - 1)
                    luma = chroma ** 0.5 # fade in and out
                    tower.set_pixel(pixel, chroma, luma)

        # for event in state.events:
        # print state.time

        light = 0
