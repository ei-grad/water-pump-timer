from machine import Pin


class Relay(object):

    ON = 0
    OFF = 1

    def __init__(self, name, pin_number):
        self.name = name
        try:
            value = int(open('%s.state' % self.name).read())
        except Exception:
            value = Relay.OFF
            with open('%s.state' % self.name, 'w') as f:
                f.write('%d\n' % value)
        self.pin = Pin(pin_number, Pin.OUT, value=value)

    def switch(self, value):
        if self.pin.value() != value:
            print("%s: TURNING %s" % (self.name, 'OFF' if value else 'ON'))
            self.pin.value(value)
            with open('%s.state' % self.name, 'w') as f:
                f.write('%d\n' % value)
        else:
            print("%s is already %s" % (self.name, 'OFF' if value else 'ON'))

    def is_active(self):
        return self.pin.value() == Relay.ON

    def state(self):
        return ['ON', 'OFF'][self.pin.value()]
