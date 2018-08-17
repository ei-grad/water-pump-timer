from machine import Pin
from time import sleep


p0 = Pin(0, Pin.OUT, value=1)


def get_duration():
    with open('duration.txt', 'r') as f:
        return int(f.read())


def get_interval():
    with open('interval.txt', 'r') as f:
        return int(f.read())


for i in range(10):
    p0.value(0)  # value 0 - turn on
    sleep(get_duration())
    p0.value(1)  # value 1 - turn off
    sleep(get_interval())
