## How to prep a BBone for Cosmic Praise
8/10/2014

LEDscape instructions here:
https://github.com/Yona-Appletree/LEDscape

1. Determine Debian or Angstrom (whatever's on the board already, Debian preferred)
2. Install LEDScape DTB file
3. Install LEDscape distro in /root/LEDscape
4. Enable LEDscape OPC server service
5. Disable HDMI hardware by uncommenting the relevant line in uEnv.txt
6. Edit /root/LEDScape/run-ledscape to set 120 pixel length
7. Change host name by editing /etc/hostname to cosmic-praise-X (see list below.)
8. Set the BBone to the appropriate static IP (see below.)

### Beaglebone Names (Locations) and Addresses:

```
cosmic-praise-1 (Base): 10.0.0.31
cosmic-praise-2 (Floor): 10.0.0.32
cosmic-praise-3 (Extra): 10.0.0.33
cosmic-praise-4 (Extra2?): 10.0.0.34
```
### Configuring Beaglebone for static IP address

Network configuration unfortunately varies across Linux distros.

**On Angstrom**

TBD. 

**On Debian (and other distros with `/etc/network/interfaces`)**

Edit `/etc/network/interfaces` and add the following lines, where .xx is the address of the BBone in the network plan (see list below.)
 
```
auto eth0
iface eth0 inet static
address 10.0.0.xx
gateway 10.0.0.1
netmask 255.255.255.0
```

**On distros with `conman`**

If `/etc/network/interfaces` doesn't exist you may be are using a flavor of unix that uses conman. Instead, do the following

`cd /usr/lib/conman/test`
`./get-services `

Note the name of the ethernet interface, it will be something like ethernet_1cba8caa91ab_cable 

Set to static with a command similar to 
`./set-ipv4-method ethernet_1cba8caa91ab_cable manual 10.0.0.34 255.255.255.0 10.0.0.1`
 
Note: things may hang or take a while to perform this, after it's done you should be able to `reboot`

