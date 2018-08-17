Water pump timer for Sunsurfers Ecovillage
==========================================

This repository contains the software to control the waterpump in [#Sunsurfers
Ecovillage](http://sunsurfers.ru/projects/eco-village-georgia/). It implements
the simple logic to turn on the pump for some time, then wait for some time and
then repeat. In future it would be triggered by water level monitor, but
currently it just does the cycle for 10 times.

The board is ESP8266-01, running [micropython](http://micropython.org/). Its
GPIO 0/2 pins are connected to two SRD-05VDC-SL-C relays.

How to connect to device
------------------------

1. Clone WebREPL: https://github.com/micropython/webrepl.git
2. Open its webrepl.html in browser
3. Enter the address ws://x.x.x.x:8266/, click "Connect"
4. Enter the password

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
