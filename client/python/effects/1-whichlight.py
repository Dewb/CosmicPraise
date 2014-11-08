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
H is from 0 to 360
S is from 0 to 1
L is from 0 to 1. 0.5 is balance, 0.5-1 is white

z is 0..15
theta  is 0..2PI
r is 0 to 1.38

index is 0 to 4799
'''

def we_are_waking(tower, state):
    maxindex = 4799
    s = (state.time % 60)

    for pixel in chain(tower.base):
        tower.set_pixel(pixel, ((pixel['index']*10*(1+s) ) % 360) / 360, min(s/15,1.0))

    for pixel in chain(tower.railing):
        if(s>10):
          tower.set_pixel(pixel, ((pixel['index']*10*(1+s) ) % 360) / 360, min((s-10)/20,1.0))

    for pixel in (tower.middle):
        if(s>20):
          tower.set_pixel(pixel, ((pixel['index']*10*(1+(s%20)/10)) % 360) / 360 , min((s-20)/20,1.0))

    for pixel in chain(tower.roofline, tower.spire):
        if(s>30):
            tower.set_pixel(pixel, ((pixel['index']*10*(1+(s%20)/10) )% 360) / 360, 1.0)

    for pixel in tower.spotlight:
        if(s>30):
            tower.set_pixel(pixel, random.random(), 1.0)


    if s%10<5 and s >35:
      for pixel in tower:
        tower.set_pixel(pixel, ((10*(1+10*state.time))% 360) / 360, min(state.time/15, 1.0))

def bloom(tower,state):
    maxtime = 60
    s_time = (state.time % maxtime)/maxtime

    col = (359-150*s_time) / 360
    if(s_time<0.5):
       # for pixel in tower:
        #    tower.set_pixel_rgb(pixel,HSL2RGB(257-(abs(sin(s_time*10)*20)),1,0.5))

        for pixel in chain(tower.spire, tower.spotlight):
            tower.set_pixel(pixel, col, min(s_time*5,0.5))

        for pixel in tower.roofline:
            tower.set_pixel(pixel, col, min(s_time*4,0.5))

        for pixel in tower.railing:
            tower.set_pixel(pixel, col, min(s_time*3,0.5))

        for pixel in tower.middle:
            tower.set_pixel(pixel, col, min(s_time*2,0.5))

        for pixel in tower.base:
            tower.set_pixel(pixel, col, min(s_time,0.5))

    if(s_time>0.5):
        for pixel in chain(tower.spire, tower.spotlight):
            tower.set_pixel(pixel, col, 0.5-min((s_time-0.5)*5,0.5))

        for pixel in tower.roofline:
            tower.set_pixel(pixel, col, 0.5-min((s_time-0.5)*4,0.5))

        for pixel in tower.railing:
            tower.set_pixel(pixel, col, 0.5-min((s_time-0.5)*3,0.5))

        for pixel in tower.middle:
            tower.set_pixel(pixel, col, 0.5-min((s_time-0.5)*2,0.5))

        for pixel in tower.base:
            tower.set_pixel(pixel, col, 0.5-min((s_time-0.5),0.5))

        for pixel in tower:
            tower.set_pixel(pixel, col, 1-s_time)

    for pixel in tower.middle:
        numpix = 1440
        width = 0.3
        p = abs(0.6-s_time)
        if abs(p)<width and random.random()<abs(p-width):
            tower.set_pixel_rgb(pixel, (1,1,1))

#height 1 to 15
#theta interval twopi/16

num_blocks = 20
# theta, height
sky_init = [[random.randint(0,15), random.randint(1,15)] for i in xrange(num_blocks)]
def skyward_gaze(tower,state):
    if len(state.events) == 0:
        return

    maxtime = 60 
    lastevent = state.events[len(state.events)-1][0]
    if lastevent < (state.absolute_time - maxtime):
        return

    base = [4,3,12,2,9,8,10,5,7,6,13,1,0,15,11,14]
    s_time = (state.absolute_time - lastevent)/maxtime
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
                tower.set_pixel_rgb(pixel, (0.2, 0.2, 0.2))

            if pixel['theta']<(p[0]+1)*twopi/16 and \
                pixel['theta']>(p[0])*twopi/16 and \
                pixel['z']<p[1]+1-1 and \
                pixel['z']>p[1]-1:
                tower.set_pixel_rgb(pixel, (0.5, 0.5, 0.5))

            if pixel['theta']<(p[0]+1)*twopi/16 and \
                pixel['theta']>(p[0])*twopi/16 and \
                pixel['z']<p[1]+1 and \
                pixel['z']>p[1]:
                tower.set_pixel_rgb(pixel, (1, 1, 1))



    '''
    for pixel in tower:
        if pixel['theta']<(16*s_time+1)*twopi/16 and pixel['theta']>(16*s_time)*twopi/16:
            tower.set_pixel_rgb(pixel,HSL2RGB(257-(abs(sin(s_time*10)*20)),1,0.2))

        if pixel['theta']<(15+1)*twopi/16 and pixel['theta']>(15)*twopi/16:
            if pixel['z']<(14*s_time+1) and pixel['z']>(14*s_time):
                tower.set_pixel_rgb(pixel,HSL2RGB(257-(abs(sin(s_time*10)*20)),1,0.2))
    '''


