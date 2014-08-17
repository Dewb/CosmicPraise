#!/usr/bin/python



import struct
import random
import cProfile
import pstats

from colorsys import rgb_to_hls

from colormath.color_objects import *
from colormath.color_conversions import convert_color


def TESTzero(a,b,c):
    # This is just to check the call overhead
    return ''

def TESTone(a,b,c):
    rgb = sRGBColor(a, b, c, True)
    return convert_color(rgb, HSLColor)

def TESTtwo(a,b,c):
    h,l,s = rgb_to_hls(a/255.0,b/255.0,c/255.0) 
    return h*255, s*255, l*255
    

def main():
    for x in range(10):
        a=random.randint(0,255)
        b=random.randint(0,255)
        c=random.randint(0,255)
        TESTzero(a,b,c)
        print TESTone(a,b,c)
        print TESTtwo(a,b,c)
        print ""

tmpfile = "/tmp/python.string.stats"
cProfile.run('main()', tmpfile)
p = pstats.Stats(tmpfile)
p.strip_dirs().sort_stats('time').print_stats()
