Cosmic Praise Data Acquisition Firmware
===============

Supporting code for [Cosmic Praise](http://douglasruuska.com/cosmic-praise/)

Code for the signal amplifier PIC, U6 on the Spark Chamber Electronics
schematic, ics\projects\spark chamber\Signal_amp_1kV.dsn Rev 1.1 by DTVZ.

The original target device is MicroChip PIC16F1518 using the XC8 compiler
v1.32.  Code performs data acquisition from 2 analog channels using the PIC
ADC at 60kHz (30kHz per channel, alternating) sample rate.  On digital signal
GATE_SENSE (RB0), "trigger," 3 more samples per channel are taken and then a
serial broadcast is initiated, sending 3 samples per channel before trigger,
and 3 samples per channel after the trigger at ~115.2kbps.

Please note, this code was written without available hardware. The author has
not yet had a chance to verify that it functions as designed.

The easiest way to build the code is to obtain the MPLAB X IDE and XC8 
compiler from MicroChip, start a new project with the PIC16F1518 target, and
add main.c to the source list.  No special flags or further setup should be
required.

