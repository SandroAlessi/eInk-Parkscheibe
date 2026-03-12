# 🅿️ Parkscheibe

**Digitale Parkscheibe mit e-Ink Display — StVO-konform, WLAN-gesteuert, mit verstecktem DOOM-Easteregg.**

<p align="center">
  <img src="Medien (nur für GitHub)/Parkscheibe.gif" alt="Parkscheibe in Aktion" width="600">
</p>

Ein MicroPython-Projekt für den Raspberry Pi Pico W (und Pico 2 W), das eine echte Parkscheibe mit 3,7" e-Ink Display simuliert. Die Ankunftszeit wird automatisch über das Smartphone synchronisiert — ganz ohne Knöpfe oder manuelle Einstellung.

---

## 📑 Inhaltsverzeichnis

- [Funktionen](#-funktionen)
- [Hardware-Voraussetzungen](#-hardware-voraussetzungen)
- [Software-Voraussetzungen](#-software-voraussetzungen)
- [Installation](#-installation)
- [Konfiguration](#%EF%B8%8F-konfiguration)
- [Benutzung](#-benutzung)
- [Dateistruktur](#-dateistruktur)
- [StVO-Konformität](#-stvo-konformität)
- [DOOM Easteregg](#-doom-easteregg)
- [Lizenz](#-lizenz)

---

## ✨ Funktionen

| Funktion | Beschreibung |
|---|---|
| **Zeitsynchronisation** | Automatische Zeitübernahme vom Smartphone per WLAN |
| **StVO-konform** | Aufrundung auf die nächste halbe Stunde gemäß § 13 Abs. 2 StVO |
| **e-Ink Display** | Energiesparendes 3,7" Schwarz/Weiß-Display — lesbar bei Sonnenlicht |
| **WLAN Access-Point** | Eigener Hotspot „Parkscheibe" — kein Router nötig |
| **Captive Portal** | Web-Interface öffnet sich automatisch beim Verbinden |
| **Benutzerdefinierte Domain** | Erreichbar unter `parkscheibe.control` |
| **Demo-Modus** | Automatischer oder manueller Testbetrieb |
| **Sommer-/Winterzeit** | Automatische Umstellung (MEZ ↔ MESZ) |
| **Täglicher Display-Refresh** | Verhindert Geisterbilder (Ghost-Images) um 03:33 Uhr |
| **Watchdog Timer** | Automatischer Neustart bei Systemhänger |
| **Konfigurierbarer Logging** | Schaltbares Debug-Logging mit verschiedenen Stufen |
| **DOOM Easteregg** | Verstecktes Spiel im Doom-Stil auf dem e-Ink Display 🎮 |

---

## 🔧 Hardware-Voraussetzungen

### Benötigte Komponenten

| Komponente | Modell | Hinweis |
|---|---|---|
| **Mikrocontroller** | Raspberry Pi Pico WH **oder** Pico 2 WH | WLAN-fähig (mit vorgelöteten Headern getestet) |
| **Display** | [Waveshare 3.7" e-Paper für Pico](https://www.waveshare.com/pico-epaper-3.7.htm) (480×280 px) | Schwarz/Weiß, 4 Grayscale |
| **Parkscheiben-Gehäuse** | [Elasto Parkscheibe Profi](https://www.elasto.de/Parkscheibe-Profi/04248003-00000) | Als Basis-Gehäuse für den Einbau der Elektronik verwendet |
| **Stromversorgung** | USB-C / Powerbank | 5V, mind. 500mA |

<p align="center">
  <img src="Medien (nur für GitHub)/Rückseite.jpg" alt="Rückseite der Parkscheibe mit Hardware" width="600">
</p>

### Pinbelegung

Das Display wird über SPI angeschlossen. Die Standardpins sind:

| Signal | GPIO-Pin | Beschreibung |
|---|---|---|
| `CLK` | GPIO 10 | SPI-Takt (PIO) |
| `DIN` | GPIO 11 | SPI-Daten (PIO) |
| `CS` | GPIO 9 | Chip-Select |
| `DC` | GPIO 8 | Daten/Befehl |
| `RST` | GPIO 12 | Hardware-Reset |
| `BUSY` | GPIO 13 | Busy-Signal |

> **Hinweis:** Die SPI-Kommunikation erfolgt über PIO (Programmable I/O), nicht über den Hardware-SPI-Bus. Das vermeidet Konflikte mit dem WLAN-Chip (CYW43).

---

## 💾 Software-Voraussetzungen

- **MicroPython** v1.19.1 oder neuer (Getestet mit v1.26.1 und v1.27.0)
  - Pico W: [Download `RPI_PICO_W-*.uf2`](https://micropython.org/download/RPI_PICO_W/)
  - Pico 2 W: [Download `RPI_PICO2_W-*.uf2`](https://micropython.org/download/RPI_PICO2_W/)
- **Keine weiteren Bibliotheken** — alles ist im Projekt enthalten

### MicroPython Firmware installieren

1. Den **BOOTSEL**-Knopf am Pico gedrückt halten
2. Pico per USB an den Computer anschließen (Knopf weiterhin gedrückt)
3. Ein USB-Laufwerk (`RPI-RP2`) erscheint
4. Die passende `.uf2`-Datei auf das Laufwerk kopieren
5. Der Pico startet automatisch mit MicroPython neu

---

## 📦 Installation

### 1. Repository klonen

```bash
git clone https://github.com/SandroAlessi/eInk-Parkscheibe.git
cd eInk-Parkscheibe
```

### 2. Dateien auf den Pico übertragen

Alle `.py`-Dateien müssen in das Stammverzeichnis des Pico kopiert werden. Dafür gibt es mehrere Möglichkeiten:

#### Option A: Thonny IDE (empfohlen für Einsteiger)

1. [Thonny](https://thonny.org/) installieren und öffnen
2. Unter **Extras → Optionen → Interpreter** den MicroPython-Interpreter auswählen
3. Den Pico per USB anschließen
4. Alle `.py`-Dateien per Rechtsklick → **„Auf den MicroPython-Gerät hochladen"** übertragen

#### Option B: mpremote (Kommandozeile)

```bash
pip install mpremote

mpremote cp konfiguration.py :
mpremote cp main.py :
mpremote cp webserver.py :
mpremote cp netzwerk_verwaltung.py :
mpremote cp zifferblatt_renderer.py :
mpremote cp zifferblatt_grafiken.py :
mpremote cp doom_spiel.py :
mpremote cp treiber.py :
mpremote cp protokoll.py :
```

#### Option C: VS Code mit MicroPico

1. Die Extension **MicroPico** in VS Code installieren
2. Projekt öffnen, Pico verbinden
3. Alle Dateien über die Seitenleiste hochladen

### 3. Pico neustarten

Nach dem Hochladen aller Dateien den Pico kurz vom USB trennen und wieder anschließen. Das Programm startet automatisch.

---

## ⚙️ Konfiguration

Alle Einstellungen befinden sich zentral in **`konfiguration.py`**. Die Datei ist in zwei Bereiche unterteilt:

### Benutzerbereich (typische Anpassungen)

```python
# WLAN-Einstellungen
WIFI_SSID = "Parkscheibe"        # Name des WLAN-Netzwerks
WIFI_PASSWORD = "Freiparken"     # WLAN-Passwort
WIFI_IP = "192.168.4.1"          # IP-Adresse des Pico
WIFI_DOMAIN = "parkscheibe.control"  # Benutzerdefinierte Domain

# Display
DISPLAY_WIDTH = 480              # Display-Breite in Pixeln
DISPLAY_HEIGHT = 280             # Display-Höhe in Pixeln
DISPLAY_ROTATION = 90            # Drehung: 0, 90, 180, 270

# Allgemeines Verhalten
DEMO_STEP_INTERVAL_MS = 5000     # Demo-Modus Intervall (ms)
FULL_REFRESH_HOUR = 3            # Stunde für täglichen Full-Refresh
FULL_REFRESH_MINUTE = 33         # Minute für täglichen Full-Refresh

# Logging
LOG_ENABLED = False              # True = An, False = Aus
LOG_LEVEL = "DEBUG"              # DEBUG, INFO, WARN, ERROR
```

### Expertenbereich (interne Feineinstellungen)

Der Expertenbereich enthält technische Parameter wie:
- HTTP-Server Timeouts
- Watchdog-Timer Konfiguration
- Display-Rendering Positionen
- DOOM-Spielparameter (Kartenaufbau, CPU-Frequenz, Viewport)

> **Tipp:** Für den normalen Betrieb ist die einzige zwingende Anpassung, die in der Konfiguration vorgenommen werden muss, die korrekte Einstellung der **Position und Ausdehnung der Anzeige** für deine spezifische Hardware-Display-Position.

---

## 🚀 Benutzung

### Schritt 1: Mit dem WLAN verbinden

1. Parkscheibe einschalten (USB anschließen)
2. Auf dem Smartphone die WLAN-Einstellungen öffnen
3. Mit dem Netzwerk **„Parkscheibe"** verbinden
4. Passwort: `Freiparken`

### Schritt 2: Web-Interface öffnen

Das Web-Interface sollte sich als **Captive Portal** automatisch öffnen. Falls nicht:
- Im Browser `http://parkscheibe.control` aufrufen
- Alternativ: `http://192.168.4.1`

### Schritt 3: Zeit synchronisieren

Auf **„Zeit synchronisieren"** tippen. Die aktuelle Uhrzeit des Smartphones wird an den Pico übertragen. Die Parkscheibe zeigt danach automatisch die korrekte Ankunftszeit gemäß StVO an.

<p align="center">
  <img src="Medien (nur für GitHub)/Normal_Web.jpg" alt="Web-Interface: Zeit synchronisieren" width="400">
</p>

### Betriebsmodi

#### 🅿️ Parkscheiben-Modus (Standard)
Nach der Synchronisation zeigt das Display die korrekte Ankunftszeit:
- Die angezeigte Zeit wird auf die nächste halbe Stunde aufgerundet
- Automatische Updates bei `:00` und `:30` (konfigurierbar)

#### 🔄 Demo-Modus (Automatisch)
- Wechselt ca. alle 5-10 Sekunden die angezeigte Uhrzeit im 30-Minuten-Takt
- Ideal zum Testen und Vorführen

<p align="center">
  <img src="Medien (nur für GitHub)/Demo_Web.jpg" alt="Web-Interface: Demo-Modus" width="400">
</p>

#### ✏️ Demo-Modus (Manuell)
- Beliebige Uhrzeit per Schieberegler einstellen
- RTC-Überschreibung für Zeitsimulation (z.B. 03:33 Uhr testen)

#### 🔀 Wechsel-Modus
Konfigurierbar über das Web-Interface:
- **Alle 30 Minuten** — Wechsel bei `:00` und `:30` (Standard)
- **Alle 60 Minuten** — Wechsel nur bei `:00`
- **Aus** — Keine automatischen Wechsel

---

## 🛠️ Entwicklungstools

Neben dem eigentlichen Quellcode für die Parkscheibe enthält das Repository einen Ordner **`Entwicklungstools/`**. Dieser beinhaltet nützliche Helfer-Skripte und Quelldateien für Entwickler, die eigene Grafiken oder Layouts erstellen möchten.

### Ordnerstruktur der Werkzeuge

- **`Zusatzprogramme/`**:
  - `Asset-Updater.py`: Python-Skript, um generierte Bilddaten (z. B. Arrays) automatisch in die entsprechenden `.py`-Quelldateien der Parkscheibe zu injizieren.
  - `Bildübertragung.html`: Ein kleines Web-Tool (im Browser lauffähig), mit dem man Bilder (wie das Doom-Logo) hochladen und in das von MicroPython benötigte 1-Bit-Array-Format (`.txt`) konvertieren kann.
  - `HUD_Layout-Anpassung.py`: Hilfsskript zur perfekten Positionierung und Berechnung der UI-Elemente im DOOM-Easteregg.
  - `Scheibenasset_Generator.py`: Generiert und berechnet die Grafik-Arrays für das Parkscheiben-Zifferblatt.
- **`Bildmaterial/`**: 
  - `Parkscheibe.psd` & `Anzeige.psb`: Offene Photoshop-Projektdateien. Hier können eigene Zifferblätter oder Display-Layouts grafisch entworfen werden.
  - `Parkdoom-Logo.png` / `.txt`: Originales Bildmaterial und fertig konvertiertes Array-Format des DOOM-Ladebildschirms.

> **Hinweis:** Keine dieser Dateien muss auf den Pico geladen werden. Sie dienen ausschließlich der Entwicklung am PC.

---

## 📁 Dateistruktur

```
parkscheibe/
├── konfiguration.py          # Zentrale Konfigurationsdatei
├── main.py                   # Hauptprogramm und Steuerlogik
├── webserver.py              # HTTP-Server, DNS und Web-Interface
├── netzwerk_verwaltung.py    # WLAN Access-Point Verwaltung
├── zifferblatt_renderer.py   # Parkscheiben-Zifferblatt Renderer
├── zifferblatt_grafiken.py   # Bitmap-Daten der Ziffern und Striche
├── doom_spiel.py             # DOOM Easteregg (Raycaster-Engine)
├── treiber.py                # e-Ink Display Treiber (PIO-basiert)
├── protokoll.py              # Konfigurierbares Logging-Modul
├── .gitignore                # Git-Ausschlussliste
├── LICENSE                   # MIT-Lizenz
└── README.md                 # Diese Datei
```

### Modulbeschreibungen

| Modul | Beschreibung |
|---|---|
| `konfiguration.py` | Alle konfigurierbaren Parameter an einem Ort — WLAN, Display, Timing, DOOM |
| `main.py` | Initialisiert Hardware, verwaltet Zustand, steuert Rendering-Loop und Moduswechsel |
| `webserver.py` | Eingebetteter HTTP-Server mit vollständigem Web-Interface (HTML/CSS/JS), DNS-Server für Captive-Portal |
| `netzwerk_verwaltung.py` | Startet den WLAN Access-Point mit statischer IP-Konfiguration |
| `zifferblatt_renderer.py` | Rendert das Parkscheiben-Zifferblatt mit rotierten Zahlen-Bitmaps per Festkomma-Mathematik |
| `zifferblatt_grafiken.py` | Enthält vorberechnete Bitmap-Daten für alle Ziffern (1–12) und Strichmarkierungen |
| `doom_spiel.py` | Vollständige Raycaster-Engine mit Gegner-KI, Wegfindung, HUD und Minimap |
| `treiber.py` | Low-Level e-Ink Treiber mit PIO-basierter SPI-Kommunikation, Partial-Refresh Unterstützung |
| `protokoll.py` | Leichtgewichtiges Logging mit konfigurierbaren Stufen und optionaler Deaktivierung |

---

## ⚖️ StVO-Konformität

Die Parkscheibe implementiert die Rundungsregel nach **§ 13 Abs. 2 StVO**:

> *Die Ankunftszeit ist auf die nächste halbe Stunde aufzurunden, die nach der Ankunft beginnt.*

| Ankunftszeit | Angezeigte Zeit |
|---|---|
| 14:00 | 14:30 |
| 14:01 | 14:30 |
| 14:29 | 14:30 |
| 14:30 | 15:00 |
| 14:31 | 15:00 |
| 14:59 | 15:00 |

Die Implementierung befindet sich in der Funktion `get_stvo_time()` in `main.py`.

> [!WARNING]
> **WICHTIGER RECHTLICHER HINWEIS**
> Dieses Projekt ist ein rein privates **Bastel-/Hobby-Projekt** und **kein offiziell zugelassenes Gerät** für den Straßenverkehr.
> Die Parkscheibe besitzt weder eine Bauartgenehmigung nach § 22a StVZO noch eine KBA-Zulassung. Die Verwendung im Geltungsbereich der StVO geschieht ausdrücklich auf eigene Gefahr. Der Entwickler übernimmt keinerlei Haftung für Verwarnungsgelder, Abschleppkosten oder sonstige Schäden.

---

## 🎮 DOOM Easteregg

Die Parkscheibe enthält ein verstecktes DOOM-ähnliches Spiel, das direkt auf dem e-Ink Display läuft!

<p align="center">
  <img src="Medien (nur für GitHub)/Doom.jpg" alt="DOOM Easteregg auf dem e-Ink Display" width="600">
</p>

<p align="center">
  <img src="Medien (nur für GitHub)/Doom_Web.jpg" alt="Web-Interface: DOOM Steuerung" width="400">
</p>

### Aktivierung

Im Web-Interface den Text **„Demo-Modus"** antippen — die Buchstaben `D`, `e`, `m`, `o`, `-`, `M`, `o`, `d`, `u`, `s` sind einzeln anklickbar. Um das Spiel zu aktivieren, müssen die angetippten Buchstaben nacheinander **D-O-O-M** ergeben (welches O oder M benutzt wird, auf Groß-/Kleinschreibung wird dabei nicht geachtet, ist egal).

Bei einer Fehleingabe wird im Hintergrund automatisch zurückgesetzt; es gelten immer die zuletzt angetippten Buchstaben.

### Steuerung

| Taste | Aktion |
|---|---|
| **W** | Vorwärts |
| **S** | Rückwärts |
| **A** | Links drehen |
| **D** | Rechts drehen |
| **FEUER** | Schießen |
| **DOOM BEENDEN** | Zurück zur Parkscheibe |

### Spielziel

Finde den Ausgang (markiert mit `3` auf der Karte) und überlebe dabei die Gegner! Du hast 4 Lebenspunkte (LP) — Gegner verursachen bei Kontakt Schaden. Benutze die Schusswaffe, um Gegner zu eliminieren.

### Technische Details

- **Raycaster-Engine** mit Fixed-Point-Arithmetik
- **Wegfindung (BFS)** für Gegner-KI innerhalb von 5 Feldern Reichweite
- **Minimap** mit blinkendem Spieler-Indikator
- **Kompass-HUD** mit fließender Richtungsanzeige
- **Ladebildschirm** mit benutzerdefiniertem Logo und unregelm. Fortschrittsbalken

---

## 📄 Lizenz

Dieses Projekt sowie die dazugehörige Hardwaredokumentation werden unter den **Nutzungsbedingungen für die Software und Bauanleitung „Digitale Parkscheibe“** (unentgeltlicher Software-Überlassungsvertrag) bereitgestellt.

- **Nutzung:** Kostenfrei für private, nicht-kommerzielle Zwecke.
- **Kommerzielle Nutzung:** Ausdrücklich untersagt.
- **Haftung:** Wie besehen, auf eigene Gefahr. Keine Haftung für StVO-Verstöße.

Siehe die Datei [LICENSE](LICENSE) für den vollständigen und detaillierten Rechtstext.
