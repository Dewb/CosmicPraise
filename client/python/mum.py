from __future__ import division
import time
import sys
import optparse
import random
import select

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


#-------------------------------------------------------------------------------
# parse layout file

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


def set_pixel_rgb(item, color):
    clients[item['address']].channelPixels[channels[item['address']]][item['index']] = color

print
print '*** sending pixels forever (control-c to exit)...'
print

start_time = time.time()
frame_time = start_time
last_frame_time = None
accum = 0

while True:
    t = frame_time - start_time

    # do stuff here

    for pixel in json_items:
        set_pixel_rgb(pixel, (255, 0, 0))


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


