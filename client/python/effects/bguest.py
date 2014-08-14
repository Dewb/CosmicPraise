__all__ = ["linear_down_effect"]

from math import pi, sqrt, cos, sin, atan2


def interpolate_color(val, color1, color2):
    color = []
    for i in range(3):
        color.append( color1[i] + (color2[i] - color1[i])*val )

    return tuple(color)

def wave_z(item, wave_width, height, bg_color, color):
    z = item['coord'][2]
    value = 0
    if abs(z - height) < wave_width/2.0:
        value = 1.0/2 + 1.0/2 * cos(pi * (2.0*z/wave_width - height))

    return interpolate_color(value, bg_color, color)

def linear_down_effect(tower, state):
	ttime = state.time
	bg_color = (0, 0, 0)
	for item in tower:
	    period = 5
	    total_height = 15.0
	    height = total_height - ttime%period * total_height/period
	    tower.set_item_color(item, wave_z(item, 2.0, height, bg_color, (255,255,0)))

