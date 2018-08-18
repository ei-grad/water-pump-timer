#!/bin/bash

set -e
set -x

for i in `ls *.py | grep -v main.py`; do
    ~/repos/micropython/mpy-cross/mpy-cross $i
done

for i in *.mpy; do
    webrepl_cli -p $WEBREPL_PASSWD $i 10.12.1.99:/$i
done

webrepl_cli -p $WEBREPL_PASSWD main.py 10.12.1.99:/main.py
