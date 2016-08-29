# OSC example

from OSC import *

c = OSCClient()
c.sendto(OSCMessage("/nextEffect"), ("127.0.0.1", 7000))

m = OSCMessage("/wheel/speed")
m.append(2.0)
c.sendTo(m, ("127.0.0.1", 7000))

