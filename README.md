Mechanica Musica lighting
=============

Simulator and lighting code for Mechanica Musica, a human music wheel

http://douglasruuska.com/human-music-wheel/

Based on the 2014 lighting code for Cosmic Praise

![ScreenShot](https://raw.github.com/Dewb/CosmicPraise/wheel/docs/simulator_wheel.png)


Quickstart
----------

1. Install dependencies

  ```
  sudo pip install colormath 
  ```
  
2. Run the simulator (pre-built for OSX, Ubuntu 14.04 32-bit, and Linux Mint 64-bit; for other platforms, you can get the source and build yourself from our OPC fork here: https://github.com/Dewb/openpixelcontrol) 

  ```
  simulator/osx-10.9/gl_server layout/wheel.json
  ```
  or
  ```
  simulator/linux-ubuntu14.04/gl_server layout/wheel.json
  ```

3. Run the client code to send pixels to the simulator:

  ```
  python client/python/wheel.py -l layout/wheel.json -f 60 -i --sim
  ```
  
4. The client will start running an effect, and you should see it running in the simulator. Go back to the client window and hit Enter to switch to the next effect. (More sophisticated show control is available via OSC, see below.)

About the system
----------------

Lighting control is run by LEDscape running on Beaglebone Blacks receiving OpenPixelControl (TCP)

 section | lights 
---------|--------
base | 24 ColorBurst fixtures, about 12' off the ground, pointing down at the vinyl base cover, which is painted with techniques that react well to color-changing light.
middle | 24 roughly 6 meter WS2812 LED strips crisscrossing along with the steel beams of the tower. Each strip is split into a 4.77m lower section and a 1.33m upper section, just as the steel structural beams are.
railing | 12 CK Fresco coves with two fixtures each, just below the handrail, illuminating the woodcut panels of the tower top railing.
roofline | 6 2.33m WS2812 strips ringing the roof of the tower top
spotlight | A 300W LED spotlight on a rotating bearing above the tower roof
spire | 16 1m WS2812 strips making an 8' antenna atop the tower roof.


How to contribute 
---------------------------

1. Fork the Cosmic Praise repo to your own account.
2. Switch to the "wheel" branch (this branch.)
3. Create a new file in client/python/effects by copying `_blank.py` to `<your name>.py`.
4. Define your effect function (see next section) and put its name in the `__all__` list.
5. Test your code in the simulator and revise. Commit it, then make another one!
6. When they all look beautiful, create a pull request on Github to contribute your changes back to the main repo.

How to write LED effects
-----------

You can see the existing effect library here:
https://github.com/Dewb/CosmicPraise/tree/wheel/client/python/effects

The simplest possible effect would be to just color every pixel in the system the same color (in this case, hue 0 in the default palette, or red.)

```python
def simplestExampleEffect(system, state):
    for pixel in system:
        system.set_pixel(pixel, 0)
```

Slightly more complicated is to color each pixel differently with some math based on its cylindrical coordinates, and the animation time:

```python
def verySimpleExampleEffect(system, state):
    for pixel in system:
        system.set_pixel(pixel, pixel['theta'] / twopi, state.time % 0.5)
```

An effect is just a function that takes two arguments, `system` and `state`, and calls `system.set_pixel(system, chroma, luma)` on whatever parts of the structure it wants to light up. `system.set_pixel` expects a pixel item from an iterator, plus two values: a "chroma" and a "luma" value. These will be mapped to the current palette of the sculpture, so we can overlap or sequence multiple effects and still achieve the effect of a unified aesthetic object. 

`chroma` and `luma` should both range from 0.0 to 1.0. You can think of `chroma` as indexing through an imaginary watercolor paintbox of unknown size, with 0.0 the left side of the box and 1.0 the right side, and `luma` as making it full strength at 1.0, or watering it down to transparent at 0.0.

There is also a `system.set_pixel_rgb(pixel, rgb)`, which expects a RGB tuple of values 0.0-1.0, for effects that must be a specific color, whether for debugging or for a specific aesthetic need. But we encourage you to use `system.set_pixel` unless absolutely necessary.

The tower object also provides iterators over the entire structure, or a certain part, like `system.wheel` or `system.ceiling`. Iterating over these generators gives you pixel items, each of which is a dictionary with information about the pixel including its (x,y,z) coordinates in 3D space, its (theta, r, x)  coordinates in a cylindrical 3D coordinate system centered on the wheel center, its strip index and address, etc. So you can color different parts of the structure with different techniques:

```python
def simpleExampleEffect(system, state):
    # make the wheel blue
    for pixel in system.wheel:
        system.set_pixel_rgb(pixel, (0, 0, 1))
    # make the ceiling red
    for pixel in system.ceiling:
        system.set_pixel_rgb(pixel, (1, 0, 0))
    # fade the doors from blue to red
    height = 15.0
    for pixel in system.doors:
        s = pixel['z'] / height
        system.set_pixel_rgb(pixel, (s, 0, (1 - s)))
    # run a yellow line across the ceiling strips
    n = int(state.time % 5)
    for pixel in system.ceiling_strip(n):
        system.set_pixel_rgb(pixel, (1, 1, 0))
```

The `system` object provides the following methods and generators at the moment:

method | use
-------|----
`system.set_pixel(pixel, chroma, luma)` | Set the color of a pixel according to the current global palette, where chroma and luma range from 0.0 to 1.0. This is the preferred method, for unified color blending across multiple effects.
`system.set_pixel_rgb(pixel, rgb)` | Set the color of a pixel to a RGB tuple, each from 0.0 to 1.0. Use only if strictly necessary.

basic generators | iterates over
----------|-----
`system` or `system.all` | every pixel, in arbitrary order 
`system.wheel` | all the pixels in the wheel
`system.wheel_right`, `system.wheel_left` | just the right and left wheels
`system.doors` | the strips surrounding the doors, 113 px on the left and right rear doors, 140 px on the front door 
`system.front_door` | the front door, 140 pixels
`system.back_door` | the two back doors, 226 pixels
`system.back_door_right`, `system.back_door_left` | just the right or left back door, 113 pixels each
`system.ceiling` | the five strips across the ceiling, in arbitrary order, 565 pixels total
`system.ceiling_strip(n)` | one of the five strips across the ceiling, with n=0 being the far right and n = 4 the far left



The state object provides:

property | purpose
---------|--------
`state.time` | the current time, to drive animations
`state.events` | a list of recent midi key events. Each event is a tuple of (event time, parameter). 
`state.random_values` | a list of 10,000 pregenerated random numbers, consistent across frames
`state.accumulator` | an effect-defined accumulation value, useful for feedback effects
`state.wheel_speeed` | Wheel speed value (in Hertz?) from the FPGA board.
`state.wheel_position` | An estimate of the wheel's current radial offset, in radians, incremented every frame based on the current value of `state.wheel_speed`.

Effect Parameters and OSC
-------------------------

In order to use the OSC features, you'll need to install the pyOSC module.
```
pip install pyosc --pre
```

osc message | effect
------------|--------
/wheel/speed f | Update the wheel speed with float f (see section on state object.)
/note/trigger f | Let the lighting system know about a note event. Optional float param will be stored as event parameter (see state.events)
/palette/select i | Change the global palette to one of three derived from NASA imagery (i = 0, 1, or 2)
/effect/<effect name>/opacity f | Change the opacity of the named effect from 1 (all the way on) to 0 (off.)
/effect/<effect name>/param/<param name> f | Change the value of named effect parameter to f

Effects can define additional named arguments after the (tower, state) arguments. Any named arguments will be slurped up into the OSC server and exposed as endpoints for timeline or interactive control. 

```python
def cortex(tower, state, sVert=0.0, sHorizon=0.0, spiralAltPeriod=4.0):
  ...
```


Running the Client Using Pypy and Python Virtual Environments
-----------------------------------------------

Pypy is a new version of the Python language tools that is *substantially* faster that the default implementation. Virtual environments provide a nice method for keeping python projects and their dependencies locally managed and seperate from the system.  Running pypy inside a virtual environment is the recommended method of running the Cosmic Praise python client.

1. Install virtualenv if it isn't already on your system:

  ```
  $ sudo pip install virtualenv
  ```
  
2. Install pypy. You may be able to install it directly from your system's package manager (e.g. `sudo apt-get install pypy` or `brew install pypy`.) If not, you can download it from http://pypy.org/download.html and link it into /usr/local/bin. 

3. Create a new environment for Cosmic Praise and install the required libraries.

  OS X
  ----
  ```
   $ virtualenv -p /usr/local/bin/pypy $HOME/local/cosmic-praise
   $ . $HOME/local/cosmic-praise/bin/activate
   (cosmic-praise)$ pip install colormath
   (cosmic-praise)$ pip install git+https://bitbucket.org/pypy/numpy.git

  ```
  
  Linux
  -----
   ```
   $ virtualenv -p /usr/bin/pypy $HOME/local/cosmic-praise   
   $ . $HOME/local/cosmic-praise/bin/activate
   (cosmic-praise)$ pip install colormath
   (cosmic-praise)$ sudo apt-get install build-essential pypy-dev git
   (cosmic-praise)$ pip install git+https://bitbucket.org/pypy/numpy.git
   ```

4. Now you can run the Cosmic Praise client in pypy to get much better performance:

  ```
  pypy client/python/cosmicpraise.py -l layout/cosmicpraise.json -f 60 --sim
  ```
  
Python-rtmidi
=============

To receive MIDI events from the spark chamber, the python-rtmidi module is required. If you don't need to use or test this feature, you can ignore this section.

```
  (cosmic-praise)$ sudo apt-get install libasound2-dev libjack-dev
  (cosmic-praise)$ sudo pip install python-rtmidi --pre
```

Ubuntu users may need to build python-rtmidi from the source distro, see the troubleshooting section below.

Troubleshooting
===============

## Segmentation fault running simulator

Make sure you have typed the path to the layout `.json` file correctly. If all else fails, try building your own copy of the simulator from https://github.com/Dewb/openpixelcontrol.

## Pypy client fails with an "ImportError: unable to load _rtmidi.pypy.so"

You need to reinstall python-rtmidi linked with libc++. 

1. `(cosmic-praise)$ pip uninstall python-rtmidi`
2. Download the python-rtmidi source from https://pypi.python.org/pypi/python-rtmidi#downloads
3. Edit `setup.py` and change the line that reads `libraries += ["pthread"]` to `libraries += ["pthread", "stdc++"]`
4. Run `pypy setup.py install` and try running the client again.
