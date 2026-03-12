import network
import time
import konfiguration
try:
    import protokoll
except ImportError:
    class protokoll:
        @staticmethod
        def info(*args, **kwargs):
            pass

def start_access_point(ssid=None, password=None, ip=None):
    if ssid is None:
        ssid = konfiguration.WIFI_SSID
    if password is None:
        password = konfiguration.WIFI_PASSWORD
    if ip is None:
        ip = konfiguration.WIFI_IP

    protokoll.info("NET", "AP-Start: SSID=%s IP=%s", ssid, ip)

    ap = network.WLAN(network.AP_IF)
    ap.config(essid=ssid, password=password)
    ap.active(True)
    
    while not ap.active():
        time.sleep(konfiguration.AP_START_WAIT_S)

    ap.ifconfig((ip, konfiguration.WIFI_SUBNET, konfiguration.WIFI_GATEWAY, konfiguration.WIFI_DNS))
    protokoll.info("NET", "AP aktiv: ifconfig=%s", ap.ifconfig())
    
    return ap
