from emulate import emulator
import ctypes
import time

Emulator = emulator()
user32 = ctypes.windll.user32

while True:
    time.sleep(1)
    VK_HANGUL = 0x15
    user32.keybd_event(VK_HANGUL, 0, 0, 0)      # Press
    time.sleep(0.05)
    user32.keybd_event(VK_HANGUL, 0, 0x0002, 0) # Release