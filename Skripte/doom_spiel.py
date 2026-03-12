import utime
import gc
import math
import konfiguration
import micropython

def _cfg(name, default, *aliases):
    if hasattr(konfiguration, name):
        return getattr(konfiguration, name)
    for alias in aliases:
        if hasattr(konfiguration, alias):
            return getattr(konfiguration, alias)
    return default

# 480x280 Display — sichtbarer Bereich durch Parkscheiben-Gehaeuse
# 56mm x 29.5mm ≈ 337 x 177 px, zentriert
VX = _cfg("DOOM_VIEW_X", 87, "DOOM_VX")       # Viewport X-Offset (kalibriert)
VY = _cfg("DOOM_VIEW_Y", 77, "DOOM_VY")       # Viewport Y-Offset (kalibriert)
VW = _cfg("DOOM_VIEW_W", 337, "DOOM_VW")      # Viewport Breite
VH = _cfg("DOOM_VIEW_H", 177, "DOOM_VH")      # Viewport Hoehe
VCX = VX + VW // 2   # Viewport Mitte X
VCY = VY + VH // 2   # Viewport Mitte Y
HUD_H = _cfg("DOOM_HUD_H", 30)                # HUD-Hoehe unten im Viewport

# Richtungsnamen
_DIR_NAME = _cfg("DOOM_DIR_NAMES", ("O", "S", "W", "N"))
ENEMY_TICK_MS = _cfg("DOOM_ENEMY_TICK_MS", 2000)
SHOOT_RANGE = _cfg("DOOM_SHOOT_RANGE", 3)
ANGLE_STEPS = _cfg("DOOM_ANGLE_STEPS", 128)
ROT_STEP = _cfg("DOOM_ROT_STEP", 4)
MOVE_STEP_FP = _cfg("DOOM_MOVE_STEP_FP", 256)
RAY_COL_W = _cfg("DOOM_RAY_COL_W", 4)
MAX_RENDER_DEPTH = _cfg("DOOM_MAX_DEPTH", 12)
FOV_COEF_FP = _cfg("DOOM_FOV_COEF_FP", 591)
LOGO_DURATION_MS = _cfg("DOOM_LOGO_DURATION_MS", 1800)

_FP = 1024
_SIN = tuple(int(math.sin((2.0 * math.pi * i) / ANGLE_STEPS) * _FP) for i in range(ANGLE_STEPS))
_COS = tuple(int(math.cos((2.0 * math.pi * i) / ANGLE_STEPS) * _FP) for i in range(ANGLE_STEPS))

# Eigene 8x8 Schriftart-Bits fuer Umlaute (von oben nach unten, 1 Byte pro Zeile)
_UMLAUTS = {
    'Ä': b'\x42\x00\x3c\x42\x42\x7e\x42\x42',
    'Ö': b'\x42\x00\x3c\x42\x42\x42\x42\x3c',
    'Ü': b'\x42\x00\x42\x42\x42\x42\x42\x3c',
    'ä': b'\x42\x00\x3c\x02\x3e\x42\x46\x3b',
    'ö': b'\x42\x00\x3c\x42\x42\x42\x42\x3c',
    'ü': b'\x42\x00\x42\x42\x42\x42\x46\x3b',
    'ß': b'\x3e\x42\x42\x7e\x42\x42\x42\x5c',
}

# Kartengroesse
MAP_W = _cfg("DOOM_MAP_W", 14)
MAP_H = _cfg("DOOM_MAP_H", 10)

# Original-Kartenvorlage (wird bei jedem Spielstart kopiert)
_MAP_TEMPLATE = _cfg("DOOM_MAP_TEMPLATE", (
    (1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1),
    (1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 2, 0, 1),
    (1, 0, 1, 1, 0, 0, 1, 0, 1, 1, 0, 1, 0, 1),
    (1, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1),
    (1, 1, 0, 1, 1, 1, 0, 1, 0, 1, 1, 1, 0, 1),
    (1, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 2, 0, 1),
    (1, 0, 1, 1, 1, 0, 1, 1, 1, 1, 0, 1, 0, 1),
    (1, 2, 0, 0, 1, 0, 0, 0, 2, 1, 0, 0, 0, 1),
    (1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 2, 3, 1),
    (1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1),
))


def _ang_norm(a):
    if a >= ANGLE_STEPS:
        return a % ANGLE_STEPS
    if a < 0:
        return a % ANGLE_STEPS
    return a

def _ticks_add(base, delta):
    try:
        return utime.ticks_add(base, delta)
    except AttributeError:
        return base + delta

class DoomGame:
    def __init__(self):
        self.px_fp = (1 << 10) + (1 << 9)
        self.py_fp = (1 << 10) + (1 << 9)
        self.ang = 0
        self.msg = "SPIEL START"
        self.msg_timer = utime.ticks_ms()
        self.kills = 0
        self.hp = 4
        self.won = False
        self.dead = False
        self.flash_ms = 0
        self.last_enemy_tick = utime.ticks_ms()
        self.map = [list(row) for row in _MAP_TEMPLATE]
        self.frame = 0
        self.gun_flash_frames = 0
        self.logo_until_ms = 0
        self.logo_start_ms = 0
        self.cols = max(1, VW // max(1, RAY_COL_W))
        self.zbuf = bytearray(b"\xff" * self.cols)

    def on_enter_mode(self):
        self.logo_start_ms = utime.ticks_ms()
        self.logo_until_ms = _ticks_add(self.logo_start_ms, LOGO_DURATION_MS)

    def _in_logo_phase(self):
        if self.logo_until_ms <= 0:
            return False
        return utime.ticks_diff(self.logo_until_ms, utime.ticks_ms()) > 0

    def _cell(self, x, y):
        if x < 0 or y < 0 or x >= MAP_W or y >= MAP_H:
            return 1
        return self.map[y][x]

    def _player_cell(self):
        return self.px_fp >> 10, self.py_fp >> 10

    def _dir_cardinal(self):
        q = ANGLE_STEPS // 4
        return ((self.ang + q // 2) // q) % 4

    def _try_move(self, sign=1):
        dx = (_COS[self.ang] * MOVE_STEP_FP * sign) >> 10
        dy = (_SIN[self.ang] * MOVE_STEP_FP * sign) >> 10
        nx_fp = self.px_fp + dx
        ny_fp = self.py_fp + dy
        nx = nx_fp >> 10
        ny = ny_fp >> 10

        if self._cell(nx, self.py_fp >> 10) != 1:
            self.px_fp = nx_fp
        if self._cell(self.px_fp >> 10, ny) != 1:
            self.py_fp = ny_fp

        self._check_cell()

    def handle_action(self, action):
        if self._in_logo_phase():
            return
        if self.won or self.dead:
            if action == "shoot":
                self.__init__()
            return

        if action == "up":
            self._try_move(1)
        elif action == "down":
            self._try_move(-1)
        elif action == "left":
            self.ang = _ang_norm(self.ang - ROT_STEP)
        elif action == "right":
            self.ang = _ang_norm(self.ang + ROT_STEP)
        elif action == "shoot":
            self.gun_flash_frames = 3
            self._shoot()

    def _check_cell(self):
        cx, cy = self._player_cell()
        cell = self.map[cy][cx]
        if cell == 2:
            self._take_hit()
            self.px_fp -= (_COS[self.ang] * MOVE_STEP_FP) >> 10
            self.py_fp -= (_SIN[self.ang] * MOVE_STEP_FP) >> 10
        elif cell == 3:
            self._set_msg("ÜBERLEBT!")
            self.won = True

    def _take_hit(self):
        self.hp -= 1
        self.flash_ms = utime.ticks_ms()
        if self.hp <= 0:
            self._set_msg("GESTORBEN!")
            self.dead = True
        else:
            self._set_msg("AUTSCH! HP: " + str(self.hp))

    @micropython.native
    def tick(self):
        if self.won or self.dead:
            return
        now = utime.ticks_ms()
        if utime.ticks_diff(now, self.last_enemy_tick) < ENEMY_TICK_MS:
            return
        self.last_enemy_tick = now

        pxc, pyc = self._player_cell()
        
        enemies_to_move = []
        for y in range(MAP_H):
            for x in range(MAP_W):
                if self.map[y][x] == 2:
                    enemies_to_move.append((x, y))

        # Wegfindung: BFS um den kuerzesten Weg zum Spieler um Waende herum zu finden
        for ex, ey in enemies_to_move:
            if ex == pxc and ey == pyc:
                self._take_hit()
                continue
            
            # Distanz zum Spieler berechnen (Manhattan Distanz reicht als schnelle Naeherung)
            dist_to_player = abs(ex - pxc) + abs(ey - pyc)
            
            best_nx, best_ny = None, None
            
            if dist_to_player <= 5:
                # Spieler in Reichweite -> BFS Pathfinding um ihn zu jagen
                q = []
                visited = bytearray(MAP_W * MAP_H)
                
                # Startpunkt initialisieren (4 Nachbarfelder)
                for dx, dy in ((0, -1), (0, 1), (-1, 0), (1, 0)):
                    nx, ny = ex + dx, ey + dy
                    if 0 <= nx < MAP_W and 0 <= ny < MAP_H:
                        if self.map[ny][nx] == 0 or (nx == pxc and ny == pyc):
                            q.append((nx, ny, nx, ny))
                            visited[ny * MAP_W + nx] = 1
                
                head = 0
                while head < len(q):
                    cx, cy, first_nx, first_ny = q[head]
                    head += 1
                    
                    if cx == pxc and cy == pyc:
                        best_nx, best_ny = first_nx, first_ny
                        break
                        
                    for dx, dy in ((0, -1), (0, 1), (-1, 0), (1, 0)):
                        nx, ny = cx + dx, cy + dy
                        if 0 <= nx < MAP_W and 0 <= ny < MAP_H:
                            idx = ny * MAP_W + nx
                            if not visited[idx]:
                                visited[idx] = 1
                                if self.map[ny][nx] == 0 or (nx == pxc and ny == pyc):
                                    q.append((nx, ny, first_nx, first_ny))
            else:
                # Spieler ausser Reichweite -> zufaelliges Umherwandern (Idle)
                import random
                possible_moves = []
                for dx, dy in ((0, -1), (0, 1), (-1, 0), (1, 0)):
                    nx, ny = ex + dx, ey + dy
                    if 0 <= nx < MAP_W and 0 <= ny < MAP_H:
                        # Nur auf leere Felder wandern (nicht in Spieler laufen wenn out of aggro)
                        if self.map[ny][nx] == 0:
                            possible_moves.append((nx, ny))
                
                if possible_moves:
                    # 50% Chance sich ueberhaupt zu bewegen, wirkt "zombie-artiger"
                    if random.getrandbits(1):
                        best_nx, best_ny = random.choice(possible_moves)

            # Bewegen, falls ein gueltiger Pfad/Schritt gefunden wurde
            if best_nx is not None and best_ny is not None:
                if best_nx == pxc and best_ny == pyc:
                    self._take_hit()
                elif self.map[best_ny][best_nx] == 0:
                    self.map[ey][ex] = 0
                    self.map[best_ny][best_nx] = 2

    def _shoot(self):
        ray_x = _COS[self.ang]
        ray_y = _SIN[self.ang]
        sx_fp = self.px_fp
        sy_fp = self.py_fp
        step_fp = 256
        max_steps = max(1, SHOOT_RANGE * 4)

        for _ in range(max_steps):
            sx_fp += (ray_x * step_fp) >> 10
            sy_fp += (ray_y * step_fp) >> 10
            x = sx_fp >> 10
            y = sy_fp >> 10

            if x < 0 or y < 0 or x >= MAP_W or y >= MAP_H:
                self._set_msg("ZU WEIT WEG")
                break
            if self.map[y][x] == 1:
                self._set_msg("WAND GETROFFEN")
                break
            if self.map[y][x] == 2:
                self.map[y][x] = 0
                self.kills += 1
                self._set_msg("GEGNER TOT!")
                break
        else:
            self._set_msg("PENG PENG")

    def _render_text(self, display, text, x, y, color):
        """Wrapper fuer display.text, der auch Umlaute zeichnet."""
        px = x
        for char in text:
            if char in _UMLAUTS:
                # Custom character zeichnen
                font_data = _UMLAUTS[char]
                for dy in range(8):
                    row = font_data[dy]
                    for dx in range(8):
                        if (row >> (7 - dx)) & 1:
                            display.pixel(px + dx, y + dy, color)
            else:
                # Standard character
                if hasattr(display, 'text'):
                    display.text(char, px, y, color)
            px += 8

    def _set_msg(self, text):
        self.msg = text
        self.msg_timer = utime.ticks_ms()

    @micropython.native
    def _render_walls(self, display, scene_h):
        pos_x = self.px_fp / 1024.0
        pos_y = self.py_fp / 1024.0
        dir_x = _COS[self.ang] / 1024.0
        dir_y = _SIN[self.ang] / 1024.0
        plane_x = -dir_y * (FOV_COEF_FP / 1024.0)
        plane_y = dir_x * (FOV_COEF_FP / 1024.0)

        for ci in range(self.cols):
            cam_x = (2.0 * ci / self.cols) - 1.0
            ray_x = dir_x + plane_x * cam_x
            ray_y = dir_y + plane_y * cam_x

            map_x = int(pos_x)
            map_y = int(pos_y)

            if ray_x == 0:
                ray_x = 1e-6
            if ray_y == 0:
                ray_y = 1e-6

            delta_x = abs(1.0 / ray_x)
            delta_y = abs(1.0 / ray_y)

            if ray_x < 0:
                step_x = -1
                side_x = (pos_x - map_x) * delta_x
            else:
                step_x = 1
                side_x = (map_x + 1.0 - pos_x) * delta_x

            if ray_y < 0:
                step_y = -1
                side_y = (pos_y - map_y) * delta_y
            else:
                step_y = 1
                side_y = (map_y + 1.0 - pos_y) * delta_y

            hit = False
            side = 0
            depth = 0

            while not hit and depth < MAX_RENDER_DEPTH:
                if side_x < side_y:
                    side_x += delta_x
                    map_x += step_x
                    side = 0
                else:
                    side_y += delta_y
                    map_y += step_y
                    side = 1

                if map_x < 0 or map_y < 0 or map_x >= MAP_W or map_y >= MAP_H:
                    break
                if self.map[map_y][map_x] == 1:
                    hit = True
                depth += 1

            if not hit:
                self.zbuf[ci] = 255
                continue

            if side == 0:
                dist = (map_x - pos_x + (1 - step_x) * 0.5) / ray_x
            else:
                dist = (map_y - pos_y + (1 - step_y) * 0.5) / ray_y

            if dist <= 0.05:
                dist = 0.05

            di = int(dist * 16)
            if di > 255:
                di = 255
            self.zbuf[ci] = di

            h = int(scene_h / dist)
            if h < 1:
                h = 1
            if h > scene_h:
                h = scene_h

            y0 = VY + (scene_h - h) // 2
            x0 = VX + ci * RAY_COL_W
            w = RAY_COL_W
            if x0 + w > VX + VW:
                w = VX + VW - x0
            if w > 0:
                display.rect(x0, y0, w, h, display.black, f=True)
                
                # Tiefeneffekt & Wand-Abgrenzung (Rasterung)
                if side == 1 and h > 3:
                    # Helle Wandseite: Ein senkrechter Streifen in der Mitte der Saeule
                    display.vline(x0 + w//2, y0, h, display.white)
                    
                if dist > 3.0:
                    # Ab ca. 3 Bloecken Entfernung wird die Textur schraffiert (verblasst im Nebel)
                    # Je nach Spalte (ci) versetzen wir die Streifen um 1 Pixel -> Schachbrett
                    offset = ci % 2
                    for dy in range(offset, h, 2):
                        display.hline(x0, y0 + dy, w, display.white)

    @micropython.native
    def _render_enemies(self, display, scene_h):
        pos_x = self.px_fp / 1024.0
        pos_y = self.py_fp / 1024.0
        dir_x = _COS[self.ang] / 1024.0
        dir_y = _SIN[self.ang] / 1024.0
        plane_x = -dir_y * (FOV_COEF_FP / 1024.0)
        plane_y = dir_x * (FOV_COEF_FP / 1024.0)

        inv_det_den = (plane_x * dir_y - dir_x * plane_y)
        if inv_det_den == 0:
            return
        inv_det = 1.0 / inv_det_den

        enemies = []
        for y in range(MAP_H):
            row = self.map[y]
            for x in range(MAP_W):
                if row[x] == 2:
                    dx = (x + 0.5) - pos_x
                    dy = (y + 0.5) - pos_y
                    enemies.append((dx * dx + dy * dy, x, y))

        enemies.sort(reverse=True)

        y_center = VY + scene_h // 2
        for _, ex, ey in enemies:
            sx = (ex + 0.5) - pos_x
            sy = (ey + 0.5) - pos_y
            tx = inv_det * (dir_y * sx - dir_x * sy)
            ty = inv_det * (-plane_y * sx + plane_x * sy)
            
            # Absturz-Schutz: Division durch Null verhindern wenn Gegner genau auf der Kameraebene
            # steht oder der Spieler den Gegner komplett ueberlappt.
            if abs(ty) < 0.05:
                continue

            # Gegner sind zu nah/gross dargestellt. Faktor anpassen:
            # Statt sprite_h direkt aus scene_h / ty, machen wir sie 60% so gross.
            # Um sie am Boden zu halten, addieren wir einen vertikalen Versatz.
            sprite_h_base = int(scene_h / ty)
            sprite_h = int(sprite_h_base * 0.6)
            
            if sprite_h < 2:
                continue
            if sprite_h > scene_h:
                sprite_h = scene_h
            # Breite ebenfalls skalieren (ca 2:1 Oval wie gewuenscht)
            sprite_w = max(2, sprite_h // 2)

            cx_pix = int((VW * 0.5) * (1.0 + tx / ty))
            x0_col = int((cx_pix - sprite_w // 2) // max(1, RAY_COL_W))
            x1_col = int((cx_pix + sprite_w // 2) // max(1, RAY_COL_W))

            # Treffer-Blitz erkennen (rot/invertiert)
            is_flashing = utime.ticks_diff(utime.ticks_ms(), getattr(self, "flash_ms", 0)) < 300
            color_bg = display.black if is_flashing else display.white
            color_fg = display.white if is_flashing else display.black

            for ci in range(x0_col, x1_col + 1):
                if ci < 0 or ci >= self.cols:
                    continue
                if int(ty * 16) > self.zbuf[ci]:
                    continue
                x0 = VX + ci * RAY_COL_W
                w = RAY_COL_W
                if x0 + w > VX + VW:
                    w = VX + VW - x0
                if w > 0:
                    col_cx = ci * RAY_COL_W + w / 2.0
                    dx = col_cx - cx_pix
                    rad_sq = 1.0 - (2.0 * dx / sprite_w)**2
                    if rad_sq > 0:
                        dy = (sprite_h / 2.0) * math.sqrt(rad_sq)
                        # Basis-Position war mittig. Jetzt tiefer setzen (Boden-Kontakt):
                        # sprite_h_base ist die volle Hoehe, sprite_h ist die verkleinerte.
                        # Wir schieben es um die halbe Differenz nach unten.
                        y_offset = (sprite_h_base - sprite_h) // 2
                        e_y0 = int(y_center - dy) + y_offset
                        e_h = int(dy * 2)
                        
                        # Zuerst das komplette Sprite in Weiss fuellen, damit Waende verdeckt werden
                        display.rect(x0, e_y0, w, e_h, color_bg, f=True)
                        
                        # Darueber das Schachbrettmuster fuer den Gegner in Schwarz
                        cw = max(2, RAY_COL_W)
                        offset = (ci % 2) * cw
                        for ey in range(offset, e_h, cw * 2):
                            bh = min(cw, e_h - ey)
                            display.rect(x0, e_y0 + ey, w, bh, color_fg, f=True)

    @micropython.native
    def _render_minimap(self, display):
        mm_s = 3
        mm_x = _cfg("DOOM_MM_X", VX + VW - MAP_W * mm_s - 4)
        mm_y = _cfg("DOOM_MM_Y", VY + 20)
        
        # Hintergrund weiss fuellen, damit der 3D-View verdeckt wird
        display.rect(mm_x - 1, mm_y - 1, MAP_W * mm_s + 2, MAP_H * mm_s + 2, display.white, f=True)
        # Schwarzer Rahmen
        display.rect(mm_x - 1, mm_y - 1, MAP_W * mm_s + 2, MAP_H * mm_s + 2, display.black)

        for my in range(MAP_H):
            for mx in range(MAP_W):
                c = self.map[my][mx]
                px = mm_x + mx * mm_s
                py = mm_y + my * mm_s
                if c == 1:
                    display.rect(px, py, mm_s, mm_s, display.black, f=True)
                elif c == 2:
                    display.pixel(px + 1, py + 1, display.black)

        pxc, pyc = self._player_cell()
        px = mm_x + pxc * mm_s
        py = mm_y + pyc * mm_s
        
        # Blinkeffekt wechselt mit jedem Frame. 
        # Da das Spiel im Idle alle 500ms neu rendert, blinkt es ca. im 1-Sekunden-Takt.
        blink_on = self.frame % 2 == 0
        
        if blink_on:
            display.rect(px, py, mm_s, mm_s, display.black)
            if mm_s > 2:
                display.pixel(px + 1, py + 1, display.black)
        else:
            # Weisses (leeres) Rechteck zeichnen um es auszublenden
            display.rect(px, py, mm_s, mm_s, display.white, f=True)

    @micropython.native
    def _render_logo(self, display):
        display.fill(display.white)

        lw = _cfg("PARKDOOM_LOGO_W", 0)
        lh = _cfg("PARKDOOM_LOGO_H", 0)
        ldata = _cfg("PARKDOOM_LOGO_DATA", None)

        if ldata and lw > 0 and lh > 0:
            import framebuf
            # Daten kopieren, um sie invertieren zu koennen, falls es bytes() sind
            data_copy = bytearray(ldata)
            for i in range(len(data_copy)):
                data_copy[i] ^= 0xFF
                
            fb = framebuf.FrameBuffer(data_copy, lw, lh, framebuf.MONO_HLSB)
            lx = VX + (VW - lw) // 2
            ly = VY + (VH - lh) // 2
            
            # Etwas hoeher positionieren fuer den Ladebalken
            ly_logo = ly - 10
            display.blit(fb, lx, ly_logo)
            
            # Ladebalken zeichnen
            bar_w = 200
            bar_h = 10
            bar_x = VX + (VW - bar_w) // 2
            bar_y = ly_logo + lh + 15
            
            display.rect(bar_x, bar_y, bar_w, bar_h, display.black)
            
            if hasattr(self, 'logo_start_ms'):
                elapsed = utime.ticks_diff(utime.ticks_ms(), self.logo_start_ms)
                x = elapsed / max(1, LOGO_DURATION_MS)
                if x > 1.0: x = 1.0
                
                # Unregelmaessiger Fortschritt fuer realistischen Ladebalken-Effekt
                if x < 0.15:
                    p = (x / 0.15) * 0.12
                elif x < 0.35:
                    p = 0.12 + ((x - 0.15) / 0.20) * 0.03
                elif x < 0.45:
                    p = 0.15 + ((x - 0.35) / 0.10) * 0.45
                elif x < 0.70:
                    p = 0.60 + ((x - 0.45) / 0.25) * 0.15
                elif x < 0.85:
                    p = 0.75 + ((x - 0.70) / 0.15) * 0.20
                else:
                    p = 0.95 + ((x - 0.85) / 0.15) * 0.05
                    
                p = max(0.0, min(1.0, p))
                fill_w = int((bar_w - 4) * p)
                if fill_w > 0:
                    display.rect(bar_x + 2, bar_y + 2, fill_w, bar_h - 4, display.black, f=True)

    @micropython.native
    def render(self, display):
        if self._in_logo_phase():
            self._render_logo(display)
            display.show()
            return

        self.tick()
        display.fill(display.white)

        scene_h = VH
        hud_y = VY + VH
        mid_y = VY + scene_h // 2
        display.hline(VX + 1, mid_y, VW - 2, display.black)

        self._render_walls(display, scene_h)
        self._render_enemies(display, scene_h)
        self._render_minimap(display)

        cdir = self._dir_cardinal()
        
        # LP: 4-teiliges Herz, leert sich gegen den Uhrzeigersinn (Oben-Links -> Unten-Links -> Unten-Rechts -> Oben-Rechts)
        # O = Rahmen-Pixel (immer), Zahlen 1-4 = gefuellte Pixel wenn LP >= Zahl
        hp_x = _cfg("DOOM_HP_X", VX + 4)
        hp_y = _cfg("DOOM_HP_Y", VY + 4)
        display.rect(hp_x, hp_y, 30, 24, display.white, f=True)
        hx, hy = hp_x + 4, hp_y + 2
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
                if char == 'O' or (char.isdigit() and int(char) <= self.hp):
                    display.rect(hx + hx_idx*2, hy + hy_idx*2, 2, 2, display.black, f=True)
        
        # Kompass-String erzeugen (basiert auf 128 Winkelschritten)
        # Die 8 Himmelsrichtungen sind auf dem 128er-Raster wie folgt verteilt:
        # O=0, SO=16, S=32, SW=48, W=64, NW=80, N=96, NO=112
        # Wir bauen einen String, der doppelt so lang ist, um flüssig zu sliden
        comp_map = "O --SO--S --SW--W --NW--N --NO--"
        comp_len = len(comp_map)
        
        # Umrechnen des Winkels in den String-Index (1 Angle-Step = 1/4 Char)
        # 128 Steps entsprechen 32 Zeichen.
        idx = int((self.ang / ANGLE_STEPS) * 32)
        
        # 11 Zeichen aus dem (verdoppelten) String ausschneiden
        comp_str = (comp_map + comp_map)[idx : idx + 11]

        k_str = "A:" + str(self.kills)
        
        # Gesamte Breite ermitteln: Abschuss-String + Leerzeichen + Kompass-String
        full_str = k_str + " | " + comp_str
        
        # Rechtsbuendig rendern
        k_x = _cfg("DOOM_KILLS_X", VX + VW - len(full_str) * 8 - 8)
        k_y = _cfg("DOOM_KILLS_Y", VY + 4)
        
        # Weissen Hintergrundkasten zeichnen
        display.rect(k_x, k_y, len(full_str) * 8 + 4, 12, display.white, f=True)
        # Text rendern
        self._render_text(display, full_str, k_x + 2, k_y + 2, display.black)

        if utime.ticks_diff(utime.ticks_ms(), self.msg_timer) < 3000:
            msg_w = len(self.msg) * 8
            display.rect(VCX - msg_w//2 - 4, VY + 4, msg_w + 8, 12, display.white, f=True)
            self._render_text(display, self.msg, VCX - msg_w//2, VY + 6, display.black)
        elif self.won or self.dead:
            msg = "FEUER: NEUSTART"
            msg_w = len(msg) * 8
            display.rect(VCX - msg_w//2 - 4, VY + 4, msg_w + 8, 12, display.white, f=True)
            self._render_text(display, msg, VCX - msg_w//2, VY + 6, display.black)

        if hasattr(display, "line"):
            gun_x = _cfg("DOOM_GUN_X", VCX)
            gun_y = _cfg("DOOM_GUN_Y", hud_y)
            
            # Blitz-Effekt: 3 Bilder lang aktiv. Bild 3: Schwarz, Bild 2: Weiss, Bild 1: Schwarz
            # -> Erzeugt ein Doppel-Blitzen
            is_flashing = self.gun_flash_frames > 0 and (self.gun_flash_frames % 2 != 0)
            fill_c = display.black if is_flashing else display.white
            
            if self.gun_flash_frames > 0:
                self.gun_flash_frames -= 1
                
            # Dreieck fuellen (von der Spitze nach unten)
            for dy in range(31):
                w = (dy * 10) // 30
                display.hline(gun_x - w, (gun_y - 30) + dy, w * 2 + 1, fill_c)
                
            # Permanenter schwarzer Rahmen
            display.line(gun_x - 10, gun_y, gun_x, gun_y - 30, display.black)
            display.line(gun_x, gun_y - 30, gun_x + 10, gun_y, display.black)
            display.hline(gun_x - 10, gun_y, 21, display.black)

        display.show()
        self.frame += 1
        if (self.frame & 7) == 0:
            gc.collect()
