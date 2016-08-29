#!/bin/sh
. /home/pi/local/wheel/bin/activate
export WHEEL_HOME=/home/pi/HumanMusicWheel/dewbUpdate/CosmicPraise

#nodejs $WHEEL_HOME/layout/generate_layout_wheel.js > $WHEEL_HOME/layout/wheel.json
pypy $WHEEL_HOME/client/python/wheel.py --layout $WHEEL_HOME/layout/wheel.json -f 60
