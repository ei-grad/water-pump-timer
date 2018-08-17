from machine import Pin, Timer, reset
import micropython
from time import sleep_ms


RELAY_ON = 0
RELAY_OFF = 1

p0 = Pin(0, Pin.OUT, value=RELAY_ON)
p2 = Pin(2, Pin.OUT, value=RELAY_OFF)


def read_int(filename):
    with open(filename, 'r') as f:
        return int(f.read())


def format_seconds(seconds):
    if seconds < 0:
        return '-%s' % format_seconds(-seconds)
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    if h > 0:
        return '%dh%02dm%02ds' % (h, m, s)
    return '%dm%02ds' % (seconds // 60, seconds % 60)


class App(object):

    def __init__(self):
        self.counter = 0
        self.tick = self.tick_on_pump
        self.timer = Timer(-1)
        self.tick_period = 1
        self._interval = read_int('interval.txt')
        self._duration = read_int('duration.txt')
        self.rounds = 0
        self.rounds_limit = 3

    @property
    def interval(self):
        return self._interval

    def set_interval(self, value):
        with open('interval.txt', 'w') as f:
            f.write('%d\n' % value)
        self._interval = value

    @property
    def duration(self):
        return self._duration

    def set_duration(self, value):
        with open('duration.txt', 'w') as f:
            f.write('%d\n' % value)
        self._duration = value

    def start(self):
        self.timer.init(
            mode=Timer.PERIODIC,
            period=self.tick_period * 1000,
            callback=self.tick_irq,
        )

    def tick_irq(self, t):
        self.counter += self.tick_period
        micropython.schedule(self.tick, self.counter)

    def tick_on_pump(self, t):
        remaining = self.duration - t % self.interval
        print('%s: PUMP is active, %s before pump power off, pump worked %d rounds' % (
            format_seconds(t),
            format_seconds(remaining),
            self.rounds,
        ))
        if remaining <= 0:
            self.switch_to_notebooks()

    def switch_to_notebooks(self):
        print("turning off the pump")
        p0.value(RELAY_OFF)
        sleep_ms(100)
        print("turning on the notebooks")
        p2.value(RELAY_ON)
        self.rounds += 1
        if self.rounds < self.rounds_limit:
            self.tick = self.tick_on_notebooks
        else:
            self.tick = self.tick_on_afterwork

    def tick_on_notebooks(self, t):
        remaining = self.interval - t % self.interval
        print('%s: NOTEBOOKS is active, %s before pump power on, pump worked %d rounds' % (
            format_seconds(t),
            format_seconds(remaining),
            self.rounds,
        ))
        if remaining > self.interval - self.duration:
            self.switch_to_pump()

    def switch_to_pump(self):
        print("turning off the notebooks")
        p2.value(RELAY_OFF)
        sleep_ms(100)
        print("turning on the pump")
        p0.value(RELAY_ON)
        self.tick = self.tick_on_pump

    def tick_on_afterwork(self, t):
        print('%s, pump is turned off for %s' % (
            format_seconds(t),
            format_seconds(t - self.interval * self.rounds_limit + self.duration),
        ))

    def reset(self):
        reset()


app = App()
app.start()
