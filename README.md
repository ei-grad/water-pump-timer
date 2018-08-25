Water pump timer for Sunsurfers Ecovillage
==========================================

This repository contains the software to control the waterpump in [#Sunsurfers
Ecovillage](http://sunsurfers.ru/projects/eco-village-georgia/). It implements
the simple logic to turn on the pump for some time, then wait for some time and
then repeat. In future it would be triggered by water level monitor, but
currently it just does the cycle for 10 times.

The board is ESP8266-01, running [micropython](http://micropython.org/). Its
GPIO 0/2 pins are connected to two SRD-05VDC-SL-C relays.

Micropython docs for ESP8266: https://docs.micropython.org/en/latest/esp8266/index.html

Firmware and code
-----------------

The firmware which is flashed to the board via esptool trough the USB TTY is
the micropython firmware binary. It shouldn't be compiled manually, just take
the latest ESP8266 binary release from http://micropython.org/download#esp8266.

During the boot this firmware runs the code from `boot.py` and `main.py` files
located on the board's internal FAT filesystem, which only could be written and
accessible from the Python REPL running on the board. The `main.py` also
imports the code from additional python modules - `app.py`, `webform.py`, etc.

To execute the code the Python interpreter first compiles it to its bytecode
representation. This compilation normaly goes during the script execution or
module import, just in the same environment where it is going to be executed
(in the micropython interpreter running on the ESP8266, in our case).  But it
could be too demanding process in terms of memory resources, and micropython
running on ESP8266 may not be able to compile some complex modules by itself.
So they have to be cross-compiled to `.mpy` files (analog to the `.pyc` files
of the CPython, the official Python implementation for regular platforms). It
is done with the
[mpy-cross](https://github.com/micropython/micropython/tree/master/mpy-cross)
tool before being deployed to ESP8266, see the `deploy.sh` script. The
`main.py` and `boot.py` files shouldn't be compiled because they are always
executed as a scripts, so it is reasonable to keep them short and simple.

The WebREPL interface could be used to put the `boot.py`, `main.py` and
pre-compiled modules to the ESP8266 internal FAT filesystem, see `deploy.sh`
and the instructions in the next section how to use WebREPL to deploy the code.
Also, the USB TTY interface could be used for this purpose too, there is a
[adafruit ampy](https://github.com/adafruit/ampy) tool for this, but I had no
luck to use it successfully yet.

Prerequirements for build and deploy
------------------------------------

* `mpy-cross`

The `mpy-cross` tool from https://github.com/micropython/micropython is needed
to precompile modules to python bytecode.

Just clone the micropython repository, enter the mpy-cross directory, then
`make` and copy the built `mpy-cross` binary somewhere to the `$PATH`, for
example to `/usr/local/bin`.

```bash
git clone https://github.com/micropython/micropython.git
cd micropython/mpy-cross
make
sudo cp ./mpy-cross /usr/local/bin
```

For more information see its
[README.md](https://github.com/micropython/micropython/blob/master/mpy-cross/README.md).

* `webrepl_cli`

The `webrepl_cli.py` tool from https://github.com/micropython/webrepl is needed
to copy the code over WebREPL interface. It could be installed this way:

```bash
curl https://raw.githubusercontent.com/micropython/webrepl/master/webrepl_cli.py > /usr/local/bin/webrepl_cli
chmod +x /usr/local/bin/webrepl_cli
MODULES_DIR=/usr/local/lib/python`python -c "import sys; print('{0.major}.{0.minor}'.format(sys.version_info))"`/site-packages
python -c "import sys; assert '$MODULES_DIR' in sys.path"
curl https://raw.githubusercontent.com/micropython/webrepl/master/websocket_helper.py > "$MODULES_DIR/websocket_helper.py"
```

Initial board configuration
---------------------------

1. Connect ESP8266 via developer board to your PC in firmware mode (hold the
   red button on the down side of the board while connecting).

2. Erase the flash:

```bash
esptool -p /dev/ttyUSB0 -b 115200 erase_flash
```

3. Reattach the board holding red button again and load the micropython firmware to it:

```bash
esptool -p /dev/ttyUSB0 -b 115200 write_flash --flash_mode qio 0x0 ./esp8266-20180511-v1.9.4.bin
```

4. Reattach the developer board with ESP8266 in regular mode (not holding the red button).

5. Connect to the TTY REPL:

```bash
screen /dev/ttyUSB0 115200
```

6. Use the TTY REPL to connect the ESP8266 to WiFi:

First save the wifi credentials to the storage, it would be used by `boot.py`
script to setup the WiFi connection during the boot:

```python
f = open('wifi-creds.txt', 'w')
ssid, password = 'ssid', 'password'  # <-- replace them by actual values
f.write('%s:%s' % (ssid, password))
f.close()
```

Then up the WiFi connection:

```python
import network
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(ssid, password)
```

To ensure that WiFi has been successfully connected and the device received the
IP address from DHCP server check the `wlan.ifconfig()` output:

```python
print('My IP address is', wlan.ifconfig()[0])
```

7. Enable the WebREPL and specify its password.

```python
import webrepl_setup
```

It would ask for required information interactively. Answer `y` to the reset
confirmation (it would do the "soft reset", keeping the WiFi connection
active). This reset is needed to run the WebREPL server.

8. Build and upload code

Now open the new terminal, clone this repository:

```
git clone https://github.com/ei-grad/water-pump-timer.git
cd water-pump-timer
```

Put the WebREPL password you have specified on previous step to the
`WEBREPL_PASSWD` env variable and run `./deploy.sh`:

```
WEBREPL_PASSWD=password ./deploy.sh
```

Deploy process could hangup due to poor network error handling in webrepl
server-side code. If it happens - interrupt the `deploy.sh` with Ctrl-C, and
then return to the USB TTY console and restart the webrepl:

```python
>>> import webrepl
>>> webrepl.start()
```

And then try to run the `./deploy.sh` again. The error could happen for a
couple of times in a row, just start the webrepl again and repeat.

9. Reboot the board:

```python
from machine import reset
reset()
```

or you could just reattach it to USB.

You now should be able to access the web interface on 80 port of the IP address
you could see in wlan.ifconfig() output.

How to connect to the WebREPL to execute commands interactively
---------------------------------------------------------------

1. Clone WebREPL: https://github.com/micropython/webrepl.git
2. Open its webrepl.html in browser
3. Enter the board address `ws://x.x.x.x:8266/` (where the `x.x.x.x` is the IP
   address, which you can get from your WiFi router DHCP leases table, or on
   the TTY while connecting the chip to developer board), and then push the
   "Connect" button.
4. Enter the WebREPL password

Troubleshooting
---------------

The FAT filesystem goes trash in some cases. Often the only way to recover the
device is the full process described in the [Initial board configuration]
section, but in some cases when the REPL is still available (via WebREPL or USB
TTY) formatting the FAT and running `deploy.sh` could be enought.

Format the FAT in REPL:

```python
import uos
import flashbdev
uos.VfsFat.mkfs(flashbdev.bdev)
```

Run `./deploy.sh` in water-pump-timer directory:

```
WEBREPL_PASSWD=password ./deploy.sh
```
