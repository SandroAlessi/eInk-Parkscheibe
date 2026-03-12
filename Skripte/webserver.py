import socket
import gc
import konfiguration
try:
    import protokoll
except ImportError:
    class protokoll:
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
            protokoll._p("DEBUG", tag, msg, *args)
        @staticmethod
        def info(tag, msg, *args):
            protokoll._p("INFO", tag, msg, *args)
        @staticmethod
        def warn(tag, msg, *args):
            protokoll._p("WARN", tag, msg, *args)
        @staticmethod
        def error(tag, msg, *args):
            protokoll._p("ERROR", tag, msg, *args)
        @staticmethod
        def exception(tag, msg, exc=None):
            protokoll._p("ERROR", tag, msg)
            if exc is not None:
                protokoll._p("ERROR", tag, "Exception: %s", exc)

def _cfg(name, default):
    return getattr(konfiguration, name, default)

WIFI_IP = _cfg("WIFI_IP", "192.168.4.1")
HTTP_PORT = _cfg("HTTP_PORT", 80)
HTTP_ACCEPT_TIMEOUT_S = _cfg("HTTP_ACCEPT_TIMEOUT_S", 0.05)
HTTP_CONN_TIMEOUT_S = _cfg("HTTP_CONN_TIMEOUT_S", 3.0)
WDT_TIMEOUT_MS = _cfg("WDT_TIMEOUT_MS", 8300)
LOG_HTTP_REQUESTS = _cfg("LOG_HTTP_REQUESTS", True)

# Vorgefertigte HTTP-Antworten
_R200 = b"HTTP/1.1 200 OK\r\nAccess-Control-Allow-Origin: *\r\nConnection: close\r\n\r\nOK"
_R204 = b"HTTP/1.1 204 No Content\r\nAccess-Control-Allow-Origin: *\r\nAccess-Control-Allow-Methods: POST, GET, OPTIONS\r\nAccess-Control-Allow-Headers: Content-Type\r\nConnection: close\r\n\r\n"
_R400 = b"HTTP/1.1 400 Bad Request\r\nConnection: close\r\n\r\nBad Request"
_R302_IP = ("HTTP/1.1 302 Found\r\nLocation: http://{}/\r\nConnection: close\r\n\r\n".format(WIFI_IP)).encode("utf-8")
_R302 = ("HTTP/1.1 302 Found\r\nLocation: http://{}/\r\nConnection: close\r\n\r\n".format(_cfg("WIFI_DOMAIN", "parkscheibe.control"))).encode("utf-8")

_FAVICON_SVG = b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><rect width="100" height="100" rx="12" fill="#034a8a"/><rect x="5" y="5" width="90" height="90" rx="8" fill="#ffffff"/><rect x="10" y="10" width="80" height="80" rx="4" fill="#0461B1"/><path fill-rule="evenodd" d="M 32 18 H 50 A 23 23 0 0 1 50 64 H 48 V 85 H 32 Z M 48 32 V 50 H 50 A 9 9 0 0 0 50 32 Z" fill="#ffffff"/></svg>'

# Globaler Zustand

def _html_page(state):
    update_mode = state.get('update_mode', 1)
    d_mode = state.get('demo_mode', 1)
    dh = state.get('disp_h', 0)
    dm = state.get('disp_m', 0)
    manual_h = state.get('demo_manual_h', 0)
    manual_m = state.get('demo_manual_m', 0)
    return """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover">
    <link rel="icon" type="image/svg+xml" href="/favicon.ico">
    <link rel="apple-touch-icon" href="/apple-touch-icon.png">
    <title>Parkscheibe</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; -webkit-tap-highlight-color: transparent; }
        :root {
            --bg: #1a1a2e;
            --card-bg: #0461B1;
            --text: #fff;
            --card-border: #fff;
            --btn-bg: #0461B1;
            --btn-active: #034a8a;
        }
        body.demo-active {
            --bg: #1a2e1d;
            --card-bg: #0f7a3d;
            --btn-bg: #0f7a3d;
            --btn-active: #0a5c2e;
        }
        body.doom-mode {
            --bg: #000;
            --card-bg: #300000;
            --text: #ff0000;
            --card-border: #ff0000;
            --btn-bg: #500000;
            --btn-active: #800000;
        }
        body { font-family: -apple-system, sans-serif; background: var(--bg); color: var(--text);
               display: flex; justify-content: center; align-items: center; min-height: 100vh; min-height: -webkit-fill-available;
               margin: 0; overflow: hidden; touch-action: none; transition: background 0.2s; 
               user-select: none; -webkit-user-select: none; }
        .card { background: var(--card-bg); padding: 2em; border-radius: 20px;
                border: 3px solid var(--card-border); box-shadow: 0 8px 32px rgba(0,0,0,0.5);
                max-width: 400px; width: 95%; max-height: 95vh; overflow-y: auto; text-align: center; 
                transition: background 0.2s, border 0.2s; scrollbar-width: none; }
        .card::-webkit-scrollbar { display: none; }
        h1 { font-size: 1.6em; margin-bottom: 0.3em; color: var(--text); }
        .sub { color: rgba(255,255,255,0.7); margin-bottom: 1.5em; font-size: 0.9em; }
        .time-small { font-size: 1em; color: var(--text); opacity: 0.7; margin-bottom: 0.2em;
                      font-family: monospace; letter-spacing: 0.05em; }
        .time { font-size: 3.5em; font-weight: bold; color: var(--text); margin-bottom: 0.2em;
                font-family: monospace; letter-spacing: 0.05em; line-height: 1; }
        .mode-label { font-size: 0.8em; color: var(--text); opacity: 0.7; margin-bottom: 1.2em; }
        button { background: var(--btn-bg); color: var(--text); border: 2px solid var(--card-border);
                 padding: 0.8em 1.5em; border-radius: 12px; font-size: 1.1em; cursor: pointer;
                 width: 100%; transition: transform 0.1s, background 0.15s; touch-action: manipulation; }
        button:active { transform: scale(0.95); background: var(--btn-active); }
        #status { margin-top: 1em; font-size: 0.95em; min-height: 1.5em; }
        .ok { color: #a0ffa0; }
        .err { color: #ff6b6b; }
        .setting { margin-top: 1.2em; text-align: left; padding: 1em; background: rgba(255,255,255,0.1);
                   border-radius: 12px; border: 1px solid rgba(255,255,255,0.3); }
        .setting label { display: flex; align-items: center; gap: 0.8em; cursor: pointer; font-size: 1em; }
        .toggle { position: relative; width: 50px; height: 28px; flex-shrink: 0; }
        .toggle input { opacity: 0; width: 0; height: 0; }
        .slider { position: absolute; top: 0; left: 0; right: 0; bottom: 0; background: rgba(255,255,255,0.3);
                  border-radius: 28px; transition: 0.3s; }
        .slider:before { content: ''; position: absolute; height: 22px; width: 22px; left: 3px;
                         bottom: 3px; background: var(--text); border-radius: 50%; transition: 0.3s; }
        .toggle input:checked + .slider { background: var(--text); }
        .toggle input:checked + .slider:before { transform: translateX(22px); background: var(--btn-bg); }
        .info { color: var(--text); opacity: 0.7; font-size: 0.8em; margin-top: 0.5em; }
        select { background: var(--btn-bg); color: var(--text); border: 2px solid rgba(255,255,255,0.3);
                 border-radius: 8px; padding: 0.8em 2em 0.8em 0.8em; font-size: 1em; width: 100%;
                 margin-top: 0.5em; outline: none; appearance: none; -webkit-appearance: none;
                 touch-action: manipulation;
                 background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='8'%3E%3Cpath d='M0 0l6 8 6-8z' fill='white'/%3E%3C/svg%3E");
                 background-repeat: no-repeat; background-position: right 0.8em center; }
                 
        .demo-btn { background: transparent; color: var(--text); border: none;
                    border-radius: 0; padding: 0.15em 0.05em; font-size: inherit; margin: 0;
                    cursor: pointer; display: inline; transition: none; width: auto;
                    font-weight: bold; min-width: 1.2em; min-height: 2em; }
        .demo-btn:active { transform: none; background: rgba(255,255,255,0.15); }

        .time-picker { display: flex; gap: 0.5em; margin-top: 0.5em; }
        .time-picker select { flex: 1; margin-top: 0; text-align: center; }
        #manual_demo_container { transition: opacity 0.3s; }
        
        #doom_controls { display: none; margin-top: 1em; }
        .d-pad { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 0.5em; margin-bottom: 1em; }
        .d-pad button { padding: 1.5em 0; font-weight: bold; font-size: 1.2em; }
        .d-empty { visibility: hidden; }
        #normal_view { display: block; }
        
        /* Slider styling */
        input[type=range] { -webkit-appearance: none; width: 100%; background: transparent; margin: 10px 0; }
        input[type=range]:focus { outline: none; }
        input[type=range]::-webkit-slider-runnable-track { width: 100%; height: 8px; cursor: pointer; background: rgba(255,255,255,0.3); border-radius: 4px; }
        input[type=range]::-webkit-slider-thumb { height: 24px; width: 24px; border-radius: 50%; background: var(--text); cursor: pointer; -webkit-appearance: none; margin-top: -8px; box-shadow: 0 2px 6px rgba(0,0,0,0.5); }
    </style>
</head>
<body>
    <div class="card">
        <h1 id="title_text">Parkscheibe</h1>
        <div id="normal_view">
        <div class="time-small" id="ctime">Aktuell: --:--:--</div>
        <div class="time" id="dtime">""" + f"{dh:02d}:{dm:02d}" + """</div>
        <div class="mode-label" id="mlabel">""" + ("Demo Automatik" if d_mode == 1 else ("Demo Manuell" if d_mode == 2 else ("Parkscheibe" if state.get('synced') else "Nicht synchronisiert"))) + """</div>
        <button onclick="syncTime()">Zeit synchronisieren</button>
        <div id="status"></div>
        <div class="setting">
            <div style="margin-bottom: 0.2em; font-weight:bold; display:flex; justify-content:space-between; align-items:center;">
                <span>
                    <span class="demo-btn" onclick="tryDoom('d', event)">D</span><span class="demo-btn" onclick="tryDoom('e', event)">e</span><span class="demo-btn" onclick="tryDoom('m', event)">m</span><span class="demo-btn" onclick="tryDoom('o', event)">o</span>-<span class="demo-btn" onclick="tryDoom('m', event)">M</span><span class="demo-btn" onclick="tryDoom('o', event)">o</span><span class="demo-btn" onclick="tryDoom('d', event)">d</span><span class="demo-btn" onclick="tryDoom('u', event)">u</span><span class="demo-btn" onclick="tryDoom('s', event)">s</span>
                </span>
                <span id="demo_mode_label" style="color:var(--text); font-size:1em;">
                    """ + ("Automatisch" if d_mode == 1 else ("Manuell" if d_mode == 2 else "Aus")) + """
                </span>
            </div>
            <input type="range" id="demo_mode" min="0" max="2" step="1" value=\"""" + str(d_mode) + """\" oninput="isUpdatingDemo=true; updateDemoModeLabel()" onchange="setDemo(this.value)">
            <div id="manual_demo_container" style="display: """ + ("block" if (d_mode == 2 or state.get('simulated', False)) else "none") + """; margin-top: 1em;">
                <label style="font-size: 0.9em; color: rgba(255,255,255,0.8); display:flex; justify-content:space-between;">
                    <span>Zeit einstellen:</span>
                    <span id="demo_time_label" style="font-weight:bold; font-family:monospace; font-size:1.1em; color:var(--text);">""" + f"{manual_h:02d}:{manual_m:02d}" + """</span>
                </label>
                <div style="margin-top: 0.8em; text-align: left;">
                    <label style="font-size: 0.8em; color: rgba(255,255,255,0.7);">Stunde (0-23)</label>
                    <input type="range" id="demo_h" min="0" max="23" step="1" value=\"""" + str(manual_h) + """\" oninput="isUpdatingDemo=true; updateDemoLabel()" onchange="setDemoTime()">
                </div>
                <div style="margin-top: 0.5em; text-align: left;">
                    <label style="font-size: 0.8em; color: rgba(255,255,255,0.7);">Minute (0 oder 30)</label>
                    <input type="range" id="demo_m" min="0" max="30" step="30" value=\"""" + str(manual_m) + """\" oninput="isUpdatingDemo=true; updateDemoLabel()" onchange="setDemoTime()">
                </div>
                
                <div style="margin-top: 1em; padding-top: 1em; border-top: 1px solid rgba(255,255,255,0.2);">
                    <label style="font-size: 0.9em; color: rgba(255,255,255,0.8); display:block; margin-bottom: 0.5em;">Exaktes Datum/Zeit simulieren (RTC-Ueberschreibung)</label>
                    <input type="datetime-local" id="fake_datetime" style="width: 100%; padding: 0.8em; border-radius: 8px; border: 2px solid rgba(255,255,255,0.3); background: var(--btn-bg); color: var(--text); font-size: 1em; margin-bottom: 0.5em;">
                    <button onclick="setFakeRTC()">Zeit testen</button>
                    <p class="info" style="font-size: 0.75em;">Ueberschreibt die Systemzeit. Perfekt fuer 03:33 Tests oder Sommerzeit-Szenarien.</p>
                </div>
            </div>
        </div>
        <div class="setting">
            <label style="margin-bottom: 0.2em; display:block; font-weight:bold;">Wechsel-Modus</label>
            <select id="update_mode" onchange="setMode(this.value)">
                <option value="1" """ + ("selected" if update_mode == 1 else "") + """>Alle 30 Minuten (hh:00 und hh:30)</option>
                <option value="0" """ + ("selected" if update_mode == 0 else "") + """>Alle 60 Minuten (nur hh:00)</option>
                <option value="2" """ + ("selected" if update_mode == 2 else "") + """>Aus (bleibt stehen)</option>
            </select>
            <p class="info" id="modeinfo">""" + ("Wechsel bei hh:00 und hh:30" if update_mode == 1 else ("Wechsel nur bei hh:00" if update_mode == 0 else "Kein automatischer Wechsel")) + """</p>
        </div>
        </div>
        
        <div id="doom_controls">
            <!-- Doom Status Panel -->
            <div id="doom_status_panel" style="background: rgba(0,0,0,0.5); border: 1px solid var(--card-border); border-radius: 8px; padding: 1em; margin-bottom: 1em; display: none;">
                <div style="display: flex; justify-content: space-between; font-weight: bold; font-family: monospace; font-size: 1.2em; margin-bottom: 0.5em; color: var(--text);">
                    <span id="ds_hp">LP: -</span>
                    <span id="ds_kills">ABSCHUESSE: -</span>
                    <span id="ds_dir">-</span>
                </div>
                <div id="ds_msg" style="color: #ffaa00; font-family: monospace; font-size: 1.1em; margin-bottom: 0.5em; min-height: 1.2em;"></div>
                <button type="button" id="ds_restart_btn" onclick="doomAction('shoot', event)" style="display: none; background: #aa0000; font-weight: bold; margin-bottom: 0.5em;">NEUSTART</button>
            </div>

            <div class="d-pad" id="doom_dpad">
                <div class="d-empty"></div>
                <button type="button" ontouchstart="startDoomAction('up', event)" ontouchend="stopDoomAction(event)" onmousedown="startDoomAction('up', event)" onmouseup="stopDoomAction(event)" onmouseleave="stopDoomAction(event)">W</button>
                <div class="d-empty"></div>
                <button type="button" ontouchstart="startDoomAction('left', event)" ontouchend="stopDoomAction(event)" onmousedown="startDoomAction('left', event)" onmouseup="stopDoomAction(event)" onmouseleave="stopDoomAction(event)">A</button>
                <button type="button" ontouchstart="startDoomAction('down', event)" ontouchend="stopDoomAction(event)" onmousedown="startDoomAction('down', event)" onmouseup="stopDoomAction(event)" onmouseleave="stopDoomAction(event)">S</button>
                <button type="button" ontouchstart="startDoomAction('right', event)" ontouchend="stopDoomAction(event)" onmousedown="startDoomAction('right', event)" onmouseup="stopDoomAction(event)" onmouseleave="stopDoomAction(event)">D</button>
            </div>
            <button type="button" id="doom_fire_btn" ontouchstart="doomAction('shoot', event)" onmousedown="doomAction('shoot', event)" style="margin-bottom: 0.8em; background: #800000; font-weight: bold;">FEUER</button>
            <button type="button" onclick="doomAction('exit')">DOOM BEENDEN</button>
        </div>
    </div>
    <script>
        function calc_stvo(h, m) {
            let sh = h;
            let sm = 30;
            if (m >= 30) { 
                sh = (h + 1) % 24; 
                sm = 0;
            }
            return {h: sh, m: sm};
        }

        // --- Fetch-Wrapper fuer Pico W ---
        // Verhindert abgeworfene Verbindungen durch Serialisierung aller Anfragen
        // und unsichtbares Wiederholen bei Fehlern.
        const originalFetch = window.fetch;
        let activeRequests = 0;
        window.fetch = async function(...args) {
            while (activeRequests > 0) {
                await new Promise(r => setTimeout(r, 50));
            }
            activeRequests++;
            try {
                for (let i = 0; i < 3; i++) {
                    try {
                        const r = await originalFetch(...args);
                        if (!r.ok) throw new Error("Status " + r.status);
                        return r;
                    } catch (e) {
                        if (i === 2) throw e;
                        await new Promise(r => setTimeout(r, 200));
                    }
                }
            } finally {
                activeRequests--;
            }
        };

        let isSyncing = false;
        function syncTime(clearDemo = true) {
            if (isSyncing) return;
            isSyncing = true;
            
            const s = document.getElementById('status');
            if (clearDemo) {
                s.className = ''; s.innerText = 'Sende...';
            }
            const now = new Date();
            const timeStr = now.getHours() + ':' + now.getMinutes() + ':' + now.getSeconds() + 
                            ':' + now.getDate() + ':' + (now.getMonth()+1) + ':' + now.getFullYear() + ':' + now.getDay() + ':0';
            
            fetch('/sync', { method: 'POST', body: timeStr })
            .then(r => r.text())
            .then(() => { 
                if (clearDemo) {
                    s.className = 'ok'; s.innerText = 'Synchronisiert!';
                    document.getElementById('demo_mode').value = 0;
                    updateDemoModeLabel();
                    document.getElementById('manual_demo_container').style.display = 'none';
                    fetch('/demo', { method: 'POST', body: '0' }).catch(() => {});
                }
            })
            .catch(() => {
                if (clearDemo) {
                    s.className = 'err'; s.innerText = 'Fehler!';
                }
            })
            .finally(() => { isSyncing = false; });
        }
        function setMode(val) {
            let info = "Kein automatischer Wechsel";
            if (val == 1) info = "Wechsel bei hh:00 und hh:30";
            else if (val == 0) info = "Wechsel nur bei hh:00";
            document.getElementById('modeinfo').innerText = info;
            fetch('/mode', { method: 'POST', body: String(val) }).catch(() => {});
        }
        function updateDemoModeLabel() {
            const val = document.getElementById('demo_mode').value;
            let label = "Aus";
            if(val == 1) label = "Automatisch";
            else if(val == 2) label = "Manuell";
            document.getElementById('demo_mode_label').innerText = label;
        }
        let isUpdatingDemo = false;
        function setDemo(val) {
            updateDemoModeLabel();
            const container = document.getElementById('manual_demo_container');
            container.style.display = (val == 2) ? 'block' : 'none';
            isUpdatingDemo = true;
            fetch('/demo', { method: 'POST', body: String(val) }).catch(() => {}).finally(() => { setTimeout(() => { isUpdatingDemo = false; }, 500); });
        }
        function updateDemoLabel() {
            const h = document.getElementById('demo_h').value;
            const m = document.getElementById('demo_m').value;
            document.getElementById('demo_time_label').innerText = String(h).padStart(2, '0') + ':' + String(m).padStart(2, '0');
        }
        function setDemoTime() {
            const h = document.getElementById('demo_h').value;
            const m = document.getElementById('demo_m').value;
            isUpdatingDemo = true;
            fetch('/demo_time', { method: 'POST', body: h + ':' + m }).catch(() => {}).finally(() => { setTimeout(() => { isUpdatingDemo = false; }, 500); });
        }
        function setFakeRTC() {
            if (isSyncing) return;
            isSyncing = true;
            const dtEl = document.getElementById('fake_datetime');
            if(!dtEl.value) { isSyncing = false; return; }
            const dt = new Date(dtEl.value);
            // JS Format: yyyy, mm (0-11), dd, hh, min, ss
            const payload = dt.getHours() + ':' + dt.getMinutes() + ':' + dt.getSeconds() + 
                            ':' + dt.getDate() + ':' + (dt.getMonth()+1) + ':' + dt.getFullYear() + ':' + dt.getDay() + ':1';
            
            const s = document.getElementById('status');
            s.className = ''; s.innerText = 'Zeit wird simuliert...';
            
            fetch('/sync', { method: 'POST', body: payload })
            .then(r => r.text())
            .then(() => { 
                s.className = 'ok'; s.innerText = 'Systemuhr auf Fake-Zeit gestellt!'; 
                document.getElementById('demo_mode').value = 0;
                updateDemoModeLabel();
                document.getElementById('manual_demo_container').style.display = 'none';
            })
            .catch(() => { s.className = 'err'; s.innerText = 'Fehler!'; })
            .finally(() => { isSyncing = false; });
        }
        let isPolling = false;
        function pollStatus() {
            if (isPolling) return;
            isPolling = true;
            fetch('/status').then(r => r.json()).then(d => {
                const pad = n => String(n).padStart(2,'0');
                if(d.demo_mode === 0) {
                    let simText = d.simulated ? ' (simuliert)' : '';
                    document.getElementById('ctime').innerText = 'Aktuell: ' + pad(d.curr_h) + ':' + pad(d.curr_m) + ':' + pad(d.curr_s) + simText;
                } else if(d.demo_mode === 1) {
                    document.getElementById('ctime').innerText = 'Demo-Modus (Auto)';
                } else if(d.demo_mode === 2) {
                    document.getElementById('ctime').innerText = 'Demo-Modus (Manuell)';
                }
                
                // UI Sync falls woanders geaendert (ausser wir warten gerade auf Server)
                const selectEl = document.getElementById('demo_mode');
                if (!isUpdatingDemo && selectEl.value != d.demo_mode) {
                    selectEl.value = d.demo_mode;
                    updateDemoModeLabel();
                }
                document.getElementById('manual_demo_container').style.display = (d.demo_mode == 2 || d.simulated) ? 'block' : 'none';

                document.getElementById('dtime').innerText = pad(d.h) + ':' + pad(d.m);
                
                let label = "Nicht synchronisiert";
                if (d.demo_mode === 1) label = "Demo Automatik";
                else if (d.demo_mode === 2) label = "Demo Manuell";
                else if (d.synced) label = "Ankunftzeit (StVO)";
                document.getElementById('mlabel').innerText = label;
                
                let isDemoOrSimulated = (d.demo_mode > 0) || d.simulated;
                if(isDemoOrSimulated) {
                    document.body.classList.add('demo-active');
                } else {
                    document.body.classList.remove('demo-active');
                }
                
                localDoomMode = !!d.doom_mode;
                enableDoomCSS(localDoomMode);

                if (localDoomMode) {
                    document.getElementById('doom_status_panel').style.display = 'block';
                    document.getElementById('ds_hp').innerText = 'LP: ' + (d.doom_hp !== undefined ? d.doom_hp : '-');
                    document.getElementById('ds_kills').innerText = 'ABSCH\u00dcSSE: ' + (d.doom_kills !== undefined ? d.doom_kills : '-');
                    document.getElementById('ds_dir').innerText = d.doom_dir !== undefined ? d.doom_dir : '-';
                    document.getElementById('ds_msg').innerText = d.doom_msg !== undefined ? d.doom_msg : '';
                    
                    if (d.doom_won || d.doom_dead) {
                        document.getElementById('ds_restart_btn').style.display = 'block';
                        document.getElementById('doom_dpad').style.display = 'none';
                        document.getElementById('doom_fire_btn').style.display = 'none';
                    } else {
                        document.getElementById('ds_restart_btn').style.display = 'none';
                        document.getElementById('doom_dpad').style.display = 'grid';
                        document.getElementById('doom_fire_btn').style.display = 'block';
                    }
                } else {
                    document.getElementById('doom_status_panel').style.display = 'none';
                }
            }).catch(() => {})
            .finally(() => { isPolling = false; });
        }
        
        function enableDoomCSS(en) {
            if (en) {
                document.body.classList.add('doom-mode');
                document.getElementById('normal_view').style.display = 'none';
                document.getElementById('doom_controls').style.display = 'block';
                document.getElementById('title_text').innerText = 'DOOM!';
            } else {
                document.body.classList.remove('doom-mode');
                document.getElementById('normal_view').style.display = 'block';
                document.getElementById('doom_controls').style.display = 'none';
                document.getElementById('title_text').innerText = 'Parkscheibe';
            }
        }
        
        let localDoomMode = false;
        let lastDoomActionTs = 0;
        let lastDoomAction = "";
        let doomActionInterval = null;
        let isSendingDoomAction = false;
        
        function doomAction(act, ev) {
            if (ev) {
                ev.preventDefault();
            }
            if (isSendingDoomAction) return;
            
            const nowTs = Date.now();
            if (act === lastDoomAction && (nowTs - lastDoomActionTs) < 160) {
                return; // Schutz gegen Doppelausloesung (Touch/Klick)
            }
            lastDoomAction = act;
            lastDoomActionTs = nowTs;

            isSendingDoomAction = true;
            fetch('/doom_action', { method: 'POST', body: act })
                .then(r => {
                    isSendingDoomAction = false;
                    if (r.ok) {
                        pollStatus();
                    }
                })
                .catch(() => {
                    isSendingDoomAction = false;
                });
        }

        function startDoomAction(act, ev) {
            if (ev) ev.preventDefault();
            doomAction(act, null);
            if (doomActionInterval) clearInterval(doomActionInterval);
            doomActionInterval = setInterval(() => {
                // Nur aufrufen, wenn wir nicht gerade schon senden
                if (!isSendingDoomAction) {
                    doomAction(act, null);
                }
            }, 400); // 400ms Intervall fuer gehaltene Tasten
        }

        function stopDoomAction(ev) {
            if (ev) ev.preventDefault();
            if (doomActionInterval) {
                clearInterval(doomActionInterval);
                doomActionInterval = null;
            }
        }
        
        let doomCode = "";
        function tryDoom(char, ev) {
            if (ev) {
                ev.preventDefault();
                ev.stopPropagation();
            }
            doomCode += char;
            if (doomCode.length > 20) doomCode = doomCode.slice(-20);
            if (doomCode.slice(-4) === "doom") {
                doomAction('enter');
                doomCode = "";
            }
        }

        setInterval(pollStatus, 1000);
        window.onload = () => {
            syncTime(false); // Hintergrund-Synchronisation, Demo-Status beibehalten
            pollStatus();
        };
    </script>
</body>
</html>"""


def handle_request(conn, state):
    try:
        data = conn.recv(1024)
        if not data:
            conn.close()
            return

        hdr_end = data.find(b'\r\n\r\n')
        if hdr_end == -1:
            conn.close()
            return

        header = data[:hdr_end].decode('utf-8')
        body = data[hdr_end + 4:]
        method_line = header.split('\r\n')[0]
        if LOG_HTTP_REQUESTS:
            protokoll.debug("HTTP", "REQ: %s", method_line)

        # OPTIONS
        if 'OPTIONS' in method_line:
            conn.send(_R204)
            conn.close()
            return

        # GET /
        if 'GET / ' in method_line or 'GET /index' in method_line:
            html = _html_page(state)
            conn.send(b"HTTP/1.1 200 OK\r\nContent-Type: text/html\r\nConnection: close\r\n\r\n")
            # Gestueckeltes Senden - MicroPython send() kann grosse Payloads abschneiden
            buf = html.encode('utf-8')
            mv = memoryview(buf)
            sent = 0
            while sent < len(buf):
                n = conn.send(mv[sent:])
                if n is None:
                    break
                sent += n
            conn.close()
            return

        # GET /status (JSON fuer Live-Aktualisierung)
        if 'GET /status' in method_line:
            import ujson
            import machine
            now = machine.RTC().datetime()
            status_dict = {
                 'h': state.get('disp_h', 0), 'm': state.get('disp_m', 0),
                 'curr_h': now[4], 'curr_m': now[5], 'curr_s': now[6],
                 'demo_mode': state.get('demo_mode', 0), 'synced': state.get('synced', False),
                 'doom_mode': state.get('doom_mode', False),
                 'simulated': state.get('simulated', False)
            }
            if state.get('doom_mode', False) and 'doom_instance' in state:
                di = state['doom_instance']
                import doom_spiel
                cdir = di._dir_cardinal()
                status_dict['doom_hp'] = di.hp
                status_dict['doom_kills'] = di.kills
                status_dict['doom_dir'] = doom_spiel._DIR_NAME[cdir]
                status_dict['doom_msg'] = di.msg
                status_dict['doom_won'] = di.won
                status_dict['doom_dead'] = di.dead

            j = ujson.dumps(status_dict)
            conn.send(b"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nAccess-Control-Allow-Origin: *\r\nConnection: close\r\n\r\n")
            conn.send(j.encode('utf-8'))
            conn.close()
            return

        # Favicon und Icons (verhindert unnoetige Redirects)
        if 'favicon.ico' in method_line or 'apple-touch-icon' in method_line:
            conn.send(b"HTTP/1.1 200 OK\r\nContent-Type: image/svg+xml\r\nCache-Control: public, max-age=31536000\r\nConnection: close\r\n\r\n")
            conn.send(_FAVICON_SVG)
            conn.close()
            return

        # Android Captive-Portal Pruefung → Redirect loest Portal-Popup aus
        if 'GET /generate_204' in method_line or 'GET /gen_204' in method_line:
            conn.send(_R302)
            conn.close()
            return
        # iOS Captive-Portal Pruefung → Redirect
        if 'GET /hotspot-detect' in method_line or 'GET /library/test' in method_line:
            conn.send(_R302)
            conn.close()
            return
        # Windows NCSI-Pruefung
        if 'GET /connecttest' in method_line or 'GET /ncsi' in method_line:
            conn.send(b"HTTP/1.1 200 OK\r\nConnection: close\r\n\r\nMicrosoft NCSI")
            conn.close()
            return
            
        # Wenn ueber die Domain aufgerufen, normale Pfade freigeben
        if header.find('Host: ' + WIFI_DOMAIN) != -1 or header.find('host: ' + WIFI_DOMAIN) != -1:
            if 'GET ' in method_line:
                # Redirect alles andere (wie /apple-touch-icon.png Rueckfall) auf Root
                conn.send(_R302)
                conn.close()
                return

        # Alle anderen unbekannten GETs -> Redirect zur Konfig-Seite (Captive-Portal-Falle)
        if 'GET ' in method_line:
            conn.send(_R302)
            conn.close()
            return

        # POST /sync
        if 'POST /sync' in method_line:
            try:
                import machine
                # Format von JS: HH:MM:SS:DD:MM:YYYY:WD:SIM_FLAG
                parts = body.decode('utf-8').strip().split(':')
                h, m, s, d, mo, y, wd = map(int, parts[:7])
                is_simulated = (parts[7] == '1') if len(parts) > 7 else False
                
                rtc = machine.RTC()
                # RTC datetime Parameter: (Jahr, Monat, Tag, Wochentag, Stunden, Minuten, Sekunden, Subsekunden)
                rtc.datetime((y, mo, d, wd, h, m, s, 0))
                
                state['synced'] = True
                state['simulated'] = is_simulated
                state['force_update'] = True
                protokoll.info("HTTP", "SYNC gesetzt: %04d-%02d-%02d %02d:%02d:%02d wd=%d", y, mo, d, h, m, s, wd)
                conn.send(_R200)
            except Exception as e:
                protokoll.exception("HTTP", "SYNC Fehler", e)
                conn.send(_R400)
            conn.close()
            return

        # POST /demo_time (MUSS vor /demo stehen wegen Teilstring-Uebereinstimmung!)
        if 'POST /demo_time' in method_line:
            try:
                h, m = map(int, body.decode('utf-8').strip().split(':'))
                state['demo_manual_h'] = h
                state['demo_manual_m'] = m
                if state.get('demo_mode', 0) == 2:
                    state['force_update'] = True
                protokoll.info("HTTP", "Demo-Zeit gesetzt: %02d:%02d", h, m)
            except:
                protokoll.warn("HTTP", "Demo-Zeit ungueltig: %s", body)
                pass
            conn.send(_R200)
            conn.close()
            return

        # POST /demo
        if 'POST /demo' in method_line:
            val = body.decode('utf-8').strip()
            try:
                new_mode = int(val)
                # Resete den automatischen Demo-Verlauf wenn wir auf Automatik wechseln,
                # damit er bei der akutell angezeigten Zeit anfaengt.
                if new_mode == 1 and state.get('demo_mode', 0) != 1:
                    state['demo_reset'] = True
                state['demo_mode'] = new_mode
                state['force_update'] = True
                protokoll.info("HTTP", "Demo-Modus gesetzt: %s", new_mode)
            except ValueError:
                protokoll.warn("HTTP", "Demo-Modus ungueltig: %s", val)
                pass
            conn.send(_R200)
            conn.close()
            return

        # POST /mode
        if 'POST /mode' in method_line:
            val = body.decode('utf-8').strip()
            try:
                state['update_mode'] = int(val)
                state['force_update'] = True
                protokoll.info("HTTP", "Update-Modus gesetzt: %s", state['update_mode'])
            except ValueError:
                protokoll.warn("HTTP", "Update-Modus ungueltig: %s", val)
                pass
            conn.send(_R200)
            conn.close()
            return

        # POST /doom_action
        if 'POST /doom_action' in method_line:
            action = body.decode('utf-8').strip()
            if action == 'enter':
                state['doom_mode'] = True
                state['doom_action'] = None
                state['force_update'] = True
                protokoll.info("HTTP", "DOOM enter")
            elif action == 'exit':
                state['doom_mode'] = False
                state['doom_action'] = None
                state['force_update'] = True
                protokoll.info("HTTP", "DOOM exit")
            else:
                # Nur im DOOM-Modus steuern; verhindert veraltete Eingaben
                if state.get('doom_mode', False):
                    state['doom_action'] = action
                    protokoll.debug("HTTP", "DOOM action: %s", action)
            conn.send(_R200)
            conn.close()
            return

        conn.send(_R200)
        conn.close()
    except OSError as e:
        if getattr(e, "errno", None) == 104 or "104" in str(e):
            # ECONNRESET: Client hat Verbindung abrupt geschlossen (typisch fuer Smartphones bei Captive-Portal-Pruefungen)
            protokoll.debug("HTTP", "ECONNRESET (104)")
        else:
            protokoll.exception("HTTP", "Request-Handler Fehler (OSError)", e)
        try:
            conn.close()
        except:
            pass
    except Exception as e:
        protokoll.exception("HTTP", "Request-Handler Fehler", e)
        try:
            conn.close()
        except:
            pass


_DNS_IP_BYTES = bytes(tuple(map(int, WIFI_IP.split('.'))))
WIFI_DOMAIN = _cfg("WIFI_DOMAIN", "parkscheibe.control")

def _dns_response(data, ip=_DNS_IP_BYTES):
    """Minimale DNS-Antwort: alle Anfragen -> 192.168.4.1 (Captive-Portal & benutzerdefinierte Domain)"""
    try:
        if len(data) < 12:
            return None
        # Kopfzeile: ID + Flags(Antwort) + Zaehler
        r = data[:2] + b'\x81\x80' + data[4:6] + b'\x00\x01\x00\x00\x00\x00'
        # Frageabschnitt kopieren
        p = 12
        while p < len(data) and data[p]:
            p += data[p] + 1
        p += 5  # Null + QTYPE(2) + QCLASS(2)
        if p > len(data):
            return None
        r += data[12:p]
        # Antwort: Zeiger + A + IN + TTL(60s) + 4 Bytes IP
        r += b'\xc0\x0c\x00\x01\x00\x01\x00\x00\x00\x3c\x00\x04' + ip
        return r
    except Exception as e:
        protokoll.exception("DNS", "DNS-Response Fehler", e)
        return None


def run_server(state, epd, check_callback=None, port=HTTP_PORT):
    """Nicht-blockierender Server-Loop mit DNS Captive-Portal."""
    # HTTP-Server
    addr = socket.getaddrinfo('0.0.0.0', port)[0][-1]
    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(addr)
    s.listen(5)

    # DNS-Server (Captive-Portal)
    dns = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    dns.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    dns.bind(('0.0.0.0', 53))
    dns.settimeout(0)

    from machine import WDT
    wdt = WDT(timeout=WDT_TIMEOUT_MS)
    epd.wdt = wdt

    s.settimeout(HTTP_ACCEPT_TIMEOUT_S)
    protokoll.info("HTTP", "Server gestartet: http://%s:%s", WIFI_IP, port)
    protokoll.info("DNS", "Captive DNS aktiv auf 0.0.0.0:53 -> %s", WIFI_IP)

    while True:
        wdt.feed()

        # 1. DNS-Anfragen beantworten (nicht-blockierend)
        try:
            ddata, daddr = dns.recvfrom(256)
            resp = _dns_response(ddata)
            if resp:
                dns.sendto(resp, daddr)
        except:
            pass

        # 2. HTTP-Anfragen verarbeiten (vor dem Rendern!)
        try:
            conn, addr = s.accept()
            conn.settimeout(HTTP_CONN_TIMEOUT_S)
            handle_request(conn, state)
        except OSError:
            pass

        # 3. Render-/Aktualisierungs-Rueckruf
        if check_callback:
            check_callback(epd)

        gc.collect()
