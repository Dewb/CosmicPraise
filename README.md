Cosmic Praise
=============

![ScreenShot](https://raw.github.com/Dewb/CosmicPraise/master/docs/simulator.png)

Simulator and lighting code for Cosmic Praise, a fifty-two-foot-tall cosmic-ray detector covered in LEDs.

http://douglasruuska.com/cosmic-praise


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

Running the Client Using Pypy and Python Virtual Environments
-----------------------------------------------

Pypy is a new version of the Python language tools that is *substantially* faster that the default implementation. Virtual environments provide a nice method for keeping python projects and their dependencies locally managed and seperate from the system.  Running pypy inside a virtual environment is the recommended method of running the Cosmic Praise python client.

1. Install virtualenv if it isn't already on your system:

  ```
  $ sudo pip install virtualenv
  ```
  
2. Install pypy. You may be able to install it directly from your system's package manager (e.g. `sudo apt-get install pypy` or `brew install pypy`.) If not, you can download it from http://pypy.org/download.html and place it into /usr/local/bin.

3. Once you have virtualenv and pypy installed, create a new environment for Cosmic Praise and install the dependencies:

   ```
   $ virtualenv $HOME/local/cosmic-praise -p /usr/local/bin/pypy pypy
   $ . $HOME/local/cosmic-praise/bin/activate
   (cosmic-praise)$ easy_install -U setuptools
   (cosmic-praise)$ pip install colormath
   (cosmic-praise)$ pip install python-rtmidi --pre
   (cosmic-praise)$ pip install git+https://bitbucket.org/pypy/numpy.git
   ```

4. Now you can run the Cosmic Praise client in pypy to get much better performance:

  ```
  pypy client/python/cosmicpraise.py -l layout/cosmicpraise.json -f 60 --sim
  ```

How to contribute to Cosmic Praise!
---------------------------

1. Fork the Cosmic Praise repo to your own account.
2. Create a new file in client/python/effects named `<your name>.py`.
3. Copy the header block from one of the existing effects files, and edit `__all__` to list the names of your effects.
4. Write your effect code (see next section) and test them in the simulator.
5. When they look beautiful, open a pull request to contribute your changes back to the main repo.

How to write LED effects
-----------

You can see the existing effect library here:
https://github.com/Dewb/CosmicPraise/tree/master/client/python/effects

The simplest possible effect would be to just color every pixel in the tower the same color (in this case, green.)

```python
def simplestExampleEffect(tower, state):
    for pixel in tower:
        tower.set_pixel_color(pixel, (0, 1, 0)))
```

Slightly more complicated is to color each pixel differently with some math based on its cylindrical coordinates, and the animation time:

```python
def verySimpleExampleEffect(tower, state):
    for pixel in tower:
        tower.set_pixel_color(pixel, 
          (pixel['theta'] / twopi, pixel['z'] / 15, state.time % 1))
```

An effect is just a function that takes two arguments, `tower` and `state`, and calls `tower.set_pixel_color` on whatever parts of the structure it wants to light up. Right now, `set_pixel_color` expects a RGB tuple of values 0.0-1.0, but this is likely to change.

The tower object provides iterators over the entire structure, or a certain part, like `tower.railing` or `tower.spire`. Iterating over these generators gives you pixels, each of which is a dictionary with information about the pixel including its (x,y,z) coordinates in 3D space, its (theta, r, z)  coordinates in cylindrical 3D space, its strip index and address, etc. So you can color different parts of the structure with different techniques:

```python
def simpleExampleEffect(tower, state):
    # make the base blue
    for pixel in tower.base:
        tower.set_pixel_color(pixel, (0, 0, 1))
    # make the railing red
    for pixel in tower.railing:
        tower.set_pixel_color(pixel, (1, 0, 0))
    # fade the tower middle from blue to red
    tower_height = 15.0
    for pixel in tower.middle:
        s = pixel['z'] / tower_height
        tower.set_pixel_color(pixel, (s, 0, (1 - s)))
    # and spin a yellow line clockwise around the clockwise tower diagonals
    n = int(state.time % 12)
    for pixel in tower.clockwise_index(n):
        tower.set_pixel_color(pixel, (1, 1, 0))
    # make the roofline and spire flash green
    for pixel in chain(tower.roofline, tower.spire):
        tower.set_pixel_color(pixel, (0, state.time % 1, 0))
```

The tower object provides the following generator methods at the moment:

generator | iterates over
----------|-----
`tower` or `tower.all` | every pixel, in arbitrary order 
`tower.spire` | all the pixels in the spire strips, order TBD 
`tower.roofline` | all the pixels in the roofline strips in clockwise order 
`tower.railing` | the 24 railing cove lights in clockwise order
`tower.middle` | the diagonally crisscrossing strips on the top two steel sections of the tower, in arbitrary order
`tower.base` | the 24 colorburst fixtures illuminating the base section vinyl mural, in clockwise order
`tower.clockwise` | only the clockwise middle diagonal crossing strips
`tower.counterclockwise` | only the counter-clockwise middle diagonal crossing strips
`tower.clockwise_index(n)`, `tower.counterclockwise_index(n)` | where n=0 through 11, one of the 12 specific diagonal strips, pixels ordered from top to bottom
`tower.diagonal_index(n)` | where n=0 through 23, all the diagonal strips in both directions, pixels ordered from top to bottom

The state object provides 

property | purpose
---------|--------
`state.time` | the current time, to drive animations
`state.events` | a list of recent spark chamber events, more details TBD, see demoEffect for one possible use
`state.random_values` | a list of pregenerated random numbers, consistent across frames
`state.accum` | an effect-defined accumulation value, useful for feedback effects
