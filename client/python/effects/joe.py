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


def ringEffect(tower, state):

    updateRays(state.events, state.time)

    for pixel in tower:
        x, y, z, theta, r, xr, yr = pixel['coord']
        print pixel['coord']
        light = 0

        for ray in rays:
            d = cartesianToCylinderDistanceSquared(xr, yr, z, 1.0, ray.theta, ray.z)
            if d < ray.size:
                light += (ray.size - d) / ray.size
