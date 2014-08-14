#!/usr/bin/env python

# Cosmic Praise
# OpenPixelControl test program
# 7/18/2014

from __future__ import division
import time
import sys
import optparse
import random
import select

from math import pi, sqrt, cos, sin, atan2

from itertools import chain

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
#from colormath.color_objects import *
#from colormath.color_conversions import convert_color

# $ sudo pip install python-rtmidi --pre
import rtmidi
from rtmidi.midiutil import open_midiport
from rtmidi.midiconstants import *

#-------------------------------------------------------------------------------
# import all effects in folder

effects = {}

from os.path import dirname, join, isdir, abspath, basename
from glob import glob
import importlib
pwd = dirname(__file__)
effectsDir = pwd + '/effects'
sys.path.append(effectsDir)
for x in glob(join(effectsDir, '*.py')):
    pkgName = basename(x)[:-3]
    effectDict = importlib.import_module(pkgName)
    for effectName in effectDict.__all__:
        effects[pkgName + "-" + effectName] = getattr(effectDict,effectName)

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
parser.add_option('--profile', dest='profile', action='store_true',
                    help='run inside a profiler or not. (default not)')
parser.add_option('-v', '--verbose', dest='verbose', action='store_true',
                    help='print extra information for debugging')

options, args = parser.parse_args()

if not options.layout:
    parser.print_help()
    print
    print 'ERROR: you must specify a layout file using --layout'
    print
    sys.exit(1)

targetFrameTime = 1/options.fps

def verbosePrint(str):
    if options.verbose:
        print str

#-------------------------------------------------------------------------------
# create MIDI event listener to receive cosmic ray information from the spark chamber HV electronics

cosmic_ray_events = []

class MidiInputHandler(object):
    def __init__(self, port):
        self.port = port
        self._wallclock = time.time()
        self.powerlevel = 0

    def __call__(self, event, data=None):
        event, deltatime = event
        self._wallclock += deltatime
        verbosePrint("[%s] @%0.6f %r" % (self.port, self._wallclock, event))

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
            cosmic_ray_events.append( (time.time(), self.powerlevel) )
        # todo: if status is a particular CC, update powerlevel

try:
    midiin, port_name = open_midiport("USB Uno MIDI Interface", use_virtual=True)
    print "Attaching MIDI input callback handler."
    midiin.set_callback(MidiInputHandler(port_name))
except (IOError, EOFError, KeyboardInterrupt):
    print "WARNING: No MIDI input ports detected."


#-------------------------------------------------------------------------------
# parse layout file

print
print '    parsing layout file'
print

groups = {}
group_strips = {}
clients = {}
channels = {}

simulatorClient = None
if options.simulator:
    simulatorClient = opc.Client("127.0.0.1:7890", verbose=False, protocol="opc")

def recordCoordinate(p):
    x, y, z = p
    theta = atan2(y, x)
    if theta < 0:
        theta = 2 * pi + theta
    r = sqrt(x * x + y * y)
    xr = cos(theta)
    yr = sin(theta)

    return tuple([x, y, z, theta, r, xr, yr])

json_items = json.load(open(options.layout))

for item in json_items:
    if 'point' in item:
        item['coord'] = recordCoordinate(item['point'])

    if 'quad' in item:
        item['coord'] = recordCoordinate(item['quad'][0])

    if 'group' in item:
        if not item['group'] in groups:
            groups[item['group']] = []
        groups[item['group']].append(item)
        if 'strip' in item:
            if not item['group'] in group_strips:
                group_strips[item['group']] = {}
            if not item['strip'] in group_strips[item['group']]:
                group_strips[item['group']][item['strip']] = []
            group_strips[item['group']][item['strip']].append(item)

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
# define client API objects

class Tower:

    def __iter__(self):
        for item in json_items:
            yield item

    @property
    def all(self):
        for item in json_items:
            yield item

    @property
    def middle(self):
        for item in chain(groups["middle-cw"], groups["middle-ccw"], groups["top-cw"], groups["top-ccw"]):
            yield item

    @property
    def roofline(self):
        for item in chain(groups["roofline-odd"], groups["roofline-even"]):
            yield item

    @property
    def spire(self):
        for item in groups["spire"]:
            yield item

    @property
    def railing(self):
        for item in groups["railing"]:
            yield item

    @property
    def base(self):
        for item in groups["base"]:
            yield item

    def group(self, name):
        for item in groups[name]:
            yield item

    @property
    def clockwise(self):
        for item in chain(groups["middle-cw"], groups["top-cw"]):
            yield item

    @property
    def counter_clockwise(self):
        for item in chain(groups["middle-ccw"], groups["top-ccw"]):
            yield item

    # Each of the 12 clockwise tower diagonals, continuously across both sections, from the top down
    def clockwise_index(self, index):
        bottomindex = index * 2
        topindex = (index * 2 + 10) % 24
        for item in chain(group_strips["top-cw"][topindex], reversed(group_strips["middle-cw"][bottomindex])):
            yield item

    # Each of the 12 counter-clockwise tower diagonals, continuously across both sections, from the top down
    def counter_clockwise_index(self, index):
        bottomindex = index * 2 + 1
        topindex = index * 2 + 1
    
        for item in chain(group_strips["top-ccw"][topindex], reversed(group_strips["middle-ccw"][bottomindex])):
            yield item 

    # Each of the 24 tower diagonals, continuously across both sections, from the top down
    def diagonals_index(self, index):
        if index < 12:
            return self.clockwise_index(index)
        else:
            return self.counter_clockwise_index(index-12)

    def set_item_color(self, item, color):
        #verbosePrint('setting pixel %d on %s channel %d' % (idx, addr, channel))
        clients[item['address']].channelPixels[channels[item['address']]][item['index']] = color

    def get_item_color(self, item):
        return clients[item['address']].channelPixels[channels[item['address']]][item['index']]

class State:
    time = 0
    random_values = [random.random() for ii in range(10000)]
    accumulator = 0

    @property
    def events(self):
        return cosmic_ray_events


#-------------------------------------------------------------------------------
# Main loop

print '    sending pixels forever (control-c to exit)...'
print

def main():
    state = State()
    tower = Tower()

    start_time = time.time()
    frame_time = start_time
    last_frame_time = None
    accum = 0
    effectsIndex = 0

    print "Running effect " + sorted(effects)[effectsIndex]

    while True:
        try:
            state.time = frame_time - start_time
            effects[sorted(effects)[effectsIndex]](tower, state)

            # press enter to cycle through effects
            i,o,e = select.select([sys.stdin],[],[], 0.0)
            for s in i:
                if s == sys.stdin:
                    input = sys.stdin.readline()
                    effectsIndex += 1
                    effectsIndex = effectsIndex % len(effects)
                    print "Running effect " + sorted(effects)[effectsIndex]

            for address in clients:
                client = clients[address]
                verbosePrint('sending %d pixels to %s:%d on channel %d' % (len(client.channelPixels[channels[address]]), client._ip, client._port, channels[address]))

                client.put_pixels(client.channelPixels[channels[address]], channel=channels[address])


            last_frame_time = frame_time
            frame_time = time.time()
            frameDelta = frame_time - last_frame_time
            verbosePrint('frame completed in %.2fms (max %.1f fps)' % (frameDelta * 1000, 1/frameDelta))

            if (targetFrameTime > frameDelta):
                time.sleep(targetFrameTime - frameDelta)

        except KeyboardInterrupt:
            return

if options.profile:
    import cProfile
    import pstats

    # OMG this is stupid. How can this not be in a fucking library.
    combined_f = "stats/blah_run_combined.stats"
    cProfile.run('print 0, main()', combined_f)
    #combined_stats = pstats.Stats(combined_f)
    #for i in range(2):
    #    filename = 'stats/blah_run_%d.stats' % i
    #    cProfile.run('print %d, main()' % i, filename)
    #    combined_stats.add(filename)
else:
    main()
