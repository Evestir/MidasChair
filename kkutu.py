from jamo import h2j, j2hcj, j2h
from sqlite import sqlite
from config import Config
from loguru import logger
from modes import Modes, WordSelModes
import random

class kkutu:
    def __init__(self):
        self.Sqlite = sqlite()
        self.history = [] # should be tuples (word, ack)
        self.failed = []
        self.acks = []
        self.hanbangs = []
        self.foundWords = []
        self.updateUI = None

    def isFirstTime(self, word):
        usedWords = [tup[0] for tup in self.history]
        return word not in usedWords

    def chooseWord(self, starting_letter:str, roomSettings):
        words = self.findWords(starting_letter, roomSettings)
        if words == "pass":
            return "pass"
        self.foundWords = words
        if self.updateUI:
            self.updateUI()
        if not words:
            return None
        logger.debug(f"Found {len(words)} Word(s).")
        suggestedWord = None
        if Config.wordSelMode == WordSelModes.longest:
            suggestedWord = words[0]
        elif Config.wordSelMode == WordSelModes.random:
            suggestions = []
            for word in words:
                if len(word) <= Config.maxWordLength:
                    suggestions.append(word)
            if suggestions:
                suggestedWord = random.choice(suggestions)
        return suggestedWord

    def findWords(self, starting_letter: str, roomSettings):
        words = []
        jm = list(j2hcj(h2j(starting_letter)))
        if jm[0] in ['ㄹ', 'ㄴ']:
            """두음법칙 적용"""
            if jm[1] in ['ㅑ', 'ㅕ', 'ㅖ', 'ㅛ', 'ㅠ', 'ㅣ']: # 롬, 랙, 롬
                jm[0] = 'ㅇ'
            elif jm[1] in ['ㅏ', 'ㅐ', 'ㅗ', 'ㅚ','ㅜ', 'ㅡ']:
                jm[0] = 'ㄴ'
            former = starting_letter
            latter = j2h(*jm)
            chars = [latter, former]
            for i in range(2):
                words = self.Sqlite.getWords(chars[i], roomSettings.ack, roomSettings.manner)
                if words:
                    words = [word for word in words if self.isFirstTime(word) and not word in self.failed and not word in self.hanbangs]
                    break
        else:
            words = self.Sqlite.getWords(starting_letter, roomSettings.ack, roomSettings.manner)
            if not words:
                return words
            words = [word for word in words if self.isFirstTime(word) and not word in self.failed and not word in self.hanbangs]
        return words
    
    def markUsed(self, tup: tuple):
        if tup and tup not in self.history:
            self.history.append(tup)
            return True
    
    def reset(self):
        self.history = []
        self.failed = []
        self.hanbangs = []

    def updateDatabase(self):
        self.Sqlite.addTuples(self.history)
        self.Sqlite.deleteWords(self.failed)
        self.Sqlite.markHanbang(self.hanbangs)

Kkutu = kkutu()