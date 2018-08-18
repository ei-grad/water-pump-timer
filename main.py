from machine import Pin, Timer, reset
import micropython
from time import sleep_ms


RELAY_ON = 0
RELAY_OFF = 1

p0 = Pin(0, Pin.OUT, value=RELAY_ON)
p2 = Pin(2, Pin.OUT, value=RELAY_OFF)


def format_seconds(seconds):
    if seconds < 0:
        return '-%s' % format_seconds(-seconds)
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return '%02d:%02d:%02d' % (h, m, s)


class Config(object):

    properties = ['interval', 'duration', 'tick_period', 'rounds']
    defaults = [3600, 600, 1, 10]

    def __init__(self, filename='config.txt'):
        self.filename = filename
        try:
            with open(self.filename) as f:
                config = f.read().strip()
                values = [int(i) for i in config.split()]
        except Exception:
            values = self.defaults
        for k, v in zip(self.properties, values):
            setattr(self, k, v)

    def __repr__(self):
        return '<Config:' + ' '.join([
            str(getattr(self, i)) for i in self.properties
        ]) + '>'

    def set(self, k, v):
        setattr(self, k, v)
        config = ' '.join([str(getattr(self, i)) for i in self.properties])
        print('Saving config: %s' % config)
        with open(self.filename, 'w') as f:
            f.write(config)
            f.write('\n')


class App(object):

    STATE_AFTERWORK = 0
    STATE_PUMP = 1
    STATE_NOTEBOOKS = 2

    def __init__(self):
        self.counter = 0
        self.timer = Timer(-1)
        self.config = Config()
        self.rounds = 0
        self.last_pump_working = 0
        self.current_round_started_at = 0

    def start(self):
        self.last_pump_working = 0
        self.current_round_started_at = 0
        self.timer.deinit()
        self.timer.init(
            mode=Timer.PERIODIC,
            period=self.config.tick_period * 1000,
            callback=self.tick_irq,
        )

    def tick_irq(self, t):
        self.counter += self.config.tick_period
        micropython.schedule(self.tick, self.counter)

    def get_desired_state(self, t):

        if self.rounds >= self.config.rounds:
            return App.STATE_AFTERWORK

        time_since_round_start = t - self.current_round_started_at

        if time_since_round_start < self.config.duration:
            return App.STATE_PUMP

        return App.STATE_NOTEBOOKS

    def tick(self, t):

        if self.rounds < self.config.rounds:
            if t - self.current_round_started_at >= self.config.interval:
                self.rounds += 1
                self.current_round_started_at = t

        desired_state = self.get_desired_state(t)

        if desired_state == App.STATE_PUMP:
            self.ensure_relay_off_on(p2, p0)
            pump_working = t - self.current_round_started_at
            pump_state = 'PUMP_WORKING:%s PUMP_REMAINING:%s' % (
                format_seconds(pump_working),
                format_seconds(self.config.duration - pump_working),
            )
        elif desired_state == App.STATE_NOTEBOOKS:
            self.ensure_relay_off_on(p0, p2)
            pump_state = 'PUMP_STANDBY:%s PUMP_LAUNCH_IN:%s' % (
                format_seconds(t - self.last_pump_working),
                format_seconds(self.current_round_started_at + self.config.interval - t),
            )
        elif desired_state == App.STATE_AFTERWORK:
            pump_state = 'PUMP_STANDBY:%s' % format_seconds(t - self.last_pump_working)
        else:
            pump_state = '<-- UNREACHABLE CODE'

        if p0.value() == 0:
            self.last_pump_working = t

        print('%s %s PUMP:%s NOTEBOOKS:%s ROUNDS:%d %s' % (
            format_seconds(t),
            ['STATE_AFTERWORK', 'STATE_PUMP', 'STATE_NOTEBOOKS'][desired_state],
            ['ON', 'OFF'][p0.value()],
            ['ON', 'OFF'][p2.value()],
            self.rounds,
            pump_state,
        ))

    def ensure_relay_off_on(self, a, b):
        if a.value() != RELAY_OFF:
            a.value(RELAY_OFF)
        if b.value() != RELAY_ON:
            sleep_ms(100)
            b.value(RELAY_ON)

    def reset(self):
        reset()


app = App()
app.start()
