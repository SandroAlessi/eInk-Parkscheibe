from treiber import EinkPIO as EPD_3in7
from zifferblatt_renderer import render_dial
import netzwerk_verwaltung
import webserver
import machine
import utime
import doom_spiel
import konfiguration
import sys
try:
    import protokoll as log
except ImportError:
    class _LogFallback:
        @staticmethod
        def _p(level, tag, msg, *args):
            if args:
                try:
                    msg = msg % args
                except:
                    msg = str(msg)
            print("[%s][%s] %s" % (level, tag, msg))
        @staticmethod
        def debug(tag, msg, *args):
            _LogFallback._p("DEBUG", tag, msg, *args)
        @staticmethod
        def info(tag, msg, *args):
            _LogFallback._p("INFO", tag, msg, *args)
        @staticmethod
        def warn(tag, msg, *args):
            _LogFallback._p("WARN", tag, msg, *args)
        @staticmethod
        def error(tag, msg, *args):
            _LogFallback._p("ERROR", tag, msg, *args)
        @staticmethod
        def exception(tag, msg, exc=None):
            _LogFallback._p("ERROR", tag, msg)
            if exc is not None:
                _LogFallback._p("ERROR", tag, "Exception: %s", exc)
    log = _LogFallback()

def _cfg(name, default, *aliases):
    if hasattr(konfiguration, name):
        return getattr(konfiguration, name)
    for alias in aliases:
        if hasattr(konfiguration, alias):
            return getattr(konfiguration, alias)
    return default

DISPLAY_ROTATION = _cfg("DISPLAY_ROTATION", 90)
DISPLAY_USE_PARTIAL_BUFFER = _cfg("DISPLAY_USE_PARTIAL_BUFFER", True, "DISPLAY_PARTIAL_BUFFER", "USE_PARTIAL_BUFFER")
STATE_DEFAULT_SYNCED = _cfg("STATE_DEFAULT_SYNCED", False)
STATE_DEFAULT_DEMO_MODE = _cfg("STATE_DEFAULT_DEMO_MODE", 1)
STATE_DEFAULT_DEMO_MANUAL_H = _cfg("STATE_DEFAULT_DEMO_MANUAL_H", 0)
STATE_DEFAULT_DEMO_MANUAL_M = _cfg("STATE_DEFAULT_DEMO_MANUAL_M", 0)
STATE_DEFAULT_UPDATE_MODE = _cfg("STATE_DEFAULT_UPDATE_MODE", 1)
STATE_DEFAULT_FORCE_UPDATE = _cfg("STATE_DEFAULT_FORCE_UPDATE", False)
STATE_DEFAULT_DISP_H = _cfg("STATE_DEFAULT_DISP_H", 0)
STATE_DEFAULT_DISP_M = _cfg("STATE_DEFAULT_DISP_M", 0)
STATE_DEFAULT_DOOM_MODE = _cfg("STATE_DEFAULT_DOOM_MODE", False)
STATE_DEFAULT_DOOM_ACTION = _cfg("STATE_DEFAULT_DOOM_ACTION", None)
DST_CHECK_MINUTE = _cfg("DST_CHECK_MINUTE", 0)
DOOM_RENDER_INTERVAL_MS = _cfg("DOOM_RENDER_INTERVAL_MS", 500)
DEMO_STEP_INTERVAL_MS = _cfg("DEMO_STEP_INTERVAL_MS", 5000)
FULL_REFRESH_HOUR = _cfg("FULL_REFRESH_HOUR", 3)
FULL_REFRESH_MINUTE = _cfg("FULL_REFRESH_MINUTE", 33)
HTTP_PORT = _cfg("HTTP_PORT", 80)
LOG_HEARTBEAT_S = _cfg("LOG_HEARTBEAT_S", 10)
DOOM_CPU_FREQ_HZ = _cfg("DOOM_CPU_FREQ_HZ", 200000000)
DOOM_CPU_FREQ_AUTO = _cfg("DOOM_CPU_FREQ_AUTO", True)
DOOM_CPU_FREQ_PRESET_PICO_W_HZ = _cfg("DOOM_CPU_FREQ_PRESET_PICO_W_HZ", 200000000)
DOOM_CPU_FREQ_PRESET_PICO_2W_HZ = _cfg("DOOM_CPU_FREQ_PRESET_PICO_2W_HZ", 260000000)

def _detect_pico_profile():
    machine_id = ""
    try:
        machine_id = str(getattr(sys.implementation, "_machine", ""))
    except:
        machine_id = ""

    m = machine_id.upper()
    # Pico 2 / Pico 2 W = RP2350
    if "RP2350" in m or "PICO 2" in m:
        return "pico2w", machine_id
    # Pico W / Pico = RP2040
    if "RP2040" in m or "PICO W" in m or "PICO" in m:
        return "picow", machine_id
    return "picow", machine_id

def _resolve_doom_cpu_freq():
    if not DOOM_CPU_FREQ_AUTO:
        return DOOM_CPU_FREQ_HZ, "manual"

    profile, machine_id = _detect_pico_profile()
    if profile == "pico2w":
        return DOOM_CPU_FREQ_PRESET_PICO_2W_HZ, "auto:pico2w:" + machine_id
    return DOOM_CPU_FREQ_PRESET_PICO_W_HZ, "auto:picow:" + machine_id

def main():
    # 1. Display initialisieren
    epd = EPD_3in7(
        rotation=DISPLAY_ROTATION,
        use_partial_buffer=DISPLAY_USE_PARTIAL_BUFFER
    )
    epd.init()
    log.info("MAIN", "Display init: rotation=%s partial_buffer=%s", DISPLAY_ROTATION, DISPLAY_USE_PARTIAL_BUFFER)

    # 2. Display ist nach init() weiss — 00:00 als Partial drauf
    render_dial(epd, 0, 0, partial=True)
    log.info("MAIN", "Initiale Anzeige gerendert: 00:00")

    # 3. WLAN-Zugangspunkt starten
    netzwerk_verwaltung.start_access_point()
    log.info("MAIN", "Netzwerk gestartet")

    # 4. Gemeinsamer Zustand zwischen Server und Hauptschleife
    rtc = machine.RTC()
    state = {
        'synced': STATE_DEFAULT_SYNCED,
        'demo_mode': STATE_DEFAULT_DEMO_MODE,         # 0: Aus, 1: Auto, 2: Manuell
        'demo_manual_h': STATE_DEFAULT_DEMO_MANUAL_H, # Gewaehlte Stunde fuer Manuellen Modus
        'demo_manual_m': STATE_DEFAULT_DEMO_MANUAL_M, # Gewaehlte Minute fuer Manuellen Modus
        'update_mode': STATE_DEFAULT_UPDATE_MODE,     # 0: :00, 1: :00/:30, 2: Aus
        'force_update': STATE_DEFAULT_FORCE_UPDATE,   # Sofort Display aktualisieren
        'disp_h': STATE_DEFAULT_DISP_H,               # Angezeigte Stunde
        'disp_m': STATE_DEFAULT_DISP_M,               # Angezeigte Minute
        'doom_mode': STATE_DEFAULT_DOOM_MODE,         # Osterei aktiv
        'doom_action': STATE_DEFAULT_DOOM_ACTION,     # Letzter Befehl (hoch, runter, etc)
    }
    log.info(
        "MAIN",
        "Start-Status: synced=%s demo_mode=%s update_mode=%s doom_mode=%s",
        state['synced'],
        state['demo_mode'],
        state['update_mode'],
        state['doom_mode']
    )

    doom_instance = doom_spiel.DoomGame()
    state['doom_instance'] = doom_instance
    last_doom_mode = False
    last_doom_render = 0

    last_update_minute = -1
    last_full_refresh_day = -1
    demo_hour = 0
    demo_minute = 0
    last_demo_tick = utime.ticks_ms()
    last_heartbeat_ms = utime.ticks_ms()
    last_dst_check_hour = -1
    winter_switched_day = -1
    cpu_freq_base_hz = None
    try:
        cpu_freq_base_hz = machine.freq()
        log.info("MAIN", "CPU Basisfrequenz: %s Hz", cpu_freq_base_hz)
    except Exception as e:
        log.warn("MAIN", "CPU Basisfrequenz nicht lesbar: %s", e)
    doom_cpu_target_hz, doom_cpu_source = _resolve_doom_cpu_freq()
    log.info("MAIN", "DOOM CPU Ziel: %s Hz (%s)", doom_cpu_target_hz, doom_cpu_source)

    def check_updates(epd):
        nonlocal last_update_minute, last_full_refresh_day
        nonlocal demo_hour, demo_minute, last_demo_tick
        nonlocal last_doom_mode, last_doom_render
        nonlocal last_heartbeat_ms
        nonlocal last_dst_check_hour, winter_switched_day
        
        def check_dst(now):
            nonlocal last_dst_check_hour, winter_switched_day
            y, mo, d, wd, h, _, s, _ = now
            # Nur einmal pro Stunde pruefen wenn Minute == 0
            if h == last_dst_check_hour:
                return False
            
            # Hilfsfunktion: Pruefen ob der letzte Sonntag eines Monats vorliegt
            # datetime in MicroPython: wd ist 0-6 fuer Mo-So
            def is_last_sunday(day, month, year):
                # Wie viele Tage hat der Monat?
                days_in_month = 31
                if month == 4 or month == 6 or month == 9 or month == 11:
                    days_in_month = 30
                elif month == 2:
                    days_in_month = 29 if (year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)) else 28
                
                # Wenn Sonntag (wd==6) und innerhalb der letzten 7 Tage des Monats
                return wd == 6 and (days_in_month - day < 7)

            changed = False
            # Wechsel auf Sommerzeit (Maerz, letzter Sonntag, 02:00 -> 03:00)
            if mo == 3 and is_last_sunday(d, mo, y) and h == 2:
                rtc.datetime((y, mo, d, wd, 3, 0, s, 0))
                changed = True
            
            # Umstellung auf Winterzeit (Oktober, letzter Sonntag, 03:00 -> 02:00)
            elif mo == 10 and is_last_sunday(d, mo, y) and h == 3:
                # Um Endlosschleifen zu vermeiden (03:00 -> 02:00 -> 03:00...) pruefen wir ob heute schon umgestellt wurde
                if winter_switched_day != d:
                    rtc.datetime((y, mo, d, wd, 2, 0, s, 0))
                    winter_switched_day = d
                    changed = True

            last_dst_check_hour = h if not changed else -1
            return changed

        def get_stvo_time(h, m):
            # § 13 Abs. 2 StVO: Auf die naechste angefangene halbe Stunde aufrunden
            # Bei Ankunft um hh:00 zeigt die Parkscheibe sofort hh:30 an
            if m < 30:
                return h, 30
            else:
                return (h + 1) % 24, 0

        if hasattr(epd, 'wdt') and epd.wdt:
            epd.wdt.feed()

        now = rtc.datetime()  # (YYYY, MM, DD, WD, HH, MM, SS, MS)
        if LOG_HEARTBEAT_S > 0:
            now_ms = utime.ticks_ms()
            if utime.ticks_diff(now_ms, last_heartbeat_ms) >= LOG_HEARTBEAT_S * 1000:
                last_heartbeat_ms = now_ms
                log.debug(
                    "MAIN",
                    "Heartbeat: rtc=%02d:%02d:%02d demo=%s update=%s doom=%s disp=%02d:%02d",
                    now[4], now[5], now[6],
                    state.get('demo_mode', 0),
                    state.get('update_mode', 1),
                    state.get('doom_mode', False),
                    state.get('disp_h', 0),
                    state.get('disp_m', 0)
                )

        # === SOMMER-/WINTERZEIT CHECK ===
        if state['synced'] and now[5] == DST_CHECK_MINUTE:
            if check_dst(now):
                now = rtc.datetime() # Reload after switch
                state['force_update'] = True
                log.info("MAIN", "DST-Wechsel angewendet: neue Zeit=%02d:%02d", now[4], now[5])

        # === DOOM EASTEREGG ===
        current_doom_mode = state.get('doom_mode', False)
        if current_doom_mode != last_doom_mode:
            # CPU-Boost zur Laufzeit entfernt:
            # Ein dynamischer Aufruf von machine.freq() waehrend das WLAN (CYW43) aktiv ist,
            # desynchronisiert den PIO-Takt des SPI-Busses zum WLAN-Chip.
            # Das fuehrt zu "[CYW43] STALL" und "hdr mismatch" Fehlern sowie dem Abbruch der WLAN-Verbindung.
            try:
                if current_doom_mode:
                    if doom_cpu_target_hz and doom_cpu_target_hz > 0:
                        log.info("MAIN", "WLAN-sicher: CPU Overclock zur Laufzeit uebersprungen (%s Hz)", doom_cpu_target_hz)
                else:
                    if cpu_freq_base_hz:
                        log.info("MAIN", "WLAN-sicher: CPU Basisfrequenz beibehalten (%s Hz)", cpu_freq_base_hz)
            except Exception as e:
                log.warn("MAIN", "CPU Frequenz-Log fehlgeschlagen: %s", e)

            # Einmaliger Clear bei Modus-Wechsel (nur 1x statt 3x)
            epd.init()
            if hasattr(epd, 'wdt') and epd.wdt: epd.wdt.feed()
            
            # Partial bleibt an — DOOM nutzt partial_refresh
            epd.partial_mode_on()
            if current_doom_mode and hasattr(doom_instance, "on_enter_mode"):
                doom_instance.on_enter_mode()
            last_doom_mode = current_doom_mode
            last_doom_render = 0
            state['force_update'] = True
            log.info("MAIN", "DOOM-Modus gewechselt: %s", "AN" if current_doom_mode else "AUS")
            
        if current_doom_mode:
            action = state.get('doom_action')
            if action:
                state['doom_action'] = None
                doom_instance.handle_action(action)
                last_doom_render = 0  # Sofort neu rendern
                log.debug("MAIN", "DOOM-Aktion: %s", action)

            # Alle 500ms automatisch rendern, bei Action sofort
            now_ms = utime.ticks_ms()
            if utime.ticks_diff(now_ms, last_doom_render) > DOOM_RENDER_INTERVAL_MS or state.get('force_update'):
                state['force_update'] = False
                last_doom_render = now_ms
                if hasattr(epd, 'wdt') and epd.wdt: epd.wdt.feed()
                doom_instance.render(epd)
                if hasattr(epd, 'wdt') and epd.wdt: epd.wdt.feed()
            return # Skip rest of logic

        # === SOFORT-UPDATE (nach Sync oder Moduswechsel) ===
        if state['force_update']:
            state['force_update'] = False
            now = rtc.datetime()
            hour, minute = now[4], now[5]
            
            demo_mode = state.get('demo_mode', 0)
            if demo_mode == 1:
                # Automatischer Demo-Modus
                if state.get('demo_reset', False):
                    state['demo_reset'] = False
                    demo_hour = state.get('disp_h', 0)
                    demo_minute = state.get('disp_m', 0)
                disp_h, disp_m = demo_hour, demo_minute
            elif demo_mode == 2:
                # Manueller Demo-Modus
                disp_h, disp_m = state.get('demo_manual_h', 0), state.get('demo_manual_m', 0)
            else:
                # Normaler Parkscheiben-Betrieb
                disp_h, disp_m = get_stvo_time(hour, minute)
                
            if hasattr(epd, 'wdt') and epd.wdt: epd.wdt.feed()
            render_dial(epd, disp_h, disp_m, partial=True)
            if hasattr(epd, 'wdt') and epd.wdt: epd.wdt.feed()
            state['disp_h'] = disp_h
            state['disp_m'] = disp_m
            last_update_minute = minute
            last_demo_tick = utime.ticks_ms()
            log.info("MAIN", "Force-Update: Anzeige=%02d:%02d (demo_mode=%s)", disp_h, disp_m, demo_mode)
            return

        # === DEMO-MODUS (Automatisch) ===
        if state.get('demo_mode', 0) == 1 and not state.get('doom_mode', False):
            elapsed = utime.ticks_diff(utime.ticks_ms(), last_demo_tick)
            if elapsed > DEMO_STEP_INTERVAL_MS:
                demo_minute += 30
                if demo_minute >= 60:
                    demo_minute = 0
                    demo_hour = (demo_hour + 1) % 24
                if hasattr(epd, 'wdt') and epd.wdt: epd.wdt.feed()
                render_dial(epd, demo_hour, demo_minute, partial=True)
                if hasattr(epd, 'wdt') and epd.wdt: epd.wdt.feed()
                state['disp_h'] = demo_hour
                state['disp_m'] = demo_minute
                last_demo_tick = utime.ticks_ms()
                log.debug("MAIN", "Demo-Auto Tick: Anzeige=%02d:%02d", demo_hour, demo_minute)
            return
            
        # === DEMO-MODUS (Manuell) ===
        if state.get('demo_mode', 0) == 2:
            return  # Nichts zu tun, wird bei force_update einmalig gerendert

        # === PARKSCHEIBEN-MODUS ===
        hour, minute, second = now[4], now[5], now[6]
        day = now[2]

        # A. Taeglicher Voll-Refresh um 03:33 (Display-Reinigung)
        if hour == FULL_REFRESH_HOUR and minute == FULL_REFRESH_MINUTE and last_full_refresh_day != day:
            epd.init()  # Hardware-Reset + Clear
            if hasattr(epd, 'wdt') and epd.wdt: epd.wdt.feed()
            render_dial(epd, hour, minute, partial=False)
            if hasattr(epd, 'wdt') and epd.wdt: epd.wdt.feed()
            # Danach sofort in Partial zurueck
            render_dial(epd, hour, minute, partial=True)
            if hasattr(epd, 'wdt') and epd.wdt: epd.wdt.feed()
            last_full_refresh_day = day
            last_update_minute = minute
            log.info("MAIN", "Daily Full-Refresh ausgefuehrt um %02d:%02d", hour, minute)
            return

        # B. Zeitbasiertes Update
        update_mode = state.get('update_mode', 1)

        if update_mode == 1:
            should_update = (minute == 0 or minute == 30) and last_update_minute != minute
        elif update_mode == 0:
            should_update = minute == 0 and last_update_minute != minute
        else:
            should_update = False

        if should_update:
            disp_h, disp_m = get_stvo_time(hour, minute)
            if hasattr(epd, 'wdt') and epd.wdt: epd.wdt.feed()
            render_dial(epd, disp_h, disp_m, partial=True)
            if hasattr(epd, 'wdt') and epd.wdt: epd.wdt.feed()
            state['disp_h'] = disp_h
            state['disp_m'] = disp_m
            last_update_minute = minute
            log.info("MAIN", "Zeit-Update: Anzeige=%02d:%02d (raw=%02d:%02d)", disp_h, disp_m, hour, minute)

    # 5. Server starten mit check_updates Rueckruf
    log.info("MAIN", "Webserver-Start auf Port %s", HTTP_PORT)
    webserver.run_server(state, epd, check_callback=check_updates, port=HTTP_PORT)

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        log.exception("MAIN", "Fataler Fehler in main()", e)
        raise
