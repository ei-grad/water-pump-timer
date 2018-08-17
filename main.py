from machine import Pin, Timer
import micropython


p0 = Pin(0, Pin.OUT, value=1)
p2 = Pin(2, Pin.OUT, value=1)


def read_int(filename):
    with open(filename, 'r') as f:
        return int(f.read())


timer = Timer(0)
counter = 0


def turn_on(t):
    global counter
    counter += 1
    if counter >= 10:
        return
    print("Pump: on")
    p0.value(0)
    timer.init(mode=Timer.ONE_SHOT, period=read_int('duration.txt') * 1000, callback=turn_off_irq)


def turn_off(t):
    print("Pump: off")
    p0.value(1)
    timer.init(mode=Timer.ONE_SHOT, period=read_int('interval.txt') * 1000, callback=turn_on_irq)


def turn_on_irq(t):
    micropython.schedule(turn_on, t)


def turn_off_irq(t):
    micropython.schedule(turn_off, t)


turn_on(0)
