import gc
import webrepl
import network
from time import sleep


try:
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    with open('wifi-creds.txt') as f:
        ssid, passwd = f.read().strip().split(':')
    wlan.connect(ssid, passwd)
    for i in range(10):
        sleep(1)
        if wlan.ifconfig()[0] != '0.0.0.0':
            break
    else:
        print("DHCP not recieved!")
    print("Wifi '%s' connected. IP Address: %s" % (ssid, wlan.ifconfig()[0]))
except Exception as e:
    print("Can't connect to WiFi: %s", e)

webrepl.start()

gc.collect()
