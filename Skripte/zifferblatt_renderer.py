"""Parkscheiben-Zifferblatt Renderer fuer e-Ink Display.
Alle Bitmaps werden per framebuf.blit() gezeichnet (C-Geschwindigkeit, kein Python-Loop).
Zahlen an den Aussenpositionen werden zur Laufzeit rotiert (Festkomma-Ganzzahl).
"""
import framebuf
import gc
from zifferblatt_grafiken import STRIPES_FULL, STRIPES_HALF, FULL
import konfiguration

# --- Feste Positionen (Display 480x280) ---
# (cx, cy) = Mittelpunkt der Zahl

POS_FULL_3 = konfiguration.DIAL_POS_FULL_3

POS_FULL_4 = konfiguration.DIAL_POS_FULL_4

STRIPES_Y = konfiguration.DIAL_STRIPES_Y

# Rotationswinkel pro Position (positiv = gegen Uhrzeigersinn, negativ = im Uhrzeigersinn)
ANGLES_3 = konfiguration.DIAL_ANGLES_3  # Volle Stunde: links +30, mitte 0, rechts -30
ANGLES_4 = konfiguration.DIAL_ANGLES_4  # Halbe Stunde: aussen +-45, innen +-15

# Festkomma-Trigonometrie (x1024) - kein math-Import noetig
_TRIG = konfiguration.DIAL_TRIG


def draw_ticks(display, half_hour=False):
    """Blittet Strichmarken per blit() (schnell)."""
    stripe = STRIPES_HALF if half_hour else STRIPES_FULL
    if stripe is None:
        return
    w, h, data = stripe
    fb = framebuf.FrameBuffer(bytearray(data), w, h, framebuf.MONO_HLSB)
    x_off = (konfiguration.DISPLAY_WIDTH - w) // 2 + konfiguration.DIAL_STRIPES_X_OFFSET
    display.blit(fb, x_off, STRIPES_Y, 1)


def _draw_number(display, number_1_to_12, cx, cy, angle=0):
    """Zeichnet ein Zahlenbild per blit(), optional zur Laufzeit rotiert."""
    if number_1_to_12 not in FULL:
        print("[WARN] Zahl", number_1_to_12, "nicht in FULL")
        return
    w, h, data = FULL[number_1_to_12]

    if angle == 0:
        # Schneller Pfad: direkt blitten (C-Level)
        fb = framebuf.FrameBuffer(bytearray(data), w, h, framebuf.MONO_HLSB)
        display.blit(fb, cx - w // 2, cy - h // 2, 1)
        return

    # --- Laufzeit-Rotation mit Festkomma-Ganzzahl-Arithmetik ---
    abs_a = abs(angle)
    if abs_a not in _TRIG:
        print("[WARN] Winkel", angle, "nicht unterstuetzt")
        return

    cos_fp, sin_fp = _TRIG[abs_a]
    if angle < 0:
        sin_fp = -sin_fp

    hw = w >> 1
    hh = h >> 1

    # Rotierter Begrenzungsrahmen (4 Ecken rotieren)
    c1x = (-hw * cos_fp + hh * sin_fp) >> 10
    c1y = (-hw * sin_fp - hh * cos_fp) >> 10
    c2x = ( hw * cos_fp + hh * sin_fp) >> 10
    c2y = ( hw * sin_fp - hh * cos_fp) >> 10
    c3x = ( hw * cos_fp - hh * sin_fp) >> 10
    c3y = ( hw * sin_fp + hh * cos_fp) >> 10
    c4x = (-hw * cos_fp - hh * sin_fp) >> 10
    c4y = (-hw * sin_fp + hh * cos_fp) >> 10

    min_dx = min(c1x, c2x, c3x, c4x)
    max_dx = max(c1x, c2x, c3x, c4x)
    min_dy = min(c1y, c2y, c3y, c4y)
    max_dy = max(c1y, c2y, c3y, c4y)

    rw = max_dx - min_dx + 1
    rh = max_dy - min_dy + 1

    # Temporaerer Puffer fuer rotierte Bitmap (MONO_HLSB, weiss gefuellt)
    rbpr = (rw + 7) >> 3
    rbuf = bytearray(b'\xff' * (rbpr * rh))

    # Quell-Bytes direkt lesen (schneller als framebuf.pixel)
    bpr = (w + 7) >> 3
    hw_fp = hw << 10
    hh_fp = hh << 10

    # WDT-Referenz holen (einmal, nicht in der Schleife)
    wdt = display.wdt if hasattr(display, 'wdt') else None

    # Ziel-Iteration (inverse Rotation: Ziel -> Quelle)
    for dy in range(min_dy, max_dy + 1):
        ty = dy - min_dy
        # Vorgezogene Berechnung fuer die innere Schleife
        row_sx_base = dy * sin_fp + hw_fp
        row_sy_base = dy * cos_fp + hh_fp

        # WDT alle 20 Zeilen fuettern
        if wdt and ty % 20 == 0:
            wdt.feed()

        for dx in range(min_dx, max_dx + 1):
            # Inverse Rotation: Quell-Pixel fuer dieses Ziel finden
            sx = (dx * cos_fp + row_sx_base) >> 10
            sy = (-dx * sin_fp + row_sy_base) >> 10

            if 0 <= sx < w and 0 <= sy < h:
                # Quell-Pixel lesen (MONO_HLSB: Bit7=links)
                src_bit = (data[sy * bpr + (sx >> 3)] >> (7 - (sx & 7))) & 1
                if not src_bit:  # 0 = Schwarz
                    tx = dx - min_dx
                    tidx = ty * rbpr + (tx >> 3)
                    rbuf[tidx] &= ~(1 << (7 - (tx & 7)))

    # Rotierte Bitmap per blit() auf Display (weiss = transparent)
    tfb = framebuf.FrameBuffer(rbuf, rw, rh, framebuf.MONO_HLSB)
    display.blit(tfb, cx + min_dx, cy + min_dy, 1)


def get_dial_numbers(hour_24, half_hour=False):
    """Berechnet welche Zahlen (1-12) an jeder Position stehen."""
    count = 4 if half_hour else 3
    offset = 1  # Mitte zeigt immer aktuelle Stunde
    numbers = []
    for i in range(count):
        h24 = (hour_24 - offset + i) % 24
        h12 = h24 % 12
        if h12 == 0:
            h12 = 12
        numbers.append(h12)
    return numbers


def render_dial(display, hour_24, minute=0, partial=True):
    """Rendert das Parkscheiben-Zifferblatt. Alle Bitmaps per blit()."""
    half = minute >= 30
    positions = POS_FULL_4 if half else POS_FULL_3
    angles = ANGLES_4 if half else ANGLES_3

    # Display-Modus VOR dem Rendern setzen, damit fill/blit in den richtigen Buffer schreiben
    if partial and not display._partial:
        display.partial_mode_on()
    elif not partial and display._partial:
        display.partial_mode_off()

    display.fill(display.white)
    gc.collect()

    # Strichmarken
    draw_ticks(display, half_hour=half)
    if hasattr(display, 'wdt') and display.wdt:
        display.wdt.feed()

    # Zahlen
    numbers = get_dial_numbers(hour_24, half_hour=half)

    for i, (cx, cy) in enumerate(positions):
        _draw_number(display, numbers[i], cx, cy, angle=angles[i])
        if hasattr(display, 'wdt') and display.wdt:
            display.wdt.feed()
        gc.collect()

    # Display aktualisieren (PIO Byte-fuer-Byte, kein WiFi-Konflikt)
    display.show()
