#!/usr/bin/env python

# Cosmic Praise
# OpenPixelControl test program
# 7/18/2014

from __future__ import division
import time
import sys
import optparse
import random
import math
try:
    import json
except ImportError:
    import simplejson as json

from CosmicPraise import opc 
from CosmicPraise import color_utils

# remember to 
# $ sudo pip install colormath
from colormath.color_objects import *
from colormath.color_conversions import convert_color

# $ sudo pip install python-rtmidi --pre
import rtmidi
from rtmidi.midiutil import open_midiport
from rtmidi.midiconstants import *

#-------------------------------------------------------------------------------
# parse command line

parser = optparse.OptionParser()
parser.add_option('-l', '--layout', dest='layout',
                    action='store', type='string',
                    help='layout file')
parser.add_option('-s', '--server', dest='server', default='127.0.0.1:7890',
                    action='store', type='string',
                    help='ip and port of server')
parser.add_option('-f', '--fps', dest='fps', default=20,
                    action='store', type='int',
                    help='frames per second')

options, args = parser.parse_args()

if not options.layout:
    parser.print_help()
    print
    print 'ERROR: you must specify a layout file using --layout'
    print
    sys.exit(1)


#-------------------------------------------------------------------------------
# create MIDI event listener

events = []

class MidiInputHandler(object):
    def __init__(self, port):
        self.port = port
        self._wallclock = time.time()

    def __call__(self, event, data=None):
        event, deltatime = event
        self._wallclock += deltatime
        print "[%s] @%0.6f %r" % (self.port, self._wallclock, event)

        if event[0] < 0xF0:
            channel = (event[0] & 0xF) + 1
            status = event[0] & 0xF0
        else:
            status = event[0]
            channel = None

        data1 = data2 = None
        num_bytes = len(event)

        if num_bytes >= 2:
            data1 = event[1]
        if num_bytes >= 3:
            data2 = event[2]

        if status == 0x90: # note on
            events.append( (channel, data1, data2, time.time()) )

try:
    midiin, port_name = open_midiport("USB Uno MIDI Interface", use_virtual=True)
    print "Attaching MIDI input callback handler."
    midiin.set_callback(MidiInputHandler(port_name))
except (EOFError, KeyboardInterrupt):
    print "Error opening MIDI port"
    

#-------------------------------------------------------------------------------
# parse layout file

print
print '    parsing layout file'
print

coordinates = []
groups = {}

def recordCoordinate(p):
    x, y, z = p
    theta = math.atan2(y, x)
    r = math.sqrt(x * x + y * y)
    xr = math.cos(theta)
    yr = math.sin(theta)

    coordinates.append(tuple(p + [theta, r, xr, yr]))


for item in json.load(open(options.layout)):
    if 'point' in item:
        recordCoordinate(item['point'])
    if 'quad' in item:
        recordCoordinate(item['quad'][0])
    if 'group' in item:
        if not item['group'] in groups:
            groups[item['group']] = []
        groups[item['group']].append(len(coordinates)-1)


#-------------------------------------------------------------------------------
# connect to server

client = opc.Client(options.server)
if client.can_connect():
    print '    connected to %s' % options.server
else:
    # can't connect, but keep running in case the server appears later
    print '    WARNING: could not connect to %s' % options.server
print


#-------------------------------------------------------------------------------
# define color effects

def scaledRGBTupleToHSL(s):
    rgb = sRGBColor(s[0], s[1], s[2], True)
    return convert_color(rgb, HSLColor)
    
def HSLToScaledRGBTuple(hsl):
    return convert_color(hsl, sRGBColor).get_upscaled_value_tuple()

def distance2d(x1, y1, x2, y2):
    v = (x2 - x1, y2 - y1)
    return math.sqrt(v[0] * v[0] + v[1] * v[1])

def plasma(t, accum, x, y):
    phase = accum
    stretch = 0.8 + (math.sin(t/20) ** 3 + 1.0) * 200
    p1 = ((math.sin(phase * 1.000) + 0.0) * 2.0, (math.sin(phase * 1.310) + 0.0) * 2.0)
    p2 = ((math.sin(phase * 1.770) + 0.0) * 2.0, (math.sin(phase * 2.865) + 0.0) * 2.0)
    d1 = distance2d(p1[0], p1[1], x, y)
    d2 = distance2d(p2[0], p2[1], x, y)
    f = (math.sin(d1 * d2 * stretch) + 1.0) * 0.5
    return f * f

def test_color(t, coord, ii, n_pixels, random_values, accum, trigger):
    c = None
    if trigger:
        c = HSLColor(330, 0.1, 0.6 + random.random() * 0.4)
    else:
        x, y, z, = coord
        theta = math.atan2(y, x)
        dist = math.sqrt(x * x + y * y + z * z)
        p = plasma(t, accum, theta, z)
        c = HSLColor(360.0 * (t % 6)/6.0 + 4 * dist - 30 * p, 0.6 + p/2, 0.5)
    return HSLToScaledRGBTuple(c)

def cylinderDistanceSquared(r0, theta0, z0, r1, theta1, z1):
    x0 = r0 * math.cos(theta0)
    y0 = r0 * math.sin(theta0)
    x1 = r1 * math.cos(theta1)
    y1 = r1 * math.sin(theta1)
    v = (x1 - x0, y1 - y0, z1 - z0)
    return v[0] * v[0] + v[1] * v[1] + v[2] * v[2];

def cartesianToCylinderDistanceSquared(x0, y0, z0, r1, theta1, z1):
    x1 = r1 * math.cos(theta1)
    y1 = r1 * math.sin(theta1)
    v = (x1 - x0, y1 - y0, z1 - z0)
    return v[0] * v[0] + v[1] * v[1] + v[2] * v[2];

class CosmicRay(object):
    def __init__(self):
        self.theta = random.random() * math.pi * 2
        self.z = 14.5;
        self.velocity = -(2.8 + random.random() * 1.8)
        self.rotation = 1.2 * random.random() * (1 if random.random() > 0.5 else -1);
        self.size = 0.05 + 0.05 * random.random()
        self.lastUpdate = time.time()

    def tick(self):
        delta = time.time() - self.lastUpdate
        self.lastUpdate += delta

        self.z += self.velocity * delta;
        self.theta = (self.theta + self.rotation * delta) % (2 * math.pi)

rays = []

def updateRays(events, frame_time):

    #if random.random() < 1/8:
    #    events.append("foo")

    while len(events):
        e = events.pop()
        rays.append(CosmicRay())

    for ray in rays:
        ray.tick()
        if ray.z < 0:
            rays.remove(ray)

def rays_color(t, coord, ii, n_pixels, random_values, accum):
    x, y, z, theta, r, xr, yr = coord
    light = 0

    for ray in rays:
        d = cartesianToCylinderDistanceSquared(xr, yr, z, 1.0, ray.theta, ray.z)
        if d < ray.size:
            light += (ray.size - d) / ray.size
    
    rgb = miami_color(t, coord, ii, n_pixels, random_values, accum)
    return (rgb[0] + light * 255, rgb[1] + light * 255, rgb[2] + light * 255)

def miami_color(t, coord, ii, n_pixels, random_values, accum):
    # make moving stripes for x, y, and z
    x, y, z, theta, r, xr, yr = coord
    y += color_utils.cos(x - 0.2*z, offset=0, period=1, minn=0, maxx=0.6)
    z += color_utils.cos(x, offset=0, period=1, minn=0, maxx=0.3)
    x += color_utils.cos(y - z, offset=0, period=1.5, minn=0, maxx=0.2)

    # make x, y, z -> r, g, b sine waves
    r = color_utils.cos(y, offset=t / 16, period=2.5, minn=0, maxx=1)
    g = color_utils.cos(z, offset=t / 16, period=2.5, minn=0, maxx=1)
    b = color_utils.cos(-x, offset=t / 16, period=2.5, minn=0, maxx=1)
    r, g, b = color_utils.contrast((r, g, b), 0.5, 1.4)

    clampdown = (r + g + b)/2
    clampdown = color_utils.remap(clampdown, 0.4, 0.5, 0, 1)
    clampdown = color_utils.clamp(clampdown, 0, 1)
    clampdown *= 0.8
    r *= clampdown
    g *= clampdown
    b *= clampdown

    g = g * 0.1 + 0.8 * (b + 0.2 * r) / 2 

    return (r*256, g*256, b*256)

#-------------------------------------------------------------------------------
# send pixels

print '    sending pixels forever (control-c to exit)...'
print

def main():
    n_pixels = len(coordinates)
    random_values = [random.random() for ii in range(n_pixels)]
    start_time = time.time()
    accum = 0
    while True:
        try:
            frame_time = time.time()
            t = frame_time - start_time

            updateRays(events, frame_time)
            pixels = [rays_color(t*0.6, coord, ii, n_pixels, random_values, accum) for ii, coord in enumerate(coordinates)]

            for index in groups['railing']:
                hsl = scaledRGBTupleToHSL(pixels[index])
                hsl.hsl_s = 0.7
                hsl.hsl_l = 0.3 + 0.4 * hsl.hsl_l
                hsl.hsl_h = 320 + 40 * hsl.hsl_h / 360;
                pixels[index] = HSLToScaledRGBTuple(hsl)

            for index in groups['base']:
                hsl = scaledRGBTupleToHSL(pixels[index])
                hsl.hsl_s = 0.7
                hsl.hsl_l = 0.3 + 0.4 * hsl.hsl_l
                hsl.hsl_h = 280 + 60 * hsl.hsl_h / 360;
                pixels[index] = HSLToScaledRGBTuple(hsl)

            client.put_pixels(pixels, channel=0)
            time.sleep(1 / options.fps)

        except KeyboardInterrupt:
            return

import cProfile
cProfile.run("main()")
#main()
