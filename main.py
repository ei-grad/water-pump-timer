from machine import reset  # noqa
import gc
from webform import WebForm
from app import App
from relay import Relay


pump_relay = Relay('PUMP', 0)
load_relay = Relay('LOAD', 2)

print("Starting App")
app = App(pump_relay, load_relay)
app.start()

gc.collect()

print("Starting WebForm")
webform = WebForm(app, wlan.ifconfig()[0], 80)  # noqa: wlan is defined in boot.py
webform.start()
