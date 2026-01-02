from sqlite import sqlite
from config import Config
from loguru import logger
from modes import Modes
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
        self.updateUI()
        if not words:
            return None
        logger.debug(f"Found {len(words)} Words. Choosing words based on MODE: {Config.MODE}")
        suggestedWord = None
        if Config.MODE == Modes.blatant:
            suggestedWord = words[0]
            logger.debug(f"Suggested: {suggestedWord}")
        elif Config.MODE == Modes.legit or Config.MODE == Modes.semiBlatant:
            suggestions = []
            for word in words:
                if len(word) <= Config.maxWordLength:
                    suggestions.append(word)
            if suggestions:
                suggestedWord = random.choice(suggestions)
        return suggestedWord

    def findWord(self, starting_letter: str, roomSettings, mode):
        suggestedWord = None
        if '(' in starting_letter:
            if len(starting_letter) > 4:
                return "pass"
            """두음법칙 적용"""
            former = starting_letter[0]
            latter = starting_letter[2]
            words = self.Sqlite.getWords(latter, roomSettings.ack, roomSettings.manner)
            if words:
                suggestedWord = self.chooseWord(words, mode)
            if not suggestedWord:
                words = self.Sqlite.getWords(former, roomSettings.ack, roomSettings.manner)
                if words:
                    suggestedWord = self.chooseWord(words, mode)
        else:
            if len(starting_letter) > 1:
                return "pass"
            words = self.Sqlite.getWords(starting_letter, roomSettings.ack, roomSettings.manner)
            if not words:
                return None
            logger.debug(f"Found {len(words)} Words")
            suggestedWord = self.chooseWord(words, mode)
        return suggestedWord

    def findWords(self, starting_letter: str, roomSettings):
        words = []
        if '(' in starting_letter:
            if len(starting_letter) > 4:
                return "pass"
            """두음법칙 적용"""
            former = starting_letter[0]
            latter = starting_letter[2]
            words = self.Sqlite.getWords(latter, roomSettings.ack, roomSettings.manner)
            if words:
                words = [word for word in words if self.isFirstTime(word) and not word in self.failed and not word in self.hanbangs]
            if not words:
                words = self.Sqlite.getWords(former, roomSettings.ack, roomSettings.manner)
                if words:
                    words = [word for word in words if self.isFirstTime(word) and not word in self.failed and not word in self.hanbangs]
        else:
            if len(starting_letter) > 1:
                return "pass"
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
        logger.info("Updated Database")


Kkutu = kkutu()