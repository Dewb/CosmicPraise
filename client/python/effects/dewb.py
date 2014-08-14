__all__ = ["demoEffect", "alignTestEffect"]

import color_utils

rays = []

def updateRays(events, frame_time):

    while len(events):
        e = events.pop()
        rays.append(CosmicRay())

    for ray in rays:
        ray.tick()
        if ray.z < 0:
            rays.remove(ray)

def miami_color(t, item, random_values, accum):
    # hue-restricted, faster version of miami.py from OPC samples
    coord = item['coord']
    # make moving stripes for x, y, and z
    x, y, z, theta, r, xr, yr = coord
    y += color_utils.cos(x - 0.2*z, offset=0, period=1, minn=0, maxx=0.6)
    z += color_utils.cos(x, offset=0, period=1, minn=0, maxx=0.3)
    x += color_utils.cos(y - z, offset=0, period=1.5, minn=0, maxx=0.2)

    # make x, y, z -> r, g, b sine waves
    r = color_utils.cos(y, offset=t / 16, period=2.5, minn=0, maxx=1)
    g = color_utils.cos(z, offset=t / 16, period=2.5, minn=0, maxx=1)
    b = color_utils.cos(-x, offset=t / 16, period=2.5, minn=0, maxx=1)
    r, g, b = color_utils.contrast((r, g, b), 0.5, 1.4)

    clampdown = (r + g + b)/2
    clampdown = color_utils.remap(clampdown, 0.4, 0.5, 0, 1)
    clampdown = color_utils.clamp(clampdown, 0, 1)
    clampdown *= 0.8
    r *= clampdown
    g *= clampdown
    b *= clampdown

    g = g * 0.1 + 0.8 * (b + 0.2 * r) / 2 

    return (r*256, g*256, b*256)

def demoEffect(tower, state):
    
    t = state.time
    updateRays(state.events, t)

    for item in tower:
        x, y, z, theta, r, xr, yr = item['coord']
        light = 0

        for ray in rays:
            d = cartesianToCylinderDistanceSquared(xr, yr, z, 1.0, ray.theta, ray.z)
            if d < ray.size:
                light += (ray.size - d) / ray.size

        rgb = miami_color(t, item, random_values, accum)

        color = (rgb[0] + light * 255, rgb[1] + light * 255, rgb[2] + light * 255)
        tower.set_item_color(item, color)


def alignTestEffect(tower, state):
    t = state.time

    angle = (t * pi/12.0) % (2.0 * pi)
    arcwidth = pi/12.0
    for item in tower:
        theta = item['coord'][3]
        #print "theta: %f angle: %f" % (theta, angle)

        delta = abs(theta - angle)

        if delta > pi:
            delta = 2.0 * pi - delta

        color = (0, 0, 127)

        if delta < arcwidth:
            p = delta / arcwidth
            c = HSLColor(360.0 * (1 - p), 1.0, 0.5)
            color = HSLToScaledRGBTuple(c)
    
        tower.set_item_color(item, color)
