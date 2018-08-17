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

2. Erase the flash and load the micropython firmware to it:

```bash
esptool -p /dev/ttyUSB0 -b 115200 erase_flash
esptool -p /dev/ttyUSB0 -b 115200 write_flash --flash_mode qio 0x0 ./esp8266-20180511-v1.9.4.bin
```

3. Reattach the developer board with ESP8266 in regular mode (not holding the red button).

4. Connect to the TTY REPL:

```bash
screen /dev/ttyUSB0 115200
```

4. Use the TTY REPL to connect the ESP8266 to WiFi:

```python
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.scan()
wlan.connect(ssid, passwd)
```

5. Enable the WebREPL and specify its password.

```

```

How to connect to configured device
-----------------------------------

1. Clone WebREPL: https://github.com/micropython/webrepl.git
2. Open its webrepl.html in browser
3. Enter the board address ws://x.x.x.x:8266/, click "Connect"
4. Enter the WebREPL password

Quick reference for REPL
------------------------

Available useful variables:

* `p0` - GPIO pin 0, controls the water pump relay
* `p2` - GPIO pin 2, controls the second relay (not connected for now)

Turn on the pump:

```python
p0.value(0)
```

Turn off the pump:

```python
p0.value(1)
```
