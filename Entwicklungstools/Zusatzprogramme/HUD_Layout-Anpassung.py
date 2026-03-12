import time
import sys
import select
from driver import EinkPIO as EPD_3in7
import doom_game
import config

epd = EPD_3in7(
    rotation=config.DISPLAY_ROTATION,
    use_partial_buffer=config.DISPLAY_USE_PARTIAL_BUFFER
)

print("Initializing Display...")
epd.init()
epd.partial_mode_on()

game = doom_game.DoomGame()

# Start positions based on current implementation
# Speichere die originalen/config Werte für die Abfrage mit Xa, Ya, Za
defaults = {
    'game_x': doom_game.VX,
    'game_y': doom_game.VY,
    'hp_x': doom_game.VX + 4,
    'hp_y': doom_game.VY + 4,
    'k_x': doom_game.VX + doom_game.VW - 56, # Approx width
    'k_y': doom_game.VY + 4,
    'mm_x': doom_game.VX + doom_game.VW - doom_game.MAP_W * 3 - 4,
    'mm_y': doom_game.VY + 20,
    'gun_x': doom_game.VX + doom_game.VW // 2,
    'gun_y': doom_game.VY + doom_game.VH
}
controls = defaults.copy()

object_defs = {
    '1': {'name': 'HP', 'x': 'hp_x', 'y': 'hp_y'},
    '2': {'name': 'Kills', 'x': 'k_x', 'y': 'k_y'},
    '3': {'name': 'Minimap', 'x': 'mm_x', 'y': 'mm_y'},
    '4': {'name': 'Spielbildschirm', 'x': 'game_x', 'y': 'game_y'},
    '5': {'name': 'Pistole', 'x': 'gun_x', 'y': 'gun_y'}
}
saved_flags = {'1': False, '2': False, '3': False, '4': False, '5': False}
CENTER_X = doom_game.VX + doom_game.VW // 2
CENTER_Y = doom_game.VY + doom_game.VH // 2

def render_preview():
    # Patch game methods/vars temporarily for this test
    old_vx = doom_game.VX
    old_vy = doom_game.VY
    old_vcx = doom_game.VCX if hasattr(doom_game, 'VCX') else (doom_game.VX + doom_game.VW // 2)
    
    doom_game.VX = controls['game_x']
    doom_game.VY = controls['game_y']
    doom_game.VCX = controls['game_x'] + doom_game.VW // 2
    
    # We use the game's actual render but overwrite coordinate calculation logic where possible,
    # or just draw over it for the test. We do NOT call game.tick() so it is just
    # a static screenshot of the scene.
    epd.fill(epd.white)
    
    scene_h = doom_game.VH
    hud_y = doom_game.VY + doom_game.VH
    mid_y = doom_game.VY + scene_h // 2
    epd.hline(doom_game.VX + 1, mid_y, doom_game.VW - 2, epd.black)

    game._render_walls(epd, scene_h)
    game._render_enemies(epd, scene_h)
    
    # Bounding Box für Spielbildschirm
    epd.rect(doom_game.VX, doom_game.VY, doom_game.VW, doom_game.VH, epd.black)
    
    # Render Custom Minimap Position
    mm_s = 3
    mm_x = controls['mm_x']
    mm_y = controls['mm_y']
    epd.rect(mm_x - 1, mm_y - 1, doom_game.MAP_W * mm_s + 2, doom_game.MAP_H * mm_s + 2, epd.black) # Hintergrund Minimap
    epd.rect(mm_x - 2, mm_y - 2, doom_game.MAP_W * mm_s + 4, doom_game.MAP_H * mm_s + 4, epd.black) # Bounding Box Minimap
    for my in range(doom_game.MAP_H):
        for mx in range(doom_game.MAP_W):
            c = game.map[my][mx]
            px = mm_x + mx * mm_s
            py = mm_y + my * mm_s
            if c == 1:
                epd.rect(px, py, mm_s, mm_s, epd.black, f=True)
            elif c == 2:
                epd.pixel(px + 1, py + 1, epd.black)

    # Render Custom HP Position
    epd.rect(controls['hp_x'], controls['hp_y'], 30, 24, epd.white, f=True)
    epd.rect(controls['hp_x'] - 1, controls['hp_y'] - 1, 32, 26, epd.black) # Bounding Box HP
    hx, hy = controls['hp_x'] + 4, controls['hp_y'] + 2
    H_SPRITE = [
        "  OOO OOO  ",
        " O444O111O ",
        "O4444O1111O",
        "O4444O1111O",
        "O4444O1111O",
        "OOOOOOOOOOO",
        " O333O222O ",
        "  O33O22O  ",
        "   O3O2O   ",
        "    OOO    "
    ]
    for hy_idx, row in enumerate(H_SPRITE):
        for hx_idx, char in enumerate(row):
            if char == 'O' or (char.isdigit() and int(char) <= game.hp):
                epd.rect(hx + hx_idx*2, hy + hy_idx*2, 2, 2, epd.black, f=True)

    # Render Custom Kills Position
    cdir = game._dir_cardinal()
    k_str = "K:" + str(game.kills) + " " + doom_game._DIR_NAME[cdir]
    epd.rect(controls['k_x'], controls['k_y'], len(k_str) * 8 + 4, 12, epd.white, f=True)
    epd.rect(controls['k_x'] - 1, controls['k_y'] - 1, len(k_str) * 8 + 6, 14, epd.black) # Bounding Box Kills
    epd.text(k_str, controls['k_x'] + 2, controls['k_y'] + 2, epd.black)

    if hasattr(epd, "line"):
        gun_x = controls['gun_x']
        gun_y = controls['gun_y']
        fill_c = epd.black if game.gun_flash_frames > 0 else epd.white
        for dy in range(31):
            w = (dy * 10) // 30
            epd.hline(gun_x - w, (gun_y - 30) + dy, w * 2 + 1, fill_c)
        epd.line(gun_x - 10, gun_y, gun_x, gun_y - 30, epd.black)
        epd.line(gun_x, gun_y - 30, gun_x + 10, gun_y, epd.black)
        epd.hline(gun_x - 10, gun_y, 21, epd.black)
        
        # Bounding Box Pistole
        epd.rect(gun_x - 11, gun_y - 31, 23, 33, epd.black)

    epd.show()

    # Restore variables
    doom_game.VX = old_vx
    doom_game.VY = old_vy
    doom_game.VCX = old_vcx

print("--- DOOM HUD LAYOUT TESTER ---")
print("Gib deine Befehle in die Konsole ein und drücke Enter.")

while True:
    print("\nWelches Symbol möchtest du verschieben?")
    print("1: HP")
    print("2: Kills")
    print("3: Minimap")
    print("4: Spielbildschirm")
    print("5: Pistole")
    print("E: Positionen aller Objekte ausgeben")
    
    choice = input("Deine Wahl (1/2/3/4/5/E): ").strip().upper()
    
    if choice == 'E':
        print("\n--- AKTUELLE POSITIONEN ---")
        for k, v in controls.items():
            print(f"'{k}': {v},")
        print("---------------------------")
        continue
        
    if choice in object_defs:
        obj = object_defs[choice]
        obj_name = obj['name']
        x_key = obj['x']
        y_key = obj['y']
        
        if not saved_flags[choice]:
            if choice != '4':
                controls[x_key] = CENTER_X
                controls[y_key] = CENTER_Y
            
        print(f"\n{obj_name} ausgewählt.")
        print("Rendere Vorschau...")
        render_preview()
        
        last_axis = None # Noch keine Achse vorgewählt
        
        while True:
            prompt_hint = f"oder {last_axis}" if last_axis else "oder direkt"
            action = input(f"[{obj_name}] X/Y verschieben (z.B. X150 {prompt_hint} Zahl), Z zentrieren, Xa/Ya/Za um orig. Wert zusehen, J speichern? (X/Y/Z/J): ").strip().upper()
            
            if action == 'J':
                saved_flags[choice] = True
                print(f"{obj_name} Position gespeichert!")
                break
            elif action == 'ZA':
                cx = defaults['game_x'] + doom_game.VW // 2
                print(f"Die ursprüngliche (zentrierte) X-Position für {obj_name} ist: {cx}")
            elif action == 'Z':
                controls[x_key] = controls['game_x'] + doom_game.VW // 2
                print(f"{obj_name} horizontal zum Spieleinhalt zentriert!")
                print("Du kannst das Objekt jetzt weiter mit X/Y verschieben oder mit J speichern.")
                print("Rendere neue Position...")
                render_preview()
            elif action == 'XA':
                print(f"Die ursprüngliche im Setup gespeicherte X-Position für {obj_name} ist: {defaults[x_key]}")
            elif action == 'YA':
                print(f"Die ursprüngliche im Setup gespeicherte Y-Position für {obj_name} ist: {defaults[y_key]}")
            elif action.startswith('X') or action.startswith('Y'):
                axis = action[0]
                val_str = action[1:].strip()
                last_axis = axis
                
                # Wenn nur 'X' oder 'Y' eingegeben wurde, nach der Zahl fragen
                if not val_str:
                    val_str = input(f"Neue {axis}-Positionsnummer eingeben: ").strip()
                
                try:
                    pos_val = int(val_str)
                    if axis == 'X':
                        controls[x_key] = pos_val
                    else:
                        controls[y_key] = pos_val
                    print("Rendere neue Position...")
                    render_preview()
                except ValueError:
                    print("Ungültige Eingabe, bitte eine Zahl eingeben.")
            else:
                try:
                    # Direkte Zahleneingabe
                    pos_val = int(action)
                    if last_axis is None:
                        while True:
                            ask_axis = input(f"Für welche Achse soll {pos_val} gelten? (X/Y): ").strip().upper()
                            if ask_axis in ('X', 'Y'):
                                last_axis = ask_axis
                                break
                            print("Bitte nur X oder Y eingeben.")
                            
                    if last_axis == 'X':
                        controls[x_key] = pos_val
                    else:
                        controls[y_key] = pos_val
                    print(f"Setze {last_axis} auf {pos_val}. Rendere neue Position...")
                    render_preview()
                except ValueError:
                    print(f"Ungültige Eingabe. Bitte z.B. X150, Y200, eine Zahl, Z, Xa oder J eingeben.")
    else:
        print("Ungültige Auswahl.")
