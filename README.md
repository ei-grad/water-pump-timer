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

```python
import network
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(ssid, passwd)
```

7. Enable the WebREPL and specify its password.

```python
import webrepl_setup
```

It would ask for required information interactively.

8. Build and upload code

The `mpy-cross` tool from https://github.com/micropython/micropython is needed
to precompile modules to python bytecode.

Put the WebREPL password you have specified on previous step to the
`WEBREPL_PASSWD` env variable, and run `./deploy.sh`:

```
export WEBREPL_PASSWD=password
./deploy.sh
```

9. Reboot the board:

```python
from machine import reset
reset()
```

or you could just reattach it to USB.

How to connect to the configured device
---------------------------------------

1. Clone WebREPL: https://github.com/micropython/webrepl.git
2. Open its webrepl.html in browser
3. Enter the board address `ws://x.x.x.x:8266/` (where the `x.x.x.x` is the IP
   address, which you can get from your WiFi router DHCP leases table, or on
   the TTY while connecting the chip to developer board), and then push the
   "Connect" button.
4. Enter the WebREPL password

Troubleshooting
---------------

Formatting the FAT:

```python
import uos
import flashbdev
uos.VfsFat.mkfs(flashbdev.bdev)
```
