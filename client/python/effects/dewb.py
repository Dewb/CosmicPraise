__all__ = ["demoEffect", "alignTestEffect"]

import color_utils

def distance2d(x1, y1, x2, y2):
    v = (x2 - x1, y2 - y1)
    return sqrt(v[0] * v[0] + v[1] * v[1])

def plasma(t, accum, x, y):
    phase = accum
    stretch = 0.8 + (sin(t/20) ** 3 + 1.0) * 200
    p1 = ((sin(phase * 1.000) + 0.0) * 2.0, (sin(phase * 1.310) + 0.0) * 2.0)
    p2 = ((sin(phase * 1.770) + 0.0) * 2.0, (sin(phase * 2.865) + 0.0) * 2.0)
    d1 = distance2d(p1[0], p1[1], x, y)
    d2 = distance2d(p2[0], p2[1], x, y)
    f = (sin(d1 * d2 * stretch) + 1.0) * 0.5
    return f * f

def test_color(t, coord, ii, n_pixels, random_values, accum, trigger):
    c = None
    if trigger:
        c = HSLColor(330, 0.1, 0.6 + random.random() * 0.4)
    else:
        x, y, z, = coord
        theta = atan2(y, x)
        dist = sqrt(x * x + y * y + z * z)
        p = plasma(t, accum, theta, z)
        c = HSLColor(360.0 * (t % 6)/6.0 + 4 * dist - 30 * p, 0.6 + p/2, 0.5)
    return HSLToScaledRGBTuple(c)

def cylinderDistanceSquared(r0, theta0, z0, r1, theta1, z1):
    x0 = r0 * cos(theta0)
    y0 = r0 * sin(theta0)
    x1 = r1 * cos(theta1)
    y1 = r1 * sin(theta1)
    v = (x1 - x0, y1 - y0, z1 - z0)
    return v[0] * v[0] + v[1] * v[1] + v[2] * v[2];

def cartesianToCylinderDistanceSquared(x0, y0, z0, r1, theta1, z1):
    x1 = r1 * cos(theta1)
    y1 = r1 * sin(theta1)
    v = (x1 - x0, y1 - y0, z1 - z0)
    return v[0] * v[0] + v[1] * v[1] + v[2] * v[2];

class CosmicRay(object):
    def __init__(self):
        self.theta = random.random() * pi * 2
        self.z = 14.5;
        self.velocity = -(2.8 + random.random() * 1.8)
        self.rotation = 1.2 * random.random() * (1 if random.random() > 0.5 else -1);
        self.size = 0.05 + 0.05 * random.random()
        self.lastUpdate = time.time()

    def tick(self):
        delta = time.time() - self.lastUpdate
        self.lastUpdate += delta

        self.z += self.velocity * delta;
        self.theta = (self.theta + self.rotation * delta) % (2 * pi)


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

    for item in tower.items:
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
    for item in tower.items:
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
