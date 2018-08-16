from machine import Pin
from time import sleep


p0 = Pin(0, Pin.OUT)


def get_duration():
    with open('duration.txt', 'r') as f:
        return int(f.read())


def get_interval():
    with open('interval.txt', 'r') as f:
        return int(f.read())


for i in range(10):
    p0.on()
    sleep(get_duration())
    p0.off()
    sleep(get_interval())
