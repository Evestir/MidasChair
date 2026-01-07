from jamo import h2j, j2hcj
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from loguru import logger
from config import Config
from modes import Modes
import platform
import pyautogui
import random
import time

pyautogui.PAUSE = 0 
class emulator:
    def __init__(self):
        """쿼티 키보드 매핑"""
        self.key_map = {
            # 자음
            'ㄱ': 'r', 'ㄲ': 'R', 'ㄴ': 's', 'ㄷ': 'e', 'ㄸ': 'E', 'ㄹ': 'f',
            'ㅁ': 'a', 'ㅂ': 'q', 'ㅃ': 'Q', 'ㅅ': 't', 'ㅆ': 'T', 'ㅇ': 'd',
            'ㅈ': 'w', 'ㅉ': 'W', 'ㅊ': 'c', 'ㅋ': 'z', 'ㅌ': 'x', 'ㅍ': 'v', 'ㅎ': 'g',
            
            # 모음
            'ㅏ': 'k', 'ㅐ': 'o', 'ㅑ': 'i', 'ㅒ': 'O', 'ㅓ': 'j',
            'ㅔ': 'p', 'ㅕ': 'u', 'ㅖ': 'P', 'ㅗ': 'h', 'ㅘ': 'hk',
            'ㅙ': 'ho', 'ㅚ': 'hl', 'ㅛ': 'y', 'ㅜ': 'n', 'ㅝ': 'nj',
            'ㅞ': 'np', 'ㅟ': 'nl', 'ㅠ': 'b', 'ㅡ': 'm', 'ㅢ': 'ml',
            'ㅣ': 'l',
            
            # 겹받침
            'ㄳ': 'rt', 'ㄵ': 'sw', 'ㄶ': 'sg', 'ㄺ': 'fr', 'ㄻ': 'fa',
            'ㄼ': 'fq', 'ㄽ': 'ft', 'ㄾ': 'fx', 'ㄿ': 'fv', 'ㅀ': 'fg',
            'ㅄ': 'qt'
        }

    def _decompose_text(self, word):
        jamo_str = j2hcj(h2j(word))
        keystrokes = []

        for char in jamo_str:
            if char in self.key_map:
                """Is Korean"""
                keystrokes.extend(self.key_map[char])
            else:
                keystrokes.append(char)
        return keystrokes

    def type(self, inputField, word, speed = 0.04, enter = True):
        inputField.click()
        if Config.MODE == Modes.blatant:
            keyStrokes = [word]
            speed = 0
        elif Config.MODE == Modes.semiBlatant:
            keyStrokes = [ch for ch in word]
        elif Config.MODE == Modes.legit:
            keyStrokes = self._decompose_text(word)
        for key in keyStrokes:
            if Config.MODE == Modes.blatant or Config.MODE == Modes.semiBlatant:
                inputField.send_keys(key)
            elif Config.MODE == Modes.legit:
                if key.isupper():
                    with pyautogui.hold("shift"):
                        pyautogui.write(key.lower())
                else:
                    pyautogui.write(key)
            factor = speed/2
            minDelay = speed - factor
            maxDelay = speed + factor
            time.sleep(random.uniform(minDelay, maxDelay))
        if enter:
            if Config.MODE == Modes.blatant or Config.MODE == Modes.semiBlatant:
                inputField.send_keys(Keys.RETURN)
            elif Config.MODE == Modes.legit:
                pyautogui.press("enter")
        
    def flush(self, inputField):
        inputField.click()
        modifier = 'command' if platform.system() == 'Darwin' else 'ctrl'
        pyautogui.hotkey(modifier, 'a')
        time.sleep(0.05)
        pyautogui.hotkey(modifier, 'a')
        pyautogui.press('backspace')

        """To fix ghosting"""
        time.sleep(0.1)
        pyautogui.hotkey(modifier, 'a')
        pyautogui.press('backspace')

    def escape(self, driver):
        try: 
            body = driver.find_element(By.TAG_NAME, "body")
            body.send_keys(Keys.ESCAPE)
        except Exception as e:
            logger.error(f"Failed to escape: {e}")

    def enter(self, inputField):
        inputField.send_keys(Keys.RETURN)

    def altTab(self):
        pyautogui.hotkey('alt', 'tab')

    def hangulkey(self):
        pyautogui.press("ralt")