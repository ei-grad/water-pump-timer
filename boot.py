import gc
import webrepl
import network


wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.scan()

with open('wifi-creds.txt') as f:
    ssid, passwd = f.read().strip().split(':')

wlan.connect(ssid, passwd)

webrepl.start()

gc.collect()
