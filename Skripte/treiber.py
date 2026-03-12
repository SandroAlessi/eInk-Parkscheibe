# LUTs vom Waveshare Pico e-Paper 3.7 Beispiel
# https://github.com/waveshare/Pico_ePaper_Code/blob/main/python/Pico-ePaper-3.7.py

EPD_3IN7_lut_4Gray_GC = bytes([
    0x2A,0x06,0x15,0x00,0x00,0x00,0x00,0x00,0x00,0x00,
    0x28,0x06,0x14,0x00,0x00,0x00,0x00,0x00,0x00,0x00,
    0x20,0x06,0x10,0x00,0x00,0x00,0x00,0x00,0x00,0x00,
    0x14,0x06,0x28,0x00,0x00,0x00,0x00,0x00,0x00,0x00,
    0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,
    0x00,0x02,0x02,0x0A,0x00,0x00,0x00,0x08,0x08,0x02,
    0x00,0x02,0x02,0x0A,0x00,0x00,0x00,0x00,0x00,0x00,
    0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,
    0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,
    0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,
    0x22,0x22,0x22,0x22,0x22
])

EPD_3IN7_lut_1Gray_GC = bytes([
    0x2A,0x05,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,
    0x05,0x2A,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,
    0x2A,0x15,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,
    0x05,0x0A,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,
    0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,
    0x00,0x02,0x03,0x0A,0x00,0x02,0x06,0x0A,0x05,0x00,
    0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,
    0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,
    0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,
    0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,
    0x22,0x22,0x22,0x22,0x22
])

EPD_3IN7_lut_1Gray_DU = bytes([
    0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,
    0x01,0x2A,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,
    0x0A,0x55,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,
    0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,
    0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,
    0x00,0x00,0x05,0x05,0x00,0x05,0x03,0x05,0x05,0x00,
    0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,
    0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,
    0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,
    0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,
    0x22,0x22,0x22,0x22,0x22
])

EPD_3IN7_lut_1Gray_A2 = bytes([
    0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,
    0x0A,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,
    0x05,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,
    0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,
    0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,
    0x00,0x00,0x03,0x05,0x00,0x00,0x00,0x00,0x00,0x00,
    0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,
    0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,
    0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,
    0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,
    0x22,0x22,0x22,0x22,0x22
])

# LUTs als Tuple (Index-Zugriff, kein Dict-Overhead)
_LUTS = (EPD_3IN7_lut_4Gray_GC, EPD_3IN7_lut_1Gray_GC,
         EPD_3IN7_lut_1Gray_DU, EPD_3IN7_lut_1Gray_A2)

from machine import Pin
import machine
import framebuf
from utime import ticks_ms, ticks_diff, sleep_ms
from ustruct import pack
import gc
import micropython
import sys
# Vorkompilierte Konstanten (vermeidet pack()-Aufrufe zur Laufzeit)
_GATE_CFG = pack("hB", 479, 0)
_SRC_VOLTAGE = pack("3B", 0x41, 0xa8, 0x32)
_BOOST_CFG = pack("5B", 0xae, 0xc7, 0xc3, 0xc0, 0xc0)
_PARTIAL_ON = pack("10B", 0x00, 0xff, 0xff, 0xff, 0xff, 0x4f, 0xff, 0xff, 0xff, 0xff)
_PARTIAL_OFF = pack("10B", 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00)


class EinkBase:
    black = 0b00
    white = 0b11
    darkgray = 0b01
    lightgray = 0b10
    RAM_BW = 0b01
    RAM_RED = 0b10
    RAM_RBW = 0b11

    def __init__(self, rotation=0, cs_pin=None, dc_pin=None, reset_pin=None, busy_pin=None, use_partial_buffer=False):
        if rotation in (0, 180):
            self.width = 280
            self.height = 480
            buf_format = framebuf.MONO_HLSB
            self._horizontal = False
        elif rotation in (90, 270):
            self.width = 480
            self.height = 280
            buf_format = framebuf.MONO_VLSB
            self._horizontal = True
        else:
            raise ValueError("Ungueltige Rotation")

        self._rotation = rotation

        # Pin-Konfiguration
        self._rst = (reset_pin or Pin(12, Pin.OUT, value=0))
        self._dc = (dc_pin or Pin(8, Pin.OUT, value=0))
        self._cs = (cs_pin or Pin(9, Pin.OUT, value=1))
        self._busy = (busy_pin or Pin(13, Pin.IN, Pin.PULL_UP))

        if reset_pin: self._rst.init(Pin.OUT, value=0)
        if dc_pin: self._dc.init(Pin.OUT, value=0)
        if cs_pin: self._cs.init(Pin.OUT, value=1)
        if busy_pin: self._busy.init(Pin.IN)

        # Framebuffer anlegen
        bw_size = self.width * self.height // 8
        self._buffer_bw_actual = bytearray(bw_size)
        self._buffer_red = bytearray(bw_size)
        self._bw_actual = framebuf.FrameBuffer(self._buffer_bw_actual, self.width, self.height, buf_format)
        self._red = framebuf.FrameBuffer(self._buffer_red, self.width, self.height, buf_format)

        self._partial = False
        self._use_partial_buffer = use_partial_buffer
        if use_partial_buffer:
            self._buffer_partial = bytearray(bw_size)
            self._part = framebuf.FrameBuffer(self._buffer_partial, self.width, self.height, buf_format)
        else:
            self._buffer_partial = None
            self._part = None

        self._buffer_bw = self._buffer_bw_actual
        self._bw = self._bw_actual

        self.fill()
        self._init_disp()
        sleep_ms(500)

    def _reset(self):
        self._rst(1); sleep_ms(30)
        self._rst(0); sleep_ms(3)
        self._rst(1); sleep_ms(30)

    def _send_command(self, command):
        raise NotImplementedError

    def _send_data(self, data):
        raise NotImplementedError

    def _send(self, command, data):
        self._send_command(command)
        self._send_data(data)

    def _read_busy(self):
        timeout = 3000  # 30s
        count = 0
        while self._busy.value() == 1 and timeout > 0:
            sleep_ms(10)
            timeout -= 1
            count += 1
            if count % 100 == 0 and hasattr(self, 'wdt') and self.wdt:
                self.wdt.feed()

        if timeout <= 0:
            self._reset()
            sleep_ms(500)

    def _load_LUT(self, lut=0):
        self._send(0x32, _LUTS[lut])

    def _set_cursor(self, x, y):
        self._send(0x4e, pack("h", x))
        self._send(0x4f, pack("h", y))

    def _set_window(self, start_x, end_x, start_y, end_y):
        self._send(0x44, pack("2h", start_x, end_x))
        self._send(0x45, pack("2h", start_y, end_y))

    def _clear_ram(self, bw=True, red=True):
        if red:
            self._send(0x46, 0xf7)
            self._read_busy()
        if bw:
            self._send(0x47, 0xf7)
            self._read_busy()

    def _init_disp(self):
        self._reset()
        self._send_command(0x12)  # Software-Reset
        sleep_ms(300)
        self._clear_ram()

        self._send(0x01, _GATE_CFG)
        self._send(0x03, 0x00)
        self._send(0x04, _SRC_VOLTAGE)

        # Daten-Eingabemodus
        seq = {0: 0x03, 180: 0x00, 90: 0x06, 270: 0x05}[self._rotation]
        self._send(0x11, seq)

        self._send(0x3c, 0x03)
        self._send(0x0c, _BOOST_CFG)
        self._send(0x18, 0x80)
        self._send(0x2c, 0x44)

        # Fenster
        r = self._rotation
        w, h = self.width, self.height
        if r == 0:    self._set_window(0, w-1, 0, h-1)
        elif r == 180: self._set_window(w-1, 0, h-1, 0)
        elif r == 90:  self._set_window(h-1, 0, 0, w-1)
        elif r == 270: self._set_window(0, h-1, w-1, 0)

        self._send(0x22, 0xcf)

    # --- Oeffentliche API ---

    def reinit(self):
        self._init_disp()

    def partial_mode_on(self):
        self._send(0x37, _PARTIAL_ON)
        self._clear_ram(bw=True, red=False)  # RED (0x26) behalten = altes Bild fuer DU-Vergleich
        if self._use_partial_buffer:
            self._buffer_bw = self._buffer_partial
            self._bw = self._part
        self._part.fill(1)
        self._partial = True

    def partial_mode_off(self):
        self._send(0x37, _PARTIAL_OFF)
        self._clear_ram()
        if self._use_partial_buffer:
            self._buffer_bw = self._buffer_bw_actual
            self._bw = self._bw_actual
        self._partial = False

    def show(self, lut=0):
        r = self._rotation
        if r == 0:     self._set_cursor(0, 0)
        elif r == 180: self._set_cursor(self.width-1, self.height-1)
        elif r == 90:  self._set_cursor(self.height-1, 0)
        else:          self._set_cursor(0, self.width-1)

    def sleep(self):
        self._send(0x10, 0x03)

    # --- Zeichenfunktionen (FrameBuffer-Wrapper) ---

    def fill(self, c=white):
        self._bw.fill(c & 1)
        if not self._partial:
            self._red.fill(c >> 1)

    def pixel(self, x, y, c=black):
        self._bw.pixel(x, y, c & 1)
        if not self._partial: self._red.pixel(x, y, c >> 1)

    def hline(self, x, y, w, c=black):
        self._bw.hline(x, y, w, c & 1)
        if not self._partial: self._red.hline(x, y, w, c >> 1)

    def vline(self, x, y, h, c=black):
        self._bw.vline(x, y, h, c & 1)
        if not self._partial: self._red.vline(x, y, h, c >> 1)

    def line(self, x1, y1, x2, y2, c=black):
        self._bw.line(x1, y1, x2, y2, c & 1)
        if not self._partial: self._red.line(x1, y1, x2, y2, c >> 1)

    def rect(self, x, y, w, h, c=black, f=False):
        self._bw.rect(x, y, w, h, c & 1, f)
        if not self._partial: self._red.rect(x, y, w, h, c >> 1, f)

    def ellipse(self, x, y, xr, yr, c=black, f=False, m=15):
        self._bw.ellipse(x, y, xr, yr, c & 1, f, m)
        if not self._partial: self._red.ellipse(x, y, xr, yr, c >> 1, f, m)

    def poly(self, x, y, coords, c=black, f=False):
        self._bw.poly(x, y, coords, c & 1, f)
        if not self._partial: self._red.poly(x, y, coords, c >> 1, f)

    def text(self, text, x, y, c=black):
        self._bw.text(text, x, y, c & 1)
        if not self._partial: self._red.text(text, x, y, c >> 1)

    def blit(self, fbuf, x, y, key=-1, palette=None, ram=RAM_RBW):
        if ram & 1 == 1 or self._partial:
            self._bw.blit(fbuf, x, y, key, palette)
        if (ram >> 1) & 1 == 1:
            self._red.blit(fbuf, x, y, key, palette)


class EinkPIO(EinkBase):
    from machine import mem32

    def __init__(self, sm_num=0, dma=5, *args, **kwargs):
        self._sm_num = sm_num
        self._dma = int(dma * 0x40 + 0x50000030)
        self._sm = None
        self._sm_shiftctrl = (0x502000d0 + 0x100000 * (sm_num // 4)
                              + 0x18 * (sm_num % 4))
        self._dma_write_addr = (0x50200010 + 0x100000 * (sm_num // 4)
                                + 0x4 * (sm_num % 4))
        dreq = sm_num % 4 + 8 * (sm_num // 4)
        if "RP2350" in getattr(sys.implementation, "_machine", ""):
            self._dma_ctrl = dreq << 17 | 1 << 4 | 1
            self._busy_shift = 26
        else:
            self._dma_ctrl = dreq << 15 | 1 << 4 | 1
            self._busy_shift = 24
        self._pio_setup()
        self._fstat = 0x50200004 + 0x100000 * (sm_num // 4)
        self._txempty_bit = 24 + (sm_num % 4)

        super(EinkPIO, self).__init__(*args, **kwargs)

        self.buffer = self._buffer_bw
        self.wdt = None

    def init(self):
        self.reinit()
        self.clear_full()

    def clear_full(self, color=1):
        self.partial_mode_off()
        self.fill(self.white)
        self.show()

    def display_partial(self, image_buffer):
        if not self._partial:
            self.partial_mode_on()
        if self._buffer_bw is not image_buffer:
            self._buffer_bw[:] = image_buffer
        self.show()

    def _pio_setup(self):
        from rp2 import asm_pio, PIO, StateMachine

        @asm_pio(out_init=PIO.OUT_LOW, sideset_init=PIO.OUT_LOW,
                 autopull=True, pull_thresh=8, out_shiftdir=PIO.SHIFT_LEFT)
        def pio_serial_tx():
            out(pins, 1).side(0)
            nop().side(1)

        self._sm = StateMachine(self._sm_num, pio_serial_tx, freq=40_000_000,
                                sideset_base=Pin(10), out_base=Pin(11))
        self._sm.active(1)

    def _reversed_output(self):
        self.mem32[self._sm_shiftctrl + 0x2000] = 1 << 19

    def _normal_output(self):
        self.mem32[self._sm_shiftctrl + 0x3000] = 1 << 19

    def _wait_pio_idle(self):
        from machine import mem32
        from utime import ticks_ms, ticks_diff, sleep_us
        start = ticks_ms()
        # Warten bis TX FIFO leer ist (Bit 24..27 je nach SM)
        while not ((mem32[self._fstat] >> self._txempty_bit) & 1):
            if hasattr(self, 'wdt') and self.wdt:
                self.wdt.feed()
            if ticks_diff(ticks_ms(), start) > 1000:
                print("[ERROR][EPD] PIO idle timeout! Resetting...")
                self._reset()
                break
        sleep_us(100)

    def _send_command(self, command):
        self._dc(0)
        self._cs(0)
        if isinstance(command, int):
            self._sm.put(command, 24)
        elif isinstance(command, (bytes, bytearray)):
            for b in command:
                self._sm.put(b, 24)
        self._wait_pio_idle()
        self._cs(1)

    def _send_data(self, data):
        self._dc(1)
        self._cs(0)
        if isinstance(data, int):
            self._sm.put(data, 24)
        elif isinstance(data, (bytes, bytearray)):
            for b in data:
                self._sm.put(b, 24)
        self._wait_pio_idle()
        self._cs(1)

    @micropython.viper
    def _dma_start(self, buffer):
        dma_ptr = ptr32(self._dma)
        dma_ptr[0] = int(self._dma_ctrl)
        dma_ptr[1] = int(self._dma_write_addr)
        dma_ptr[2] = int(len(buffer))
        dma_ptr[3] = int(ptr32(buffer))

    @micropython.viper
    def _check_dma_busy(self, a: ptr32, shift: int) -> int:
        return (a[0] >> shift) & 1

    def _send_buffer(self, buffer):
        if self._horizontal:
            self._reversed_output()

        self._dc(1)
        self._cs(0)

        # Byte-fuer-Byte per PIO (kein DMA, kein WiFi-Konflikt)
        sm_put = self._sm.put
        if self._horizontal:
            # Reverse mode (right-shift): Daten an Bits 0-7
            for b in buffer:
                sm_put(b, 0)
        else:
            # Normal mode (left-shift): Daten an Bits 24-31
            for b in buffer:
                sm_put(b, 24)

        self._wait_pio_idle()
        self._cs(1)

        if self._horizontal:
            self._normal_output()

    def show(self, lut=0):
        super().show(lut)
        self._send_command(0x24)
        self._send_buffer(self._buffer_bw)

        if self._partial:
            self._load_LUT(2)
        else:
            self._send_command(0x26)
            self._send_buffer(self._buffer_red)
            self._load_LUT(lut)

        self._send_command(0x20)
        self._read_busy()


