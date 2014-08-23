from __future__ import division
from itertools import chain
import color_utils
import time
from random import random
from colormath.color_objects import *
from colormath.color_conversions import convert_color
from math import pi, sqrt, cos, sin, atan2, log
twopi = 2 * pi

__all__ = ["spire_fire"]


# Try to implement a fire routine. Not sure if it'll work...
#
# The normal fire routines generally:
#   0. start an array of known geometry
#   1. Cool everything down a little
#   2. heat drives up, and difuses a little
#   3. Randomly ignite sparks.
#   4. fire spreads along the bottom
#
# Challenges:
#
# We have a highly non-uniform polar geomtry. This presents at least 2
# issues. First, we have a circle, so iterating over it for diffusion
# requires us to think about how not to double count at the
# edges. Probably we should create a array and then bulk apply
# it. (Eg: we need 2 phase commit)
#
# Second, the representation of difussion is non-trivial. We can't
# just look at things 1 over in all the columns. Instead, we must do
# something clever. Perhaps we can segment by theta and z? Is theta
# clear enough? pixel is supposed to have (theta, r, z)  

spire_pixel_temp = []
for z in range(16):
    spire_pixel_temp.append(map(lambda x: 0,range(30)))


def spire_fire(tower, state, cooling = 0.2, heating = 0.1, sparking = 0.9999, spark_temp = 0.7):
    # Let's try for a simpler test case -- The spire. 
    #
    # 16 rings, 0-15 is our z axis
    # 30 pixels around
    # And some iterators that will hand them to us.

    # Should chroma and luma move at the same rate, or use
    # different random numners? I don't know. Probably have to
    # try both to see. Maybe cooling effects luma, and heating
    # effects chroma.


    for p in range(30):
        for height in range(16):
            # Step 1: Cool everything a little
            # Things are cooler higher up.
            spire_pixel_temp[height][p] = max(0, spire_pixel_temp[height][p] - random() * (height + 1)/15 * cooling)


            # Step 2: heat goes up and to the sides
            # We calculate this from the perspective of the *current*
            # pixel pulling in heat. Not pushing out heat.
            # (I bet there's a much nicer matrix way to calculate this)
            heat_accumulator = 0
            heat_accumulator += spire_pixel_temp[height][(p+1)%16] * .4
            heat_accumulator += spire_pixel_temp[height][(p-1)%16] * .4
            if height-1 >= 0:
                heat_accumulator += spire_pixel_temp[height-1][p] * .9
                heat_accumulator += spire_pixel_temp[height-1][(p+1)%16] * .36
                heat_accumulator += spire_pixel_temp[height-1][(p-1)%16] * .36
                if height-2 >= 0:
                    heat_accumulator += spire_pixel_temp[height-2][p] * .81
                    #heat_accumulator += spire_pixels[height-2][(p+1)%16] * .3
                    #heat_accumulator += spire_pixels[height-2][(p-1)%16] * .3
            spire_pixel_temp[height][p] = min(1, spire_pixel_temp[height][p] + heat_accumulator * heating)

            # Step 3: Is there a spark?
            # We have 480 pixels, each one a chance for a new fire.
            # 
            if random() > sparking:
                spire_pixel_temp[height][p] = spark_temp
            
            if spire_pixel_temp[height][p] < 0.0001:
                spire_pixel_temp[height][p] = 0

            print spire_pixel_temp[height][p]

            

    # Push all the pixels to the tower

    for i,pixel in enumerate(tower.spire):
        p = i % 30
        z = i % 16
        #print "%s,%s  = %s" % (z, p, spire_pixel_temp[z][p])
        tower.set_pixel(pixel, spire_pixel_temp[z][p], 1)
        
#        tower.set_pixel(pixel, pixel['theta'] / twopi, state.time % 0.5)
        #pixel(col, i) = qsub8( pixel(col,i),  random8(0, ((COOLING * 10) / height) + 2));

 
#    for z in range(15):
#        for pixel in tower.spire_ring(z):
#            print pixel['theta']


def fire_v1(tower, state):
    print "called %s"
    thetas = []
    for pixel in tower:
        if pixel['theta'] > twopi:
            print pixel['theta']
        thetas.append(int(pixel['theta']))



def interpolate_color(val, color1, color2):
    color = []
    for i in range(3):
        color.append( color1[i] + (color2[i] - color1[i])*val )

    return tuple(color)

def wave_z(pixel, wave_width, height, bg_color, color):
    z = pixel['z']
    if 'quad' in pixel:
        z = pixel['quad'][0][2]
    value = 0
    if abs(z - height) < wave_width/2.0:
        value = 1.0/2 + 1.0/2 * cos(pi * (2.0*z/wave_width - height))

    return interpolate_color(value, bg_color, color)

def linear_down_effect(tower, state):
    bg_color = (0, 0, 0)
    period = 5
    total_height = 15.0
    height = total_height - state.time % period * total_height/period
    for pixel in tower:
        tower.set_pixel_rgb(pixel, wave_z(pixel, 2.0, height, bg_color, (1.0, 1.0, 0)))

