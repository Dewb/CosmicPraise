'''
Blank effects file for Cosmic Praise

Make a copy of this file under your own name and go to town!

See the README on Github for more details. Also check _common.py for potentially useful utility functions.
'''

from __future__ import division
from itertools import chain, islice, imap
import color_utils
import time
import random
from _common import *
from colormath.color_objects import *
from colormath.color_conversions import convert_color
from math import pi, sqrt, cos, sin, atan2, log
import copy
twopi = 2 * pi

__all__ = ["bloom", "we_are_waking", "skyward_gaze"]

'''
Define your effects as functions that take a tower and a state object, like so.

def verySimpleExampleEffect(tower, state):
    for pixel in tower:
        tower.set_pixel(pixel, pixel['theta'] / twopi, state.time % 0.5)

and then edit the __all__ line above to list your effect functions, e.g.:

__all__ = ["verySimpleExampleEffect"]


H is from 0 to 360
S is from 0 to 1
L is from 0 to 1. 0.5 is balance, 0.5-1 is white

z is 0..15
theta  is 0..2PI
r is 0 to 1.38

index is 0 to 4799
'''

def verySimpleExampleEffect(tower, state):
    for pixel in tower:
        tower.set_pixel(pixel, 1, state.time % 0.5)

def HSL2RGB(h,s,l):
    hsl = HSLColor(h,s,l)
    rgb_col = convert_color(hsl, sRGBColor)
    return rgb_col.get_value_tuple()


def simpleExampleEffect(tower, state):

    #full piece
    hsl_col = HSL2RGB(1,1,(state.time/10)%0.5)
    for pixel in tower:
        tower.set_pixel_rgb(pixel, hsl_col)


    base_col = HSL2RGB(264,1,0.1)
    # make the base blue
    for pixel in tower.base:
        tower.set_pixel_rgb(pixel, base_col)


    rail_col = HSL2RGB(0,1,0.5)
    for pixel in tower.railing:
        tower.set_pixel_rgb(pixel, rail_col)

    tower_height = 15.0
    for pixel in tower.middle:
        s = pixel['z'] / tower_height
        tower.set_pixel_rgb(pixel, HSL2RGB(s*360,1,0.5))

    n = int(state.frame % 12)
    for pixel in tower.clockwise_index(n):
        tower.set_pixel_rgb(pixel, (1, 1, 0))

    for pixel in chain(tower.roofline, tower.spire, tower.spotlight):
        tower.set_pixel_rgb(pixel, (0, state.time % 1, 0))


def we_are_waking(tower, state):
    maxindex = 4799
    s = (state.time % 60)

    for pixel in chain(tower.base):
        tower.set_pixel_rgb(pixel, HSL2RGB((pixel['index']*10*(1+s) )% 361,1,min(s/15,0.5)))

    for pixel in chain(tower.railing):
        if(s>10):
          tower.set_pixel_rgb(pixel, HSL2RGB((pixel['index']*10*(1+s) )% 361,1,min((s-10)/20,0.5)))

    for pixel in (tower.middle):
        if(s>20):
          tower.set_pixel_rgb(pixel, HSL2RGB((pixel['index']*10*(1+(s%20)/10) )% 361,1,min((s-20)/20,0.5)))

    for pixel in chain(tower.roofline, tower.spire):
        if(s>30):
            tower.set_pixel_rgb(pixel, HSL2RGB((pixel['index']*10*(1+(s%20)/10) )% 361,1,0.5))

    for pixel in tower.spotlight:
        if(s>30):
            tower.set_pixel_rgb(pixel, HSL2RGB(random.randint(0,360),1,0.5))


    if s%10<5 and s >35:
      for pixel in tower:
        tower.set_pixel_rgb(pixel, HSL2RGB(10*(1+10*state.time)% 360,1,min(state.time/15,0.5)))

def bloom(tower,state):
    maxtime = 60
    s_time = (state.time % maxtime)/maxtime

    col = 360-150*s_time
    if(s_time<0.5):
       # for pixel in tower:
        #    tower.set_pixel_rgb(pixel,HSL2RGB(257-(abs(sin(s_time*10)*20)),1,0.5))

        for pixel in chain(tower.spire, tower.spotlight):
            tower.set_pixel_rgb(pixel,HSL2RGB(col,1,min(s_time*5,0.5)))

        for pixel in tower.roofline:
            tower.set_pixel_rgb(pixel,HSL2RGB(col,1,min(s_time*4,0.5)))

        for pixel in tower.railing:
            tower.set_pixel_rgb(pixel,HSL2RGB(col,1,min(s_time*3,0.5)))

        for pixel in tower.middle:
            tower.set_pixel_rgb(pixel,HSL2RGB(col,1,min(s_time*2,0.5)))

        for pixel in tower.base:
            tower.set_pixel_rgb(pixel,HSL2RGB(col,1,min(s_time,0.5)))

    if(s_time>0.5):
        for pixel in chain(tower.spire, tower.spotlight):
            tower.set_pixel_rgb(pixel,HSL2RGB(col,1,0.5-min((s_time-0.5)*5,0.5)))

        for pixel in tower.roofline:
            tower.set_pixel_rgb(pixel,HSL2RGB(col,1,0.5-min((s_time-0.5)*4,0.5)))

        for pixel in tower.railing:
            tower.set_pixel_rgb(pixel,HSL2RGB(col,1,0.5-min((s_time-0.5)*3,0.5)))

        for pixel in tower.middle:
            tower.set_pixel_rgb(pixel,HSL2RGB(col,1,0.5-min((s_time-0.5)*2,0.5)))

        for pixel in tower.base:
            tower.set_pixel_rgb(pixel,HSL2RGB(col,1,0.5-min((s_time-0.5),0.5)))

        for pixel in tower:
            tower.set_pixel_rgb(pixel,HSL2RGB(col,1,1-s_time))

    for pixel in tower.middle:
        numpix = 1440
        width = 0.3
        p = abs(0.6-s_time)
        if abs(p)<width and random.random()<abs(p-width):
            tower.set_pixel_rgb(pixel,HSL2RGB(col,0,1))

#height 1 to 15
#theta interval twopi/16

num_blocks = 20
# theta, height
sky_init = [[random.randint(0,15), random.randint(1,15)] for i in xrange(num_blocks)]
def skyward_gaze(tower,state):
    base = [4,3,12,2,9,8,10,5,7,6,13,1,0,15,11,14]
    maxtime = 60
    s_time = (state.time % maxtime)/maxtime
    maxheight = 0

    len_blocks = 1+int(s_time*len(sky_init)-1)
    for p in sky_init[:len_blocks]:
        p[1]+=1
        p[1]%=15

        for pixel in tower:

            if pixel['theta']<(p[0]+1)*twopi/16 and \
                pixel['theta']>(p[0])*twopi/16 and \
                pixel['z']<p[1]+1-2 and \
                pixel['z']>p[1]-2:
                tower.set_pixel_rgb(pixel, HSL2RGB(0,0,0.2))

            if pixel['theta']<(p[0]+1)*twopi/16 and \
                pixel['theta']>(p[0])*twopi/16 and \
                pixel['z']<p[1]+1-1 and \
                pixel['z']>p[1]-1:
                tower.set_pixel_rgb(pixel, HSL2RGB(0,0,0.5))

            if pixel['theta']<(p[0]+1)*twopi/16 and \
                pixel['theta']>(p[0])*twopi/16 and \
                pixel['z']<p[1]+1 and \
                pixel['z']>p[1]:
                tower.set_pixel_rgb(pixel, HSL2RGB(0,0,1))



    '''
    for pixel in tower:
        if pixel['theta']<(16*s_time+1)*twopi/16 and pixel['theta']>(16*s_time)*twopi/16:
            tower.set_pixel_rgb(pixel,HSL2RGB(257-(abs(sin(s_time*10)*20)),1,0.2))

        if pixel['theta']<(15+1)*twopi/16 and pixel['theta']>(15)*twopi/16:
            if pixel['z']<(14*s_time+1) and pixel['z']>(14*s_time):
                tower.set_pixel_rgb(pixel,HSL2RGB(257-(abs(sin(s_time*10)*20)),1,0.2))
    '''


