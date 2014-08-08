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

import pprint
pp = pprint.PrettyPrinter(indent=4)

try:
    import json
except ImportError:
    import simplejson as json

import opc 
import color_utils

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
parser.add_option('-f', '--fps', dest='fps', default=20,
                    action='store', type='int',
                    help='frames per second')
parser.add_option('--sim', dest='simulator', action='store_true', 
                    help='target simulator instead of servers in layout')

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
except (IOError, EOFError, KeyboardInterrupt):
    print "Error opening MIDI port"
    

#-------------------------------------------------------------------------------
# parse layout file

print
print '    parsing layout file'
print

groups = {}
clients = {}
channels = {}

simulatorClient = None
if options.simulator:
    simulatorClient = opc.Client("127.0.0.1:7890", verbose=False, protocol="opc")

def recordCoordinate(p):
    x, y, z = p
    theta = math.atan2(y, x)
    if theta < 0:
        theta = 2 * math.pi + theta 
    r = math.sqrt(x * x + y * y)
    xr = math.cos(theta)
    yr = math.sin(theta)

    return tuple(p + [theta, r, xr, yr])

def set_item_color(self, color):
    addr = self['address']
    idx = self['index']
    channel = channels[addr]
    #print 'setting pixel %d on %s' % (idx, addr)
    clients[addr].channelPixels[channel][idx] = color

def get_item_color(self):
    addr = self['address']
    idx = self['index']
    channel = channels[addr]
    return clients[addr].channelPixels[channel][idx]

items = json.load(open(options.layout))

for item in items:
    if 'point' in item:
        item['coord'] = recordCoordinate(item['point'])
    if 'quad' in item:
        item['coord'] = recordCoordinate(item['quad'][0])
    if 'group' in item:
        if not item['group'] in groups:
            groups[item['group']] = []
        groups[item['group']].append(item)
    if 'address' in item:
        address = item['address']

        if options.simulator:
            # Redirect everything on this address to its own channel on localhost
            if not address in clients:
                clients[address] = simulatorClient
            if not address in channels:
                channels[address] = len(channels)
        else:        
            if not address in clients:
                client = opc.Client(address, verbose=False, protocol=item['protocol'])
                if client.can_connect():
                    print '    connected to %s' % address
                else:
                    # can't connect, but keep running in case the server appears later
                    print '    WARNING: could not connect to %s' % address
                print
                clients[address] = client
            if not address in channels:
                channels[address] = 0
    

pp.pprint(clients)
pp.pprint(channels)

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

def rays_color(t, item, random_values, accum):

    x, y, z, theta, r, xr, yr = item['coord']
    light = 0

    for ray in rays:
        d = cartesianToCylinderDistanceSquared(xr, yr, z, 1.0, ray.theta, ray.z)
        if d < ray.size:
            light += (ray.size - d) / ray.size
    
    rgb = miami_color(t, item, random_values, accum)
    return (rgb[0] + light * 255, rgb[1] + light * 255, rgb[2] + light * 255)

def miami_color(t, item, random_values, accum):
    coord = item['coord']
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


def radial_spin(t, item, random_values, accum):
    angle = (t * math.pi/16.0) % (2.0 * math.pi)
    arcwidth = math.pi/12.0
    theta = item['coord'][3]
    #print "theta: %f angle: %f" % (theta, angle)

    delta = abs(theta - angle)

    if delta > math.pi:
        delta = 2.0 * math.pi - delta

    if delta < arcwidth:
        p = delta / arcwidth
        c = HSLColor(360.0 * (1 - p), 1.0, 0.5)
        return HSLToScaledRGBTuple(c)
    else:
        return (0, 0, 127)


#-------------------------------------------------------------------------------
# send pixels

print '    sending pixels forever (control-c to exit)...'
print

def main():
    random_values = [] #[random.random() for ii in range(n_pixels)]
    start_time = time.time()
    accum = 0
    while True:
        try:
            frame_time = time.time()
            t = frame_time - start_time

            foo = 0

            updateRays(events, frame_time)
            for item in items:
                color = rays_color(t*0.6, item, random_values, accum)
                #color = (255, 0, 0)
                #color = (color_utils.cos(t, period=color_utils.cos(t, period=30) * 9 + 1) * 255, 0, 0)
                #color = HSLToScaledRGBTuple(HSLColor(color_utils.cos(t, period=60) * 360, 1.0, color_utils.cos(t, period=3) * 0.3 + 0.2))                
                #color = radial_spin(t, item, random_values, accum)

                # stripes
                #color = HSLToScaledRGBTuple(HSLColor((item['coord'][3] - (item['coord'][3] % math.pi/3))* 360/(math.pi*2), 1.0, 0.5))
                
                #strobe = color_utils.cos(t, period=1/60)
                #color = HSLToScaledRGBTuple(HSLColor(color_utils.cos(t, period=1.2) * 360, 1.0, 0.5))
                set_item_color(item, color)


            for item in groups['top-cw']:
                set_item_color(item, (255,0,255))
            for item in groups['top-ccw']:
                set_item_color(item, (0,255,255))

            
            for item in groups['floodlight']:
                set_item_color(item, (0,0,255))
            
            for item in groups['railing']:
                hsl = scaledRGBTupleToHSL(get_item_color(item))
                hsl.hsl_s = 0.7
                hsl.hsl_l = 0.3 + 0.4 * hsl.hsl_l
                hsl.hsl_h = 320 + 40 * hsl.hsl_h / 360;
                set_item_color(item, HSLToScaledRGBTuple(hsl))
                set_item_color(item, (0,255,0))

            for item in groups['base']:
                hsl = scaledRGBTupleToHSL(get_item_color(item))
                hsl.hsl_s = 0.7
                hsl.hsl_l = 0.3 + 0.4 * hsl.hsl_l
                hsl.hsl_h = 280 + 60 * hsl.hsl_h / 360;
                set_item_color(item, HSLToScaledRGBTuple(hsl))
                set_item_color(item, (255,0,0))
            

            for address in clients:
            #for address in ["10.0.0.21:6038", "10.0.0.32:7890", "10.0.0.41:6038", "10.0.0.51:6038"]:
                client = clients[address]
                #print 'sending %d pixels to %s:%d' % (len(client.pixels), client._ip, client._port)
                client.put_pixels(client.channelPixels[channels[address]], channel=channels[address])

            time.sleep(1 / options.fps)

        except KeyboardInterrupt:
            return

import cProfile
cProfile.run("main()")
#main()
