from __future__ import division
from itertools import chain, islice, imap
import time
import random
from math import pi, sqrt, cos, sin, atan2, log
twopi = 2 * pi

__all__ = ["barberRingEffect"]

things = dict()

def barberRingEffect(tower, state, rotating_freq = 0.625, twisting_ratio = 0.1, color_minimize = 0.3, static_brightness = 0.3,
    ring_thickness = 0.1, ring_speed = 0.2, ring_fade_exponent = 0.5):

    # STATIC EFFECT VARIABLES #
    rotating_freq = (rotating_freq - 0.5) * -32 # SPEED (negative is upwards barber pole)
    twisting_ratio *= 20 # HOW MUCH IT TWISTS
    color_minimize = color_minimize # WHAT IS THE MAX CHROMA VALUE THE EFFECT REACHES (scales the range)
    static_brightness = static_brightness # THE LUMA

    # COSMIC RAY RESPONSE VARIABLES #
    ring_thickness *= 10 # in z
    ring_speed *= 10 # downward (cannot just make this negative)
    ring_fade_exponent = min(ring_fade_exponent + .00001, 1.0) # 0 < x <= 1 . Lower number is quicker fade

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
        #if event_time + 1 < things['spireZBoundary'][1]:
        if True:
            for pixel in tower: #chain(tower.spire, tower.roofline, tower.railing, tower.middle):
                x, y, z, theta, r, xr, yr = pixel['coord']
                position = - (z - things['spireZBoundary'][1]) # downwards. z - things['middleZBoundary'][0] would be upwards
                phase = position - ring_speed * event_time + ring_thickness
                if 0 < phase < ring_thickness:
                    chroma = abs((2 * phase / ring_thickness) - 1)
                    luma = (1 - chroma) ** ring_fade_exponent # fade in and out
                    tower.set_pixel(pixel, chroma, luma)
