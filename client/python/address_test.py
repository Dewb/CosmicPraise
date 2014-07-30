#!/usr/bin/env python

"""A demo client for Open Pixel Control
http://github.com/zestyping/openpixelcontrol

Sends red, green, and blue to the first 3 LEDs.

To run:
First start the gl simulator using, for example, the included "wall" layout

    make
    bin/gl_server layouts/wall.json

Then run this script in another shell to send colors to the simulator

    example_clients/example.py

"""

import time
import random
import opc

ADDRESS = '10.42.0.42:7890'

# Create a client object
client = opc.Client(ADDRESS)

# Test if it can connect
if client.can_connect():
    print 'connected to %s' % ADDRESS
else:
    # We could exit here, but instead let's just print a warning
    # and then keep trying to send pixels in case the server
    # appears later
    print 'WARNING: could not connect to %s' % ADDRESS

# Send pixels forever
while True:
    pixels = []
    for strip in range(48):
        #pixels = pixels + [(0, 0, 0)] * channel 
	#pixels.append((255, 0, 0))
        #pixels = pixels + [(0, 0, 0)] * (46 - channel)
        for bit in range(6):
            pixels.append((255, 0, 0) if strip & 1<<bit else (0, 0, 0))
        pixels = pixels + [(0, 0, 0)] * (30 - 6) 
    client.put_pixels(pixels, channel=0)
    time.sleep(0.2)

