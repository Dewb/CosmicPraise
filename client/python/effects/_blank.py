'''
Blank effects file for Cosmic Praise

Make a copy of this file under your own name and go to town!

See the README on Github for more details. Also check _common.py for potentially useful utility functions.
'''

from __future__ import division
from itertools import chain, islice, imap
import color_utils
import time
import random
from _common import *
from colormath.color_objects import *
from colormath.color_conversions import convert_color
from math import pi, sqrt, cos, sin, atan2, log
twopi = 2 * pi

__all__ = []

'''
Define your effects as functions that take a tower and a state object, like so. 

def verySimpleExampleEffect(system, state):
    for pixel in system:
        tower.set_pixel(pixel, pixel['theta'] / twopi, state.time % 0.5)

and then edit the __all__ line above to list your effect functions, e.g.:

__all__ = ["verySimpleExampleEffect"]

'''