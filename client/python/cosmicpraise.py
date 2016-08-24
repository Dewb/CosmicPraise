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
globalParams["spotlightBrightness"] = 0
effects["dewb-demoEffect"]["opacity"] = 1.0


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
parser.add_option('--osc', dest='osc_address', action='store', type='string',
                    help='OSC Destination of the form ip_address:port.  Default is 127.0.0.1:7000')

options, args = parser.parse_args()

if not options.layout:
    parser.print_help()
    print
    print 'ERROR: you must specify a layout file using --layout'
    print
    sys.exit(1)

#parsing osc address
#default values
osc_ip_address = '127.0.0.1'
osc_port_no = 7000;

if(options.osc_address):
    try:
        socket.inet_aton(options.osc_address.split(':')[0])
        #if the first chunk is a valid ip, parse it:
        if len(options.osc_address.split(':')) == 1:
            #no port number
            osc_ip_address = options.osc_address.split(':')[0]
        elif len(options.osc_address.split(':')) == 2:
            #ip and port number
            osc_ip_address = options.osc_address.split(':')[0]
            osc_port_no = int(options.osc_address.split(':')[1])
    except socket.error:
        print "ERROR: --osc not given a valid IP address"
        sys.exit()

targetFrameTime = 1/options.fps

def verbosePrint(str):
    if options.verbose:
        print str


globalParams["motorSpeed"] = 0

def updateSpotlightSpeed():
    #print "motor update %d" % globalParams["motorSpeed"] 
    motorControllerSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    motorControllerSocket.connect(("10.0.0.71", 6565))
    motorControllerSocket.send("s %d" % globalParams["motorSpeed"])


#-------------------------------------------------------------------------------
# create MIDI event listener to receive cosmic ray information from the spark chamber HV electronics

cosmic_ray_events = []

if midi_support:

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
# Create OSC listener for timeline/effects control

if osc_support:
    def default_handler(path, tags, args, source):
        return

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

    def motor_handler(path, tags, args, source):
        speed = args[0]
        adjustedSpeed = 0
        if speed > 1.0:
            speed = 1.0
        if speed < 0.0:
            speed = 0.0
        if speed > 0.6 or speed < 0.4:
            adjustedSpeed = speed * 200 - 100 
        #print "setting motor speed to %d" %  adjustedSpeed
        globalParams["motorSpeed"] = adjustedSpeed

    def spotlight_brightness_handler(path, tags, args, source):
        globalParams["spotlightBrightness"] = args[0]

    def ray_trigger_handler(path, tags, args, source):
        cosmic_ray_events.append((time.time(), 0))

    def palette_select_handler(path, tags, args, source):
        paletteIndex = int(args[0] * (len(palettes) - 1))
	globalParams["palette"] = paletteIndex 

    server = ThreadingOSCServer( (osc_ip_address, osc_port_no) )
    
    for effectName in effects:
        server.addMsgHandler("/effect/%s/opacity" % effectName, effect_opacity_handler)
        for paramName in effects[effectName]['params']:
            server.addMsgHandler("/effect/%s/param/%s" % (effectName, paramName), effect_param_handler)

    server.addMsgHandler("/spotlight/motorSpeed", motor_handler)
    server.addMsgHandler("/spotlight/brightness", spotlight_brightness_handler)
    server.addMsgHandler("default", default_handler)
    server.addMsgHandler("/ray/trigger", ray_trigger_handler)
    server.addMsgHandler("/palette/select", palette_select_handler)
    thread = Thread(target=server.serve_forever)
    thread.setDaemon(True)
    thread.start()
    print "Listening for OSC messages on %s:%s" % (osc_ip_address, osc_port_no)

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
    theta = atan2(y, x)
    if theta < 0:
        theta = 2 * pi + theta
    r = sqrt(x * x + y * y)
    xr = cos(theta)
    yr = sin(theta)

    item['x'] = x
    item['y'] = y
    item['z'] = z
    item['theta'] = theta
    item['r'] = r

    # for backwards compatibility, remove in future?
    item['coord'] = (x, y, z, theta, r, xr, yr)

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

class Tower:

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
    def middle(self):
        for item in chain.from_iterable(imap(self.diagonals_index, range(24))):
            yield item

    @property
    def diagonals(self):
        for item in chain.from_iterable(imap(self.diagonals_index, range(24))):
            yield item

    @property
    def roofline(self):
        for item in chain(reversed(group_strips["roofline-even"][28]), 
                          group_strips["roofline-odd"][30], 
                          reversed(group_strips["roofline-even"][25]),
                          group_strips["roofline-odd"][27], 
                          reversed(group_strips["roofline-even"][35]),
                          group_strips["roofline-odd"][33]):
            yield item

    @property
    def spire(self):
        for item in groups["spire"]:
            yield item

    def spire_ring(self, n):
        for item in islice(groups["spire"], 30 * n, 30 * (n + 1)):
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
    def spotlight(self):
        for item in groups["spotlight"]:
            yield item

    @property
    def clockwise(self):
        for item in chain.from_iterable(imap(self.clockwise_index, range(12))):
            yield item

    @property
    def counter_clockwise(self):
        for item in chain.from_iterable(imap(self.counter_clockwise_index, range(12))):
            yield item

    # Each of the 12 clockwise tower diagonals, continuously across both sections, from the top down
    def clockwise_index(self, index):
        bottomindex = index
        topindex = (index + 2) % 12
        tops = group_strips["top-cw"]
        bots = group_strips["middle-cw"]

        for item in chain(tops[sorted(tops, None, None, True)[topindex]], reversed(bots[sorted(bots)[bottomindex]])):
            yield item

    # Each of the 12 counter-clockwise tower diagonals, continuously across both sections, from the top down
    def counter_clockwise_index(self, index):
        bottomindex = (index + 5) % 12
        topindex = (index + 1) % 12
        tops = group_strips["top-ccw"]
        bots = group_strips["middle-ccw"]

        for item in chain(tops[sorted(tops, None, None, True)[topindex]], reversed(bots[sorted(bots)[bottomindex]])):
            yield item     

    # Each of the 12 clockwise tower diagonals, continuously across both sections, from the bottom up
    def clockwise_index_reversed(self, index):
        bottomindex = (index + 4) % 12
        topindex = (index + 6) % 12
        tops = group_strips["top-cw"]
        bots = group_strips["middle-cw"]

        for item in chain(bots[sorted(bots)[bottomindex]], reversed(tops[sorted(tops, None, None, True)[topindex]])):
            yield item 

    # Each of the 12 counter-clockwise tower diagonals, continuously across both sections, from the bottom up
    def counter_clockwise_index_reversed(self, index):
        bottomindex = (index + 4) % 12 
        topindex = index
        tops = group_strips["top-ccw"]
        bots = group_strips["middle-ccw"]

        for item in chain(bots[sorted(bots)[bottomindex]], reversed(tops[sorted(tops, None, None, True)[topindex]])):
            yield item


    # Each of the 24 tower diagonals, continuously across both sections, from the top down
    def diagonals_index(self, index):
        if index % 2 == 0:
            return self.counter_clockwise_index(int(index/2))
        else:
            return self.clockwise_index(int((index-1)/2))

    # Each of the 24 tower diagonals, continuously across both sections, from the bottom up
    def diagonals_index_reversed(self, index):
        if index % 2 == 0:
            return self.counter_clockwise_index_reversed(int(index/2))
        else:
            return self.clockwise_index_reversed(int((index-1)/2))

    def diagonal_segment(self, index, startrow, endrow=-1):
        if endrow == -1 or endrow < startrow:
            endrow = startrow

        startPixels = [0, 40, 64, 85, 104, 125]
        endPixels = [40, 64, 85, 104, 125, 153]

        for item in islice(self.diagonals_index(index), startPixels[startrow], endPixels[endrow]):
            yield item

    def lightning(self, start, seed=0.7): 
        stripIds = [start]
        last = start
        advance = [1, 3, 5, 7, 9]
        for step in range(5):
            if (int(seed * 31) >> step) & 1:
                if last % 2 == 0:
                    last = (last + advance[step]) % 24
                else:
                    last = (last - advance[step]) % 24
            stripIds.append(last)

        for item in chain.from_iterable(imap(self.diagonal_segment, stripIds, range(6))):
            yield item

    def diamond(self, col, row):
        index = col * 2
        for item in chain(self.diagonal_segment(index, row), 
                          self.diagonal_segment((index - 1 + row * 2) % 24, row),
                          self.diagonal_segment((index + 1 + row * 2) % 24, row + 1),
                          self.diagonal_segment((index - 2          ) % 24, row + 1)):
            yield item

    def diamonds(self, x, y):
        for item in chain.from_iterable(starmap(self.diamond, product(range(x, 12, 2), range(y, 5, 2)))):
            yield item

    @property
    def diamonds_even(self):
        for item in self.diamonds(0, 0):
            yield item

    @property
    def diamonds_odd(self):
        for item in self.diamonds(1, 1):
            yield item

    @property
    def diamonds_even_shifted(self):
        for item in self.diamonds(1, 0):
            yield item

    @property
    def diamonds_odd_shifted(self):
        for item in self.diamonds(0, 1):
            yield item

    @property
    def interior(self):
     	for item in groups["interior"]:
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

    @property
    def events(self):
        return cosmic_ray_events


#-------------------------------------------------------------------------------
# Main loop


def main():

    print
    print '*** sending pixels forever (control-c to exit)...'
    print

    state = State()
    tower = Tower()

    start_time = time.time()
    frame_time = start_time
    last_frame_time = None
    last_motor_update_time = start_time
    accum = 0
    effectsIndex = 0

    for effectName in effects:
        if effects[effectName]["opacity"] > 0:
            print "Running effect " + effectName 

    while True:
        try:
            state.time = frame_time - start_time
            state.absolute_time = frame_time
            
            #if frame_time - last_motor_update_time > 1:
            #    updateSpotlightSpeed()
            #    last_motor_update_time = frame_time
  
            if len(state.events) > 0 and state.events[0][0] < frame_time - 30:
                state.events.remove(state.events[0])

            tower.currentEffectOpacity = 1.0
            for pixel in tower:
                tower.set_pixel_rgb(pixel, (0, 0, 0))

            for effectName in effects:
                if effects[effectName]["opacity"] > 0:
                    tower.currentEffectOpacity = effects[effectName]['opacity']
                    params = effects[effectName]['params']
                    effects[effectName]['action'](tower, state, **params)

            tower.currentEffectOpacity = 1.0
	    for pixel in tower.spotlight:
	        color = tower.get_pixel_rgb(pixel)
	        s = globalParams["spotlightBrightness"]
                color = [color[0] * s, color[1] * s, color[2] * s]
                tower.set_pixel_rgb(pixel, color)

            for pixel in tower.interior:
		tower.set_pixel_rgb(pixel, (1,1,1))

            # press enter to cycle through effects
            if options.interactive:
                i,o,e = select.select([sys.stdin],[],[], 0.0)
                for s in i:
                    if s == sys.stdin:
                        input = sys.stdin.readline()
                        effectsIndex += 1
                        effectsIndex = effectsIndex % len(effects)
                        print "Running effect " + sorted(effects)[effectsIndex]
                        for effectName in effects:
                            effects[effectName]["opacity"] = 0
                        effects[sorted(effects)[effectsIndex]]["opacity"] = 1.0

            for address in clients:
            #for address in ["10.0.0.31:7890", "10.0.0.21:6038", "10.0.0.22:6038"]:
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
