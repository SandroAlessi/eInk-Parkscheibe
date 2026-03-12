"""Generiert Ziffern- und Streifen-Bitmaps fuer die Parkscheibe.
Laeuft auf dem Desktop-PC. Erzeugt dial_assets.py fuer den Pico.
Voraussetzung: pip install Pillow

Erwartet im Numbers/-Ordner:
  - 0_large.png..9_large.png  (grosse Ziffern, aufrecht, schwarz auf weiss)
  - 0_small.png..9_small.png  (kleine Ziffern, aufrecht, schwarz auf weiss)
  - OhneZahlenVoll.png        (Strichmarken fuer volle Stunden)
  - OhneZahlenHalb.png        (Strichmarken fuer halbe Stunden)
"""
from PIL import Image, ImageDraw, ImageFont
import os

# Projektverzeichnis (eine Ebene ueber .vscode/)
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NUMBERS_DIR = os.path.join(PROJECT_DIR, "Numbers")

# Fallback-Schriftgroessen
FONT_LARGE = 72
FONT_SMALL = 36
FONT_PATHS = [
    "C:/Windows/Fonts/ariblk.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
    "C:/Windows/Fonts/impact.ttf",
]


def find_font():
    for p in FONT_PATHS:
        if os.path.exists(p):
            return p
    raise FileNotFoundError("Keine passende Schrift gefunden!")


def render_digit(digit, font):
    """Rendert eine Ziffer als 1-Bit Bild (Fallback ohne PNGs)."""
    tmp_img = Image.new('L', (1, 1), 255)
    bbox = ImageDraw.Draw(tmp_img).textbbox((0, 0), str(digit), font=font)
    tw, th = bbox[2] - bbox[0] + 20, bbox[3] - bbox[1] + 20
    img = Image.new('L', (tw, th), 255)
    ImageDraw.Draw(img).text((10 - bbox[0], 10 - bbox[1]), str(digit), fill=0, font=font)
    img = img.point(lambda p: 0 if p < 128 else 255, '1')
    box = img.getbbox()
    return img.crop(box) if box else img


def load_png(path):
    """Laedt ein PNG und konvertiert zu 1-Bit mit engem Zuschnitt."""
    img = Image.open(path).convert('L')
    img = img.point(lambda p: 0 if p < 128 else 255, '1')
    box = img.getbbox()
    return img.crop(box) if box else img


def image_to_mono_hlsb(img):
    """Konvertiert 1-Bit PIL-Bild in MicroPython MONO_HLSB bytes.
    Bit=0 -> schwarz, Bit=1 -> weiss (transparent bei blit key=1).
    """
    w, h = img.size
    px = img.load()
    bpr = (w + 7) // 8
    data = bytearray(b'\xff' * (bpr * h))
    for y in range(h):
        for x in range(w):
            if px[x, y] == 0:
                data[y * bpr + x // 8] &= ~(1 << (7 - x % 8))
    return bytes(data)


def generate():
    large, small = {}, {}

    # Ziffern laden
    has_pngs = os.path.exists(os.path.join(NUMBERS_DIR, "0_large.png"))
    if has_pngs:
        print(f"Verwende PNGs aus: {NUMBERS_DIR}")
        for d in range(10):
            img = load_png(os.path.join(NUMBERS_DIR, f"{d}_large.png"))
            large[d] = (img.width, img.height, image_to_mono_hlsb(img))
            img = load_png(os.path.join(NUMBERS_DIR, f"{d}_small.png"))
            small[d] = (img.width, img.height, image_to_mono_hlsb(img))
    else:
        font_path = find_font()
        print(f"Keine PNGs, verwende Schrift: {font_path}")
        fl = ImageFont.truetype(font_path, FONT_LARGE)
        fs = ImageFont.truetype(font_path, FONT_SMALL)
        for d in range(10):
            img = render_digit(d, fl)
            large[d] = (img.width, img.height, image_to_mono_hlsb(img))
            img = render_digit(d, fs)
            small[d] = (img.width, img.height, image_to_mono_hlsb(img))

    # Streifen laden
    stripes_full = stripes_half = None
    voll_path = os.path.join(NUMBERS_DIR, "OhneZahlenVoll.png")
    halb_path = os.path.join(NUMBERS_DIR, "OhneZahlenHalb.png")
    if os.path.exists(voll_path) and os.path.exists(halb_path):
        print("Lade Strichmarken-Bitmaps...")
        img_v = load_png(voll_path)
        stripes_full = (img_v.width, img_v.height, image_to_mono_hlsb(img_v))
        img_h = load_png(halb_path)
        stripes_half = (img_h.width, img_h.height, image_to_mono_hlsb(img_h))
        print(f"  Voll: {img_v.width}x{img_v.height} = {len(stripes_full[2])} Bytes")
        print(f"  Halb: {img_h.width}x{img_h.height} = {len(stripes_half[2])} Bytes")
    else:
        print("WARNUNG: OhneZahlenVoll/Halb.png nicht gefunden!")

    # Ausgabedatei ins Projektverzeichnis schreiben
    out = os.path.join(PROJECT_DIR, "dial_assets.py")
    with open(out, "w", encoding="utf-8") as f:
        f.write("# Auto-generierte Assets fuer die Parkscheibe\n")
        f.write("# NICHT MANUELL BEARBEITEN - generate_dial_assets.py ausfuehren\n\n")

        # Streifen
        if stripes_full and stripes_half:
            w, h, data = stripes_full
            f.write(f"# Strichmarken volle Stunden: {w}x{h}px\n")
            f.write(f"STRIPES_FULL = ({w}, {h}, {repr(data)})\n\n")
            w, h, data = stripes_half
            f.write(f"# Strichmarken halbe Stunden: {w}x{h}px\n")
            f.write(f"STRIPES_HALF = ({w}, {h}, {repr(data)})\n\n")
        else:
            f.write("STRIPES_FULL = None\nSTRIPES_HALF = None\n\n")

        # Grosse Ziffern
        f.write("# Grosse Ziffern 0-9: (Breite, Hoehe, MONO_HLSB-Daten)\n")
        f.write("LARGE = {\n")
        for d in range(10):
            w, h, data = large[d]
            f.write(f"    {d}: ({w}, {h}, {repr(data)}),\n")
        f.write("}\n\n")

        # Kleine Ziffern
        f.write("# Kleine Ziffern 0-9: (Breite, Hoehe, MONO_HLSB-Daten)\n")
        f.write("SMALL = {\n")
        for d in range(10):
            w, h, data = small[d]
            f.write(f"    {d}: ({w}, {h}, {repr(data)}),\n")
        f.write("}\n")

    total_digits = sum(len(large[d][2]) + len(small[d][2]) for d in range(10))
    total_stripes = (len(stripes_full[2]) + len(stripes_half[2])) if stripes_full else 0
    print(f"\nErzeugt: {out}")
    print(f"Ziffern: {total_digits} Bytes")
    print(f"Streifen: {total_stripes} Bytes")
    print(f"Gesamt: {total_digits + total_stripes} Bytes")


if __name__ == "__main__":
    generate()
