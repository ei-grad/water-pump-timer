from machine import Timer
import micropython

from relay import Relay


def format_ms(ms):
    if ms < 0:
        return '-%s' % format_ms(-ms)
    seconds = ms // 1000
    ms = ms % 1000
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return '%02d:%02d:%02d.%d' % (h, m, s, ms // 100)


class Config(object):

    def __init__(self):
        try:
            with open('config.txt') as f:
                (
                    self.tick_period,
                    self.load_duration,
                    self.pump_duration,
                    self.rounds,
                    self.load_on_delay,
                ) = [
                    int(i) for i in f.read().split()
                ]
        except Exception:
            self.tick_period = 100
            self.load_duration = 3000
            self.pump_duration = 600
            self.rounds = 10
            self.load_on_delay = 3000

    def save(self):
        config = ' '.join([str(i) for i in (
            self.tick_period,
            self.load_duration,
            self.pump_duration,
            self.rounds,
            self.load_on_delay,
        )])
        print('Saving config:', config)
        try:
            with open('config.txt', 'w') as f:
                f.write(config)
        except OSError as e:
            print("ERROR: couldn't save config:", e)


class State(object):

    PUMP = 0
    PUMP_TO_LOAD = 1
    LOAD = 2
    UNKNOWN = 3

    @staticmethod
    def name(state):
        return [
            'PUMP',
            'PUMP_TO_LOAD',
            'LOAD',
            'UNKNOWN',
        ][state]


class App(object):

    def __init__(self, pump_relay, load_relay):
        self.pump_relay = pump_relay
        self.load_relay = load_relay
        self.running = False
        self.state = self.determine_state()
        self.pause_time = 0
        try:
            self.time, self.rounds = [int(i) for i in open('app.state').read().split()]
        except Exception:
            self.time, self.rounds = 0, 0
        self.last_pump_working = 0
        self.state_changed_at = 0
        self.saved_time_in_current_state = 0
        self.timer = Timer(-1)
        self.config = Config()

    def start(self):
        if self.determine_state() == State.UNKNOWN:
            self.pump_relay.switch(Relay.OFF)
            self.state = State.PUMP_TO_LOAD
        self.running = True
        self.pause_time = 0
        self.rounds = 0
        self.time = 0
        self.last_pump_working = 0
        self.state_changed_at = 0
        self.timer.deinit()
        self.timer.init(
            mode=Timer.PERIODIC,
            period=self.config.tick_period,
            callback=self.tick_irq,
        )

    def resume(self):
        self.running = True

    def pause(self):
        self.running = False

    def tick_irq(self, t):
        micropython.schedule(lambda x: self.tick(), 0)

    def determine_state(self):
        if self.pump_relay.is_active() and not self.load_relay.is_active():
            return State.PUMP
        if self.load_relay.is_active() and not self.pump_relay.is_active():
            return State.LOAD
        return State.UNKNOWN

    def get_status(self):

        if self.state == State.PUMP:
            pump_working = self.time - self.state_changed_at
            pump_state = 'PUMP_WORKING:%s' % format_ms(pump_working)
            if self.running:
                pump_state += ' PUMP_REMAINING:%s' % (
                    format_ms(self.config.pump_duration * 1000 - pump_working),
                )
        elif self.state == State.LOAD:
            pump_state = 'PUMP_STANDBY:%s' % format_ms(self.time - self.last_pump_working)
            if self.running and self.rounds < self.config.rounds:
                pump_state += ' PUMP_LAUNCH_IN:%s' % format_ms(
                    self.state_changed_at + self.pause_time + self.config.load_duration * 1000
                    - self.time)
        elif self.state == State.PUMP_TO_LOAD:
            pump_state = 'PUMP_STANDBY:%s' % format_ms(self.time - self.last_pump_working)
            pump_state += ' LOAD_LAUNCH_IN:%s' % format_ms(
                self.state_changed_at + self.config.load_on_delay - self.time)
        else:
            pump_state = 'PUMP_STANDBY:%s' % format_ms(self.time - self.last_pump_working)

        return 'UPTIME:%s TIMER:%s STATE:%s PUMP:%s LOAD:%s ROUNDS:%d/%d %s' % (
            format_ms(self.time),
            'RUNNING' if self.running else 'STOPPED',
            State.name(self.state),
            self.pump_relay.state(),
            self.load_relay.state(),
            self.rounds, self.config.rounds,
            pump_state,
        )

    def state_changed(self, state):
        if state == State.PUMP_TO_LOAD:
            self.rounds += 1
        self.state = state
        self.state_changed_at = self.time
        self.pause_time = 0
        with open('app.state', 'w') as f:
            f.write('0 %d\n' % self.rounds)

    def tick(self):

        self.time += self.config.tick_period

        if not self.running:
            self.pause_time += self.config.tick_period
            if self.time % 1000 == 0:
                print(self.get_status())
            return

        time_in_current_state = self.time - self.state_changed_at
        if time_in_current_state - self.saved_time_in_current_state > 60000:
            with open('app.state', 'w') as f:
                f.write('%d %d\n' % (time_in_current_state, self.rounds))
            self.saved_time_in_current_state = time_in_current_state

        if self.state == State.PUMP:
            if time_in_current_state >= self.config.pump_duration * 1000 + self.pause_time:
                self.state_changed(State.PUMP_TO_LOAD)
                self.pump_relay.switch(Relay.OFF)
        elif self.state == State.PUMP_TO_LOAD:
            if time_in_current_state >= self.config.load_on_delay + self.pause_time:
                self.state_changed(State.LOAD)
                self.load_relay.switch(Relay.ON)
        elif self.state == State.LOAD:
            if time_in_current_state >= self.config.load_duration * 1000 + self.pause_time:
                if self.rounds < self.config.rounds:
                    self.state_changed(State.PUMP)
                    self.load_relay.switch(Relay.OFF)
                    self.pump_relay.switch(Relay.ON)
                else:
                    self.running = False

        if self.pump_relay.is_active():
            self.last_pump_working = self.time

        if self.time % 1000 == 0:
            print(self.get_status())

    def switch_relays(self):

        if self.state == State.PUMP:
            self.state_changed(State.PUMP_TO_LOAD)
            self.pump_relay.switch(Relay.OFF)
            message = "Switching to LOAD..."

        elif self.state == State.LOAD:
            self.state_changed(State.PUMP)
            self.load_relay.switch(Relay.OFF)
            self.pump_relay.switch(Relay.ON)
            message = "Switched to PUMP"

        else:
            message = "ERROR: Can't switch in state %s (PUMP:%s LOAD:%s)" % (
                self.state, self.pump_relay.state(), self.load_relay.state())

        print(message)

        return message
