#!/usr/bin/env python

# Cosmic Praise
# OpenPixelControl test program
# 7/18/2014

from __future__ import division
import time
import sys
import optparse
import random
from math import pi, sqrt, cos, sin, atan2

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
# import all effects in folder

effects = []

from os.path import dirname, join, isdir, abspath, basename
from glob import glob
import importlib
pwd = dirname(__file__)
effectsDir = pwd + '/effects'
sys.path.append(effectsDir)
for x in glob(join(effectsDir, '*.py')):
    pkgName = basename(x)[:-3]
    print pkgName
    effectDict = importlib.import_module(pkgName)
    for effectName in effectDict.__all__:
        effects.append(getattr(effectDict,effectName))
print effects
    # for (name, effect) in effectDict.iteritems():
        # print name

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

    return tuple(p + [theta, r, xr, yr])

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
    @property
    def items(self):
        return json_items

    def set_item_color(self, item, color):
        #verbosePrint('setting pixel %d on %s channel %d' % (idx, addr, channel))
        clients[item['address']].channelPixels[channels[item['address']]][item['index']] = color

    def get_item_color(self, item):
        return clients[item['address']].channelPixels[channels[item['address']]][item['index']]

class State:
    time = 0
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

    random_values = [] #[random.random() for ii in range(n_pixels)]
    start_time = time.time()
    frame_time = start_time
    last_frame_time = None
    accum = 0
    while True:
        try:
            state.time = frame_time - start_time
            effects[1](tower, state)

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
