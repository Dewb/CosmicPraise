Cosmic Praise
=============

Simulator and lighting code for Cosmic Praise, a fifty-two-foot-tall cosmic-ray detector covered in LEDs.

http://douglasruuska.com/cosmic-praise

![ScreenShot](https://raw.github.com/Dewb/CosmicPraise/master/docs/simulator.png)


Quickstart
----------

1. Install dependencies

  ```
  sudo pip install colormath 
  sudo pip install python-rtmidi --pre
  ```
  
2. Run the simulator (pre-built for OSX; Linux binaries might be available soonish; you can get the source and build yourself from our OPC fork here: https://github.com/Dewb/openpixelcontrol) 

  ```
  simulator/osx-10.9/gl_server layout/cosmicpraise.json
  ```

3. Run the client code to send pixels to the simulator:

  ```
  python client/python/cosmicpraise.py -l layout/cosmicpraise.json -f 60 --sim
  ```
  
4. The client will start running an effect, and you should see it running in the simulator. Go back to the client window and hit Enter to switch to the next effect. (More sophisticated show control is in the works.)


How to contribute to Cosmic Praise!
---------------------------

1. Fork the Cosmic Praise repo to your own account.
2. Create a new file in client/python/effects by copying `_blank.py` to `<your name>.py`.
3. Define your effect function (see next section) and put its name in the `__all__` list.
4. Test your code in the simulator and revise. Commit it, then make another one!
5. When they all look beautiful, create a pull request on Github to contribute your changes back to the main repo.

How to write LED effects
-----------

You can see the existing effect library here:
https://github.com/Dewb/CosmicPraise/tree/master/client/python/effects

The simplest possible effect would be to just color every pixel in the tower the same color (in this case, red.)

```python
def simplestExampleEffect(tower, state):
    for pixel in tower:
        tower.set_pixel(pixel, 0)
```

Slightly more complicated is to color each pixel differently with some math based on its cylindrical coordinates, and the animation time:

```python
def verySimpleExampleEffect(tower, state):
    for pixel in tower:
        tower.set_pixel(pixel, pixel['theta'] / twopi, state.time % 0.5)
```

An effect is just a function that takes two arguments, `tower` and `state`, and calls `tower.set_pixel(pixel, chroma, luma)` on whatever parts of the structure it wants to light up. `tower.set_pixel` expects the pixel item from the iterator, plus two values: a "chroma" and a "luma" value. These will be mapped to the current palette of the sculpture, so we can overlap or sequence multiple effects and still achieve the effect of a unified aesthetic object. 

`chroma` and `luma` should both range from 0.0 to 1.0. You can think of `chroma` as indexing through an imaginary watercolor paintbox of unknown size, with 0.0 the left side of the box and 1.0 the right side, and `luma` as making it full strength at 1.0, or watering it down to transparent at 0.0.

There is also a `tower.set_pixel_rgb(pixel, rgb)`, which expects a RGB tuple of values 0.0-1.0, for effects that must be a specific color, whether for debugging or for a specific aesthetic need. But we encourage you to use `tower.set_pixel` unless absolutely necessary.

The tower object also provides iterators over the entire structure, or a certain part, like `tower.railing` or `tower.spire`. Iterating over these generators gives you pixel items, each of which is a dictionary with information about the pixel including its (x,y,z) coordinates in 3D space, its (theta, r, z)  coordinates in cylindrical 3D space, its strip index and address, etc. So you can color different parts of the structure with different techniques:

```python
def simpleExampleEffect(tower, state):
    # make the base blue
    for pixel in tower.base:
        tower.set_pixel_rgb(pixel, (0, 0, 1))
    # make the railing red
    for pixel in tower.railing:
        tower.set_pixel_rgb(pixel, (1, 0, 0))
    # fade the tower middle from blue to red
    tower_height = 15.0
    for pixel in tower.middle:
        s = pixel['z'] / tower_height
        tower.set_pixel_rgb(pixel, (s, 0, (1 - s)))
    # and spin a yellow line clockwise around the clockwise tower diagonals
    n = int(state.time % 12)
    for pixel in tower.clockwise_index(n):
        tower.set_pixel_rgb(pixel, (1, 1, 0))
    # make the roofline and spire flash green
    for pixel in chain(tower.roofline, tower.spire):
        tower.set_pixel_rgb(pixel, (0, state.time % 1, 0))
```

The tower object provides the following methods and generators at the moment:

method | use
-------|----
`tower.set_pixel(pixel, chroma, luma)` | Set the color of a pixel according to the current global palette, where chroma and luma range from 0.0 to 1.0. This is the preferred method, for unified color blending across multiple effects.
`tower.set_pixel_rgb(pixel, rgb)` | Set the color of a pixel to a RGB tuple, each from 0.0 to 1.0. Use only if strictly necessary.

generator | iterates over
----------|-----
`tower` or `tower.all` | every pixel, in arbitrary order 
`tower.spire` | all the pixels in the spire strips, starting at the bottom of the spire and proceeding counterclockwise in each ring
`tower.spire_index(n)` | where n=0 through 15, all the pixels in one specific ring, starting at the bottom of the spire and proceeding counterclockwise in each ring
`tower.roofline` | all the pixels in the roofline strips in counterclockwise order 
`tower.railing` | the 24 railing cove lights in counterclockwise order
`tower.base` | the 24 colorburst fixtures illuminating the base section vinyl mural, in counterclockwise order
`tower.middle`, `tower.diagonals` | the diagonally crisscrossing strips on the top two steel sections of the tower, one strip at a time from top to bottom
`tower.diagonals_index(n)` | where n=0 through 23, a specific diagonal strip, pixels ordered from top to bottom
`tower.clockwise` | only the clockwise middle diagonal crossing strips
`tower.counterclockwise` | only the counter-clockwise middle diagonal crossing strips
`tower.clockwise_index(n)`, `tower.counterclockwise_index(n)` | where n=0 through 11, a specific diagonal strip of a certain direction, pixels ordered from top to bottom
`tower.lightning(start, seed)` | a branching path down the tower middle, similar to a lightning bolt, where start=0 through 23, the starting location of the bolt, and seed is a value from 0.0-1.0 that determines the branching decisions. Still buggy.
`tower.diamond(row, col)` | Four sections of diagonal strip in a diamond pattern. Row counts from 0 to 4 down from the top, column is from 0 to 23 counting counter-clockwise. Still buggy.
`tower.spotlight` | Iterates over just one pixel: a NINE THOUSAND lumen 300W LED spotlight, the kind they use on the Empire State Building and the Zakim Bridge. It's represented in the simulator as a single dot, but it will actually be spinning a tight beam across the playa. Unless we have enough time to put together a network control system, it will probably be spinning at roughly 60-70rpm. If conditions line up right, the beam should be visible like a laser in the dusty air. What crazy things can you come up with to do with it?

The state object provides:

property | purpose
---------|--------
`state.time` | the current time, to drive animations
`state.events` | a list of recent spark chamber events, more details TBD, see demoEffect for one possible use
`state.random_values` | a list of 10,000 pregenerated random numbers, consistent across frames
`state.accumulator` | an effect-defined accumulation value, useful for feedback effects

Running the Client Using Pypy and Python Virtual Environments
-----------------------------------------------

Pypy is a new version of the Python language tools that is *substantially* faster that the default implementation. Virtual environments provide a nice method for keeping python projects and their dependencies locally managed and seperate from the system.  Running pypy inside a virtual environment is the recommended method of running the Cosmic Praise python client.

1. Install virtualenv if it isn't already on your system:

  ```
  $ sudo pip install virtualenv
  ```
  
2. Install pypy. You may be able to install it directly from your system's package manager (e.g. `sudo apt-get install pypy` or `brew install pypy`.) If not, you can download it from http://pypy.org/download.html and place it into /usr/local/bin. 
3. Linux users: Make sure you have your platform's dev tools, plus some additional libraries for the MIDI interface:

  ```
  sudo apt-get install git build-essential libasound2-dev libjack-dev
  ```
  
4. Once you have virtualenv and pypy installed, create a new environment for Cosmic Praise and install the dependencies:

   ```
   $ virtualenv -p /usr/local/bin/pypy $HOME/local/cosmic-praise
   $ . $HOME/local/cosmic-praise/bin/activate
   (cosmic-praise)$ easy_install -U setuptools
   (cosmic-praise)$ sudo apt-get install python-dev [Linux only]
   (cosmic-praise)$ pip install colormath
   (cosmic-praise)$ pip install python-rtmidi --pre
   (cosmic-praise)$ pip install git+https://bitbucket.org/pypy/numpy.git
   ```

5. Now you can run the Cosmic Praise client in pypy to get much better performance:

  ```
  pypy client/python/cosmicpraise.py -l layout/cosmicpraise.json -f 60 --sim
  ```

