Cosmic Praise
=============

Simulator and lighting code for Cosmic Praise

http://douglasruuska.com/cosmic-praise


Quickstart
----------

1. Install dependencies

  ```
  sudo pip install colormath 
  sudo pip install python-rtmidi --pre
  ```
  
2. Run the simulator (pre-built for OSX; Windows and Linux binaries soonish; you can get the source and build yourself from our OPC fork here: https://github.com/Dewb/openpixelcontrol) 

  ```
  simulator/osx-10.9/gl_server layouts/cosmicpraise.json
  ```

3. Run the client code to send pixels to the simulator:

  ```
  python client/python/cosmicpraise.py -l layouts/cosmicpraise.json
  ```

