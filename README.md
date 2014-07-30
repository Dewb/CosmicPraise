Cosmic Praise
=============

Simulator and lighting package for Cosmic Praise.

http://douglasruuska.com/cosmic-praise

Installation Instructions
-------------------------------------------

If you don't have the commmand *virtualenv* installed, you will need to install it the first time:

  ```
  $ sudo pip install virtualenv
  ```

Once you have virtualenv installed, you will need to build and install your environment:

  ```
  $ virtualenv pyenv
  $ . ./pyenv/bin/activate
  (pyenv)$ python setup.py install
  ```

Quickstart
----------

1. Run the simulator (pre-built for OSX; Windows and Linux binaries soonish; you can get the source and build yourself from our OPC fork here: https://github.com/Dewb/openpixelcontrol) 

  ```
  (pyenv)$ gl_server layouts/cosmicpraise.json
  ```

2. Run the client code to send pixels to the simulator:

  ```
  (pyenv)$ cosmicpraise.py -l layouts/cosmicpraise.json
  ```

