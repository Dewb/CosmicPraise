import socket

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.connect(("10.0.0.71", 6565))
s.send("s %d" % 100)
