#!/bin/bash

set -e
set -x

rm -f *.mpy

for i in `ls *.py | grep -v main.py | grep -v boot.py`; do
    mpy-cross $i
done

for i in *.mpy webform.tpl boot.py main.py wifi-creds.txt; do
    webrepl_cli -p $WEBREPL_PASSWD $i 10.12.1.99:/$i
    sleep 1
done
