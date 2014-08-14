__all__ = ["cortex"]

from math import log, atan2, sqrt, cos, sin, pi
from colormath.color_objects import *
from colormath.color_conversions import convert_color
from itertools import chain

def scaledRGBTupleToHSL(s):
    rgb = sRGBColor(s[0], s[1], s[2], True)
    return convert_color(rgb, HSLColor)
    
def HSLToScaledRGBTuple(hsl):
    return convert_color(hsl, sRGBColor).get_upscaled_value_tuple()

sVert = 0.0
sHorizon = 0.2
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
spiralAltPeriod = 4.0
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

def cortex(tower, state):

    Time = state.time / 3
    for item in tower:
        
        if True:
            cX = item['coord'][0] / 4 + 0.5
            cY = item['coord'][2] / 14
        else:
            cX = item['coord'][3] / (2.0*pi)
            cY = item['coord'][2] / 14
        
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
        

        tower.set_item_color(item, (sin( color + Time / 3.0 ) * 0.75 * 255, color * 255, sin( color + Time / 3.0 ) * 0.75 * 255))
    
    for item in tower.railing:
        hsl = HSLColor(112, 0.5, 0.5)
        tower.set_item_color(item, HSLToScaledRGBTuple(hsl))
        
    for item in tower.base:
        hsl = HSLColor(282, 0.5, 0.5)
        tower.set_item_color(item, HSLToScaledRGBTuple(hsl))
        
