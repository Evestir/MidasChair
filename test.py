from emulate import emulator
import ctypes
import time
from sqlite import sqlite

Emulator = emulator()
user32 = ctypes.windll.user32
Sqlite = sqlite()

Sqlite.deleteWords(["쁨"])

exit()
while True:
    time.sleep(1)
    VK_HANGUL = 0x15
    user32.keybd_event(VK_HANGUL, 0, 0, 0)      # Press
    time.sleep(0.05)
    user32.keybd_event(VK_HANGUL, 0, 0x0002, 0) # Release