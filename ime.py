from loguru import logger
import time
import pyautogui
import platform
system = platform.system()
if system == "Windows":
    import ctypes
    imm32 = ctypes.WinDLL('imm32', use_last_error=True)
    user32 = ctypes.WinDLL('user32', use_last_error=True)


class IME:
    def __init__(self):
        logger.debug(f"System: {system}")

    def isHangul(self):
        if system == "Windows":
            hwnd = user32.GetForegroundWindow()
            if not hwnd:
                return False
            length = user32.GetWindowTextLengthW(hwnd)
            buff = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buff, length + 1)
            #logger.debug(f"Window Name: {buff.value}")
            hime = imm32.ImmGetContext(hwnd)
            if not hime:
                return False
            conversion_status = ctypes.c_ulong()
            sentence_mode = ctypes.c_ulong()
            imm32.ImmGetConversionStatus(
                hime, 
                ctypes.byref(conversion_status), 
                ctypes.byref(sentence_mode)
            )
            imm32.ImmReleaseContext(hwnd, hime)
            return (conversion_status.value & 0x1) != 0

    def forceHangul(self):
        """Checks if English, and presses the Hangul key if needed."""
        if not self.isHangul():
            logger.debug("Switching to Korean IME")
            VK_HANGUL = 0x15
            user32.keybd_event(VK_HANGUL, 0, 0, 0)
            time.sleep(0.05)
            user32.keybd_event(VK_HANGUL, 0, 0x0002, 0)