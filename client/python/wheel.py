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
import socket

from math import pi, sqrt, cos, sin, atan2

from itertools import chain, islice, imap, starmap, product

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
colormath_support = True
try:
    from colormath.color_objects import *
    from colormath.color_conversions import convert_color
except ImportError:
    print "WARNING: colormath not found"
    colormath_support = False

midi_support = True
try:
    # $ sudo pip install python-rtmidi --pre
    import rtmidi
    from rtmidi.midiutil import open_midiport
    from rtmidi.midiconstants import *
except ImportError:
    print "WARNING: python-rtmidi not found, MIDI event input will not be available."
    midi_support = False

osc_support = True
try:
    from OSC import ThreadingOSCServer
    from threading import Thread
except ImportError:
    print "WARNING: pyOSC not found, remote OSC control will not be available."
    osc_support = False

#-------------------------------------------------------------------------------
# import all effects in folder

effects = {}

from os.path import dirname, join, isdir, abspath, basename
from glob import glob
import importlib
import inspect

pwd = dirname(__file__)
effectsDir = pwd + '/effects'
sys.path.append(effectsDir)
for x in glob(join(effectsDir, '*.py')):
    pkgName = basename(x)[:-3]
    if not pkgName.startswith("_"):
        try:
            effectDict = importlib.import_module(pkgName)
            for effectName in effectDict.__all__:
                effectFunc = getattr(effectDict, effectName)
                args, varargs, keywords, defaults = inspect.getargspec(effectFunc)
                params = {} if defaults == None or args == None else dict(zip(reversed(args), reversed(defaults)))
                effects[pkgName + "-" + effectName] = { 
                    'action': effectFunc, 
                    'opacity': 0.0,
                    'params': params
                }
        except ImportError:
	    print "WARNING: could not load effect %s" % pkgName

# import all palettes
sys.path.append(pwd + '/palettes')
from palettes import palettes

# expand palettes
for p in palettes:
   p = reduce(lambda a, b: a + b, map(lambda c: [c] * 16, p))

# set startup effect and palette
globalParams = {}
globalParams["palette"] = 2
globalParams["wheelSpeed"] = 0.8
globalParams["effectIndex"] = 0
effects["dewb-wheelSpinEffect"]["opacity"] = 1.0


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
parser.add_option('-i', '--interactive', dest='interactive', action='store_true',
                    help='enable interactive control of effects at console')

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

def nextEffect():
    globalParams["effectIndex"] += 1
    effectsIndex = globalParams["effectIndex"]
    effectsIndex = effectsIndex % len(effects)
    print "Running effect " + sorted(effects)[effectsIndex]
    for effectName in effects:
        effects[effectName]["opacity"] = 0
    effects[sorted(effects)[effectsIndex]]["opacity"] = 1.0


note_events = []


#-------------------------------------------------------------------------------
# create MIDI event listener to receive cosmic ray information from the spark chamber HV electronics

# if midi_support:

#     class MidiInputHandler(object):
#         def __init__(self, port):
#             self.port = port
#             self._wallclock = time.time()
#             self.powerlevel = 0

#         def __call__(self, event, data=None):
#             event, deltatime = event
#             self._wallclock += deltatime
#             verbosePrint("[%s] @%0.6f %r" % (self.port, self._wallclock, event))

#             if event[0] < 0xF0:
#                 channel = (event[0] & 0xF) + 1
#                 status = event[0] & 0xF0
#             else:
#                 status = event[0]
#                 channel = None

#             data1 = data2 = None
#             num_bytes = len(event)

#             if num_bytes >= 2:
#                 data1 = event[1]
#             if num_bytes >= 3:
#                 data2 = event[2]

#             if status == 0x90: # note on
#                 cosmic_ray_events.append( (time.time(), self.powerlevel) )
#             # todo: if status is a particular CC, update powerlevel

#     try:
#         midiin, port_name = open_midiport("USB Uno MIDI Interface", use_virtual=True)
#         print "Attaching MIDI input callback handler."
#         midiin.set_callback(MidiInputHandler(port_name))
#     except (IOError, EOFError, KeyboardInterrupt):
#         print "WARNING: No MIDI input ports detected."


#-------------------------------------------------------------------------------
# Create OSC listener for timeline/effects control

if osc_support:
    def default_handler(path, tags, args, source):
        return

    def next_effect_handler(path, tags, args, source):
        nextEffect()

    def effect_opacity_handler(path, tags, args, source):
        addr = path.split("/")
        effectName = addr[2]
        value = args[0]
        if effectName in effects:
            effects[effectName]['opacity'] = value

    def effect_param_handler(path, tags, args, source):
        addr = path.split("/")
        effectName = addr[2]
        paramName = addr[4]
        value = args[0]
        if effectName in effects:
            if paramName in effects[effectName]['params']:
                effects[effectName]['params'][paramName] = value

    def wheel_speed_handler(path, tags, args, source):
        globalParams["wheelSpeed"] = args[0]

    def note_trigger_handler(path, tags, args, source):
        note_events.append((time.time(), args[0]))

    def palette_select_handler(path, tags, args, source):
        paletteIndex = int(args[0] * (len(palettes) - 1))
	globalParams["palette"] = paletteIndex 

    server = ThreadingOSCServer( ("0.0.0.0", 7000) )
    
    for effectName in effects:
        server.addMsgHandler("/effect/%s/opacity" % effectName, effect_opacity_handler)
        for paramName in effects[effectName]['params']:
            server.addMsgHandler("/effect/%s/param/%s" % (effectName, paramName), effect_param_handler)

    server.addMsgHandler("default", default_handler)
    server.addMsgHandler("/wheel/speed", wheel_speed_handler)
    server.addMsgHandler("/note/trigger", note_trigger_handler)
    server.addMsgHandler("/palette/select", palette_select_handler)
    server.addMsgHandler("/nextEffect", next_effect_handler)
    thread = Thread(target=server.serve_forever)
    thread.setDaemon(True)
    thread.start()
    print "Listening for OSC messages on port 7000"

#-------------------------------------------------------------------------------
# parse layout file

groups = {}
group_strips = {}
clients = {}
channels = {}

simulatorClient = None
if options.simulator:
    simulatorClient = opc.Client("127.0.0.1:7890", verbose=False, protocol="opc")

def recordCoordinate(item, p):
    x, y, z = p

    # precalculate angle from wheel center (0, -20, 13.9)
    dy = y + 20
    dz = z - 14.75
    theta = atan2(dy, dz)
    if theta < 0:
        theta = 2 * pi + theta
    
    r = sqrt(dy * dy + dz * dz)
    zr = cos(theta)
    yr = sin(theta)

    item['x'] = x
    item['y'] = y
    item['z'] = z
    item['theta'] = theta
    item['r'] = r

    # for backwards compatibility, remove in future?
    item['coord'] = (x, y, z, theta, r, zr, yr)

json_items = json.load(open(options.layout))

for item in json_items:
    if 'point' in item:
        recordCoordinate(item, item['point'])

    if 'quad' in item:
        center = map(lambda i: i/4, reduce(lambda x, y: map(lambda a, b: a + b, x, y), item['quad']))
        recordCoordinate(item, center)

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

for index, client in enumerate(clients):
    proto = clients[client].protocol
    address = clients[client].address
    channel = channels[client]
    print "- Client %d at %s protocol %s on channel %d" %(index, address, proto, channel)

#-------------------------------------------------------------------------------
# define client API objects

class OPCSystem:

    def __init__(self):
        self.currentEffectOpacity = 1.0

    def __iter__(self):
        for item in json_items:
            yield item

    @property
    def all(self):
        for item in json_items:
            yield item

    @property
    def wheel(self):
        for item in chain(groups["wheel-left"], groups["wheel-right"]):
            yield item

    @property
    def wheel_left(self):
        for item in groups["wheel-left"]:
            yield item

    @property
    def wheel_right(self):
        for item in groups["wheel-right"]:
            yield item

    @property
    def back_door_right(self):
        for item in groups["back-door-right"]:
            yield item

    @property
    def back_door_left(self):
        for item in groups["back-door-left"]:
            yield item

    @property
    def back_door(self):
        for item in chain(self.back_door_right, self.back_door_left):
            yield item

    @property
    def front_door(self):
        for item in groups["front-door"]:
            yield item

    @property
    def doors(self):
        for item in chain(self.back_door, self.front_door):
            yield item

    @property
    def ceiling(self):
        for item in chain(groups["ceiling-right-low"], groups["ceiling-right-high"], groups["ceiling-center"], groups["ceiling-left-high"], groups["ceiling-left-low"]):
            yield item

    def ceiling_strip(self, index):
        ceilingStrips = [groups["ceiling-right-low"], groups["ceiling-right-high"], groups["ceiling-center"], groups["ceiling-left-high"], groups["ceiling-left-low"]]
        for item in ceilingStrips[index]:
            yield item

    @property
    def not_wheel(self):
        for item in chain(self.doors, self.ceiling):
            yield item

    def set_pixel_rgb(self, item, color):
        #verbosePrint('setting pixel %d on %s channel %d' % (idx, addr, channel))
        current = (255 * color[0], 255 * color[1], 255 * color[2])
        previous = self.get_pixel_rgb_upscaled(item)
        c = self.blend_color(current, 1.0, previous)
        clients[item['address']].channelPixels[channels[item['address']]][item['index']] = c

    def get_pixel_rgb(self, item):
        color = clients[item['address']].channelPixels[channels[item['address']]][item['index']]
        return (color[0]/255, color[1]/255, color[2]/255)

    def get_pixel_rgb_upscaled(self, item):
        color = clients[item['address']].channelPixels[channels[item['address']]][item['index']]
        return (color[0], color[1], color[2])

    def blend_color(self, src, srcluma, dest):
        s = self.currentEffectOpacity * srcluma
        return map(lambda c1, c2: c1 * s + c2 * (1 - s), src, dest)

    def set_pixel(self, item, chroma, luma = 0.5):
        #current = convert_color(HSLColor(chroma * 360, 1.0, luma), sRGBColor).get_upscaled_value_tuple()
        #current = palettes[currentPaletteIndex][int(chroma * 255)]

        palette = palettes[globalParams["palette"]]
        pfloat = chroma * (len(palette) - 2)
        pindex = int(pfloat)
        ps = pfloat - pindex
        current = map(lambda a, b: a * (1 - ps) + b * ps, palette[pindex], palette[pindex+1])
        current = map(lambda p: p * luma, current)
        previous = self.get_pixel_rgb_upscaled(item)
        c = self.blend_color(current, luma, previous)
        clients[item['address']].channelPixels[channels[item['address']]][item['index']] = c


class State:
    time = 0
    absolute_time = 0
    random_values = [random.random() for ii in range(10000)]
    accumulator = 0
    frame = 0
    wheel_speed = 0
    wheel_position = 0

    @property
    def events(self):
        return note_events


#-------------------------------------------------------------------------------
# Main loop


def main():

    print
    print '*** sending pixels forever (control-c to exit)...'
    print

    if options.interactive:
        print 'Press ENTER to cycle effects'

    state = State()
    system = OPCSystem()

    start_time = time.time()
    frame_time = start_time
    last_frame_time = None
    accum = 0

    for effectName in effects:
        if effects[effectName]["opacity"] > 0:
            print "Running effect " + effectName 

    while True:
        try:
            new_time = frame_time - start_time
            time_delta = new_time - state.time
            state.time = new_time
            state.absolute_time = frame_time

            state.wheel_speed = globalParams["wheelSpeed"]

            # revise this once wheel speed units are known
            state.wheel_position = (state.wheel_position + state.wheel_speed * time_delta) % (2 * pi)
              
            if len(state.events) > 0 and state.events[0][0] < frame_time - 30:
                state.events.remove(state.events[0])

            system.currentEffectOpacity = 1.0
            for pixel in system:
                system.set_pixel_rgb(pixel, (0, 0, 0))

            for effectName in effects:
                if effects[effectName]["opacity"] > 0:
                    system.currentEffectOpacity = effects[effectName]['opacity']
                    params = effects[effectName]['params']
                    effects[effectName]['action'](system, state, **params)

            system.currentEffectOpacity = 1.0

            # press enter to cycle through effects
            if options.interactive:
                i,o,e = select.select([sys.stdin],[],[], 0.0)
                for s in i:
                    if s == sys.stdin:
                        input = sys.stdin.readline()
                        nextEffect()

            for address in clients:
                client = clients[address]
                verbosePrint('sending %d pixels to %s:%d on channel %d' % (len(client.channelPixels[channels[address]]), client._ip, client._port, channels[address]))

                client.put_pixels(client.channelPixels[channels[address]], channel=channels[address])


            last_frame_time = frame_time
            frame_time = time.time()
            frameDelta = frame_time - last_frame_time
            verbosePrint('frame completed in %.2fms (max %.1f fps)' % (frameDelta * 1000, 1/frameDelta))
            state.frame = state.frame + 1

            if (targetFrameTime > frameDelta):
                time.sleep(targetFrameTime - frameDelta)

        except KeyboardInterrupt:
            return

if options.profile:
    import cProfile
    import pstats

    combined_f = "client/python/performance/stats/blah_run_combined.stats"
    cProfile.run('print 0, main()', combined_f)
    combined_stats = pstats.Stats(combined_f)
    combined_stats.print_stats()
else:
    main()
