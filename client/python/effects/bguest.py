from __future__ import division
from itertools import chain
import color_utils
import time
import random
from colormath.color_objects import *
from colormath.color_conversions import convert_color
from math import pi, sqrt, cos, sin, atan2, log
twopi = 2 * pi

__all__ = ["linear_down_effect"]


def interpolate_color(val, color1, color2):
    color = []
    for i in range(3):
        color.append( color1[i] + (color2[i] - color1[i])*val )

    return tuple(color)

def wave_z(pixel, wave_width, height, bg_color, color):
    z = pixel['z']
    if 'quad' in pixel:
        z = pixel['quad'][0][2]
    value = 0
    if abs(z - height) < wave_width/2.0:
        value = 1.0/2 + 1.0/2 * cos(pi * (2.0*z/wave_width - height))

    return interpolate_color(value, bg_color, color)

def linear_down_effect(system, state):
    bg_color = (0, 0, 0)
    period = 3
    total_height = 30.0
    height = total_height - state.time % period * total_height/period
    for pixel in system:
        system.set_pixel_rgb(pixel, wave_z(pixel, 3.5, height, bg_color, (1.0, 1.0, 0)))

