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

