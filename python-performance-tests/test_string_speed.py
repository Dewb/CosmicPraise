#!/usr/bin/python

import struct
import random
import cProfile
import pstats

def zero(a,b,c):
    # This is just to check the call overhead
    return ''

def one(a,b,c):
    return '%c%c%c' % (a,b,c)

def two(a,b,c):
    return chr(a) + chr(b) + chr(c)

def three(a,b,c):
    return struct.pack("BBB", a,b,c)

def four(a,b,c):
    return struct.pack("B", a) + struct.pack('B',b) + struct.pack("B",c)

def main():
    for x in range(100000):
        a=random.randint(0,255)
        b=random.randint(0,255)
        c=random.randint(0,255)
        zero(a,b,c)
        one(a,b,c)
        two(a,b,c)
        three(a,b,c)
        four(a,b,c)

tmpfile = "/tmp/python.string.stats"
cProfile.run('main()', tmpfile)
p = pstats.Stats(tmpfile)
p.strip_dirs().sort_stats('time').print_stats()
