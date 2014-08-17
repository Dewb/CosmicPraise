#!/usr/bin/python

import struct
import random
import cProfile
import pstats
import math
from math import cos, sin, pi

def TESToverhead(a):
    # This is just to check the call overhead
    return ''

def TESTmath(a):
    return math.cos(a)

def TESTdirect(a):
    return cos(a)

def main():
    for x in range(10000000):
        a=random.randint(0,255)
        TESToverhead(a)
        TESTmath(a)
        TESTdirect(a)

tmpfile = "/tmp/python.stats"
cProfile.run('main()', tmpfile)
p = pstats.Stats(tmpfile)
p.strip_dirs().sort_stats('time').print_stats()
