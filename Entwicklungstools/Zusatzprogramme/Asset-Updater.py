import os
from PIL import Image

def image_to_hlsb(img_path, threshold=200):
    img = Image.open(img_path).convert("RGBA")
    w, h = img.size
    bpr = (w + 7) // 8
    data = bytearray(bpr * h)
    for y in range(h):
        for x in range(w):
            r, g, b, a = img.getpixel((x, y))
            # Wenn transparent oder hell -> Weiss (Bit=1), sonst Schwarz (Bit=0).
            # Wir machen den Threshold sehr hoch, damit nur wirklich schwarze Pixel schwarz werden,
            # um die grauen Punkte an den Raendern zu vermeiden.
            if a < 128:
                bit = 1
            else:
                gray = (r + g + b) // 3
                bit = 1 if gray > threshold else 0
                
            if bit:
                idx = y * bpr + (x // 8)
                data[idx] |= (1 << (7 - (x % 8)))
    return w, h, bytes(data)

def main(threshold=50):
    import dial_assets
    
    new_full = {}
    for i in range(1, 13):
        w, h, data = image_to_hlsb(f"Numbers/{i}_full.png", threshold=threshold)
        new_full[i] = (w, h, data)
        
    print("FULL (1-12) generiert.")
    
    # Read the original stripes so we don't lose them
    stripes_full = dial_assets.STRIPES_FULL
    stripes_half = dial_assets.STRIPES_HALF
    
    with open("dial_assets.py", "w") as f:
        f.write("# Auto-generierte Assets fuer die Parkscheibe\n")
        f.write("# NICHT MANUELL BEARBEITEN - generiert durch update_assets.py\n\n")
        
        f.write("STRIPES_FULL = " + repr(stripes_full) + "\n\n")
        f.write("STRIPES_HALF = " + repr(stripes_half) + "\n\n")
        
        f.write("FULL = {\n")
        for k, v in new_full.items():
            f.write(f"    {k}: {repr(v)},\n")
        f.write("}\n")
        
    print("Fertig. dial_assets.py gespeichert.")

if __name__ == "__main__":
    main(threshold=50)
