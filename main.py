from machine import Pin, Timer
from machine import reset  # noqa
import micropython
from time import sleep_ms


class Relay(object):

    ON = 0
    OFF = 1

    def __init__(self, name, pin_number, initial_value):
        self.name = name
        self.pin = Pin(pin_number, Pin.OUT, value=initial_value)

    def switch_on(self):
        if self.pin.value() != Relay.ON:
            print("%s: TURNING ON" % self.name)
            self.pin.value(Relay.ON)

    def switch_off(self):
        if self.pin.value() != Relay.OFF:
            print("%s: TURNING OFF" % self.name)
            self.pin.value(Relay.OFF)

    def is_on(self):
        return self.pin.value() == Relay.ON

    def is_off(self):
        return self.pin.value() == Relay.OFF

    def state(self):
        return ['ON', 'OFF'][self.pin.value()]


pump_relay = Relay('PUMP', 0, Relay.OFF)
notebooks_relay = Relay('NOTEBOOKS', 2, Relay.OFF)


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
        return '<Config:' + ';'.join([
            '%s:%s' % (i, getattr(self, i))
            for i in self.properties
        ]) + '>'

    def set(self, k, v):
        setattr(self, k, v)
        config = ' '.join([str(getattr(self, i)) for i in self.properties])
        print('Saving config: %s' % config)
        with open(self.filename, 'w') as f:
            f.write(config)
            f.write('\n')


class State(object):

    STOP = 0
    PUMP = 1
    NOTEBOOKS = 2
    AFTERWORK = 3
    UNKNOWN = 4

    @staticmethod
    def name(state):
        return [
            'STATE_STOP',
            'STATE_PUMP',
            'STATE_NOTEBOOKS',
            'STATE_AFTERWORK',
            'STATE_UNKNOWN',
        ][state]


class App(object):

    def __init__(self):
        self.running = False
        self.rounds = 0
        self.counter = 0
        self.last_pump_working = 0
        self.current_round_started_at = 0
        self.timer = Timer(-1)
        self.config = Config()

    def start(self):
        self.running = True
        self.rounds = 0
        self.counter = 0
        self.last_pump_working = 0
        self.current_round_started_at = 0
        self.timer.deinit()
        self.timer.init(
            mode=Timer.PERIODIC,
            period=self.config.tick_period * 1000,
            callback=self.tick_irq,
        )

    def stop(self):
        self.running = False
        self.timer.deinit()

    def tick_irq(self, t):
        self.counter += self.config.tick_period
        micropython.schedule(self.tick, self.counter)

    def get_desired_state(self, t):

        if self.rounds >= self.config.rounds:
            return State.AFTERWORK

        time_since_round_start = t - self.current_round_started_at

        if time_since_round_start < self.config.duration:
            return State.PUMP

        return State.NOTEBOOKS

    @property
    def state(self):
        if not self.running:
            return State.STOP
        if self.rounds >= self.config.rounds:
            return State.AFTERWORK
        if pump_relay.is_on() and notebooks_relay.is_off():
            return State.PUMP
        if notebooks_relay.is_on() and pump_relay.is_off():
            return State.NOTEBOOKS
        return State.UNKNOWN

    def tick(self, t):

        if self.rounds < self.config.rounds:
            if t - self.current_round_started_at >= self.config.interval:
                self.rounds += 1
                self.current_round_started_at = t

        desired_state = self.get_desired_state(t)

        if desired_state == State.PUMP:
            if not notebooks_relay.is_off():
                notebooks_relay.switch_off()
            if not pump_relay.is_on():
                sleep_ms(100)
                pump_relay.switch_on()
            pump_working = t - self.current_round_started_at
            pump_state = 'PUMP_WORKING:%s PUMP_REMAINING:%s' % (
                format_seconds(pump_working),
                format_seconds(self.config.duration - pump_working),
            )
        elif desired_state == State.NOTEBOOKS:
            if not pump_relay.is_off():
                pump_relay.switch_off()
            if not notebooks_relay.is_on():
                sleep_ms(100)
                notebooks_relay.switch_on()
            pump_state = 'PUMP_STANDBY:%s' % format_seconds(t - self.last_pump_working)
            if self.rounds < self.config.rounds - 1:
                pump_state += ' PUMP_LAUNCH_IN:%s' % format_seconds(
                    self.current_round_started_at + self.config.interval - t)
        else:
            pump_state = 'PUMP_STANDBY:%s' % format_seconds(t - self.last_pump_working)

        if self.state != desired_state:
            print("Error: desired state is %s but app.state says it is %s" % (
                State.name(desired_state),
                State.name(self.state),
            ))

        if pump_relay.is_on():
            self.last_pump_working = t

        print('%s %s PUMP:%s NOTEBOOKS:%s ROUNDS:%d/%d %s' % (
            format_seconds(t),
            State.name(self.state),
            pump_relay.state(),
            notebooks_relay.state(),
            self.rounds, self.config.rounds,
            pump_state,
        ))


def switch_relays():

    if app.state in [State.PUMP, State.NOTEBOOKS]:
        print("Can't switch relays while the app is in active state. You can "
              "execute `app.stop()` to stop the app.")
        return

    if pump_relay.is_on() and notebooks_relay.is_off():
        pump_relay.switch_off()
        sleep_ms(100)
        notebooks_relay.switch_on()

    elif notebooks_relay.is_on() and pump_relay.is_off():
        notebooks_relay.switch_off()
        sleep_ms(100)
        pump_relay.switch_on()

    else:
        print("Can't switch: PUMP:%s NOTEBOOKS:%s" % (
            pump_relay.state(), notebooks_relay.state()))


app = App()
app.start()
