from __future__ import division
from itertools import chain
import color_utils
import time
import random
#from colormath.color_objects import *
#from colormath.color_conversions import convert_color
from math import pi, sqrt, cos, sin, atan2, log
twopi = 2 * pi

__all__ = ["cortex"]


def scaledRGBTupleToHSL(s):
    rgb = sRGBColor(s[0], s[1], s[2], True)
    return convert_color(rgb, HSLColor)
    
def HSLToScaledRGBTuple(hsl):
    return convert_color(hsl, sRGBColor).get_value_tuple()

#sVert = 0.0
#sHorizon = 0.2
sDiag = 0.3
sDiagAlt = 0.0
sArms = 0.0
sRings = 1.0
sSpiral = 0.0
sSpiralAlt = 0.7
vertPeriod = 4.0
horizonPeriod = 4.0
diagPeriod = 4.0
diagAltPeriod = 4.0
armPeriod = 4.0
ringPeriod = 4.0
spiralPeriod = 4.0
#spiralAltPeriod = 4.0
numVert = 40.0
numHorizon = 40.0
numDiag = 40.0
numDiagAlt = 40.0
numArms = 4.0
numRings = 4.0
numSpiral = 4.0
numSpiralAlt = 4.0

spiralAngle = pi/3.0;
spiralAngleAlt = 2.0*pi - pi/3.0;

def cortex(tower, state, sVert = 0.0, sHorizon = 0.0, spiralAltPeriod=4.0):

    Time = state.time / 6
    for pixel in chain(tower.middle, tower.roofline, tower.spire):
        
        if False:
            cX = pixel['x'] / 4 + 0.5
            cY = pixel['z'] / 14
        else:
            cX = pixel['theta'] / (2.0*pi)
            cY = pixel['z'] / 14
        
        newX = log(sqrt(cX*cX + cY*cY))
        newY = atan2(cX, cY)
        
        color = 0.0
        
        # Vertical Bands
        color += sVert * cos(numVert*cY + vertPeriod*Time)
        # Horizontal Bands
        color += sHorizon * cos(numHorizon*cX + horizonPeriod*Time)
        # Diagonal Bands
        color += sDiag * (cos(2.0*numDiag*(cX*sin(spiralAngle) + cY*cos(spiralAngle)) + diagPeriod*Time))
        # Perpendicular Diagonal bands
        color += sDiagAlt * (cos(2.0*numDiagAlt*(cX*sin(spiralAngleAlt) + cY*cos(spiralAngleAlt)) + diagAltPeriod*Time))
        # Arms
        color += sArms * cos(numArms*newY + armPeriod*Time)
        # Rings
        color += sRings * cos(numRings*newX + ringPeriod*Time)
        # Spirals
        color += sSpiral * (cos(2.0*numSpiral*(newX*sin(spiralAngle) + newY*cos(spiralAngle)) + spiralPeriod*Time))
        # Alt Spirals
        color += sSpiralAlt * (cos(2.0*numSpiralAlt*(newX*sin(spiralAngleAlt) + newY*cos(spiralAngleAlt)) + spiralAltPeriod*Time))
        #overall brightness/color
        color *= cos(Time/10.0)
        

        tower.set_pixel(pixel, (sin( color + Time / 3.0 ) * 0.75), color * 0.5)
    
    for pixel in chain(tower.railing, tower.base):
        tower.set_pixel(pixel, (pixel['theta'] / twopi + state.time/60) % 1.0, (state.time % 30) / 60 + 0.5)
