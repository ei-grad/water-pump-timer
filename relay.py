from machine import Pin


class Relay(object):

    ON = 0
    OFF = 1

    def __init__(self, name, pin_number, initial_value):
        self.name = name
        self.pin = Pin(pin_number, Pin.OUT, value=initial_value)

    def switch(self, value):
        if self.pin.value() != value:
            print("%s: TURNING %s" % (self.name, 'OFF' if value else 'ON'))
            self.pin.value(value)

    def is_active(self):
        return self.pin.value() == Relay.ON

    def state(self):
        return ['ON', 'OFF'][self.pin.value()]
