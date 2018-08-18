from machine import Timer
import micropython
from time import sleep_ms

from relay import Relay


def format_seconds(seconds):
    if seconds < 0:
        return '-%s' % format_seconds(-seconds)
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return '%02d:%02d:%02d' % (h, m, s)


class Config(object):

    def __init__(self):
        with open('config.txt') as f:
            self.interval, self.duration, self.tick_period, self.rounds = [
                int(i) for i in f.read().split()
            ]

    def save(self):
        config = '%d %d %d %d' % (
            self.interval, self.duration, self.tick_period, self.rounds
        )
        print('Saving config:', config)
        with open('config.txt', 'w') as f:
            f.write(config)


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

    def __init__(self, pump_relay, notebooks_relay):
        self.pump_relay = pump_relay
        self.notebooks_relay = notebooks_relay
        self.running = False
        self.rounds = 0
        self.time = 0
        self.last_pump_working = 0
        self.current_round_started_at = 0
        self.timer = Timer(-1)
        self.config = Config()

    def start(self):
        self.running = True
        self.rounds = 0
        self.time = 0
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
        self.time += self.config.tick_period
        micropython.schedule(lambda x: self.tick(), 0)

    def get_desired_state(self):

        if self.rounds >= self.config.rounds:
            return State.AFTERWORK

        time_since_round_start = self.time - self.current_round_started_at

        if time_since_round_start < self.config.duration:
            return State.PUMP

        return State.NOTEBOOKS

    def state(self):
        if not self.running:
            return State.STOP
        if self.rounds >= self.config.rounds:
            return State.AFTERWORK
        if self.pump_relay.is_active() and not self.notebooks_relay.is_active():
            return State.PUMP
        if self.notebooks_relay.is_active() and not self.pump_relay.is_active():
            return State.NOTEBOOKS
        return State.UNKNOWN

    def get_status(self):
        state = self.state()
        if state == State.PUMP:
            pump_working = self.time - self.current_round_started_at
            pump_state = 'PUMP_WORKING:%s PUMP_REMAINING:%s' % (
                format_seconds(pump_working),
                format_seconds(self.config.duration - pump_working),
            )
        elif state == State.NOTEBOOKS:
            pump_state = 'PUMP_STANDBY:%s' % format_seconds(self.time - self.last_pump_working)
            if self.rounds < self.config.rounds - 1:
                pump_state += ' PUMP_LAUNCH_IN:%s' % format_seconds(
                    self.current_round_started_at + self.config.interval - self.time)
        else:
            pump_state = 'PUMP_STANDBY:%s' % format_seconds(self.time - self.last_pump_working)

        return '%s %s PUMP:%s NOTEBOOKS:%s ROUNDS:%d/%d %s' % (
            format_seconds(self.time),
            State.name(state),
            self.pump_relay.state(),
            self.notebooks_relay.state(),
            self.rounds, self.config.rounds,
            pump_state,
        )

    def tick(self):

        if self.rounds < self.config.rounds:
            if self.time - self.current_round_started_at >= self.config.interval:
                self.rounds += 1
                self.current_round_started_at = self.time

        desired_state = self.get_desired_state()

        if desired_state == State.PUMP:
            if not not self.notebooks_relay.is_active():
                self.notebooks_relay.switch(Relay.OFF)
            if not self.pump_relay.is_active():
                sleep_ms(100)
                self.pump_relay.switch(Relay.ON)
        elif desired_state == State.NOTEBOOKS:
            if not not self.pump_relay.is_active():
                self.pump_relay.switch(Relay.OFF)
            if not self.notebooks_relay.is_active():
                sleep_ms(100)
                self.notebooks_relay.switch(Relay.ON)

        if self.state() != desired_state:
            print("Error: desired state is %s but app.state() says it is %s" % (
                State.name(desired_state),
                State.name(self.state()),
            ))

        if self.pump_relay.is_active():
            self.last_pump_working = self.time

        print(self.get_status())

    def switch_relays(self):
        if self.state() in [State.PUMP, State.NOTEBOOKS]:
            message = "ERROR: Can't switch relays while the app is in the active state."
        elif self.pump_relay.is_active() and not self.notebooks_relay.is_active():
            self.pump_relay.switch(Relay.OFF)
            sleep_ms(100)
            self.notebooks_relay.switch(Relay.ON)
            message = "Switched to notebooks."
        elif self.notebooks_relay.is_active() and not self.pump_relay.is_active():
            self.notebooks_relay.switch(Relay.OFF)
            sleep_ms(100)
            self.pump_relay.switch(Relay.ON)
            message = "Switched to pump."
        else:
            message = "ERROR: Can't switch PUMP:%s NOTEBOOKS:%s" % (
                self.pump_relay.state(), self.notebooks_relay.state())
        print(message)
        return message
