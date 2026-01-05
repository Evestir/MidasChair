from Daemons.Pegasus.watchdog import Watchdog
from selenium.webdriver.common.by import By
from state import States, TurnPhase
from ime import IME
from emulate import emulator
from sqlite import sqlite
from config import Config
from loguru import logger
from config import Modes
from kkutu import Kkutu
import threading
import time 

class Pegasus:
    def __init__(self, driver):
        self.is_running = False
        self.driver = driver
        self.Sqlite = None
        self.Emulator = None
        self.Watchdog = None

        """Pre Game Vars"""
        self.rounds = 0
        """In Game Vars"""
        self.turnPhase = TurnPhase.WAIT
        self.suggestedWord = None
        self.chosenWord = None

    def run(self):
        self.driver.get("https://kkutu.co.kr/")
        self.Watchdog = Watchdog(self.driver)
        self.Sqlite = sqlite()
        self.Emulator = emulator()
        self.IME = IME()
        self.Watchdog.start_listening()

        while self.is_running:
            time.sleep(Config.sleepTime)
            event = self.Watchdog.getEvent()
            if event:
                eventType = event["type"]
                if eventType == "ROUND_CHANGE":
                    logger.debug(f"Round Changed: {self.Watchdog.currentRound + 1}")
                    Kkutu.updateDatabase()
                    Kkutu.reset()
                    self.turnPhase = TurnPhase.WAIT
                elif eventType == "GAME_ENDED":
                    logger.warning("Gamed Ended")
                    Kkutu.updateDatabase()
                    Kkutu.reset()
                    if Config.GG:
                        try:
                            for i in range(2):
                                exitBtn = self.driver.find_element(By.ID, "result-ok")
                                exitBtn.click()
                                time.sleep(0.2)
                        except Exception as e:
                            pass
                        self.Emulator.type(self.inputField, Config.GG)

            if self.Watchdog.state == States.lobby:
                Kkutu.reset()
            elif self.Watchdog.state == States.in_game:
                """Timing Issue Fix"""
                if not self.Watchdog.players:
                    continue
                """Checking if it's my turn and if the last attempt was a failure"""
                if self.Watchdog.isMyTurn():
                    if self.turnPhase == TurnPhase.TYPED and (self.suggestedWord or self.chosenWord) or self.turnPhase == TurnPhase.ERROR: # Unnecessary () however... 
                        try:
                            if self.turnPhase == TurnPhase.ERROR:
                                raise ValueError("Intentional Error")
                            element = self.Watchdog.cCField.find_element(By.CSS_SELECTOR, ".game-fail-text")
                            text = element.get_attribute("textContent").strip()
                            if "한방 단어:" in text:
                                if self.chosenWord:
                                    self.suggestedWord = self.chosenWord
                                    self.chosenWord = None
                                Kkutu.hanbangs.append(self.suggestedWord)
                                logger.error(f"{self.suggestedWord} is a hanbang word.")
                                self.suggestedWord = None
                            else:
                                if self.chosenWord:
                                    self.suggestedWord = self.chosenWord
                                    self.chosenWord = None
                                Kkutu.failed.append(self.suggestedWord)
                                if self.Watchdog.roomSettings.ack:
                                    logger.error(f"{self.suggestedWord} is not a valid word.")
                                else:
                                    logger.error(f"{self.suggestedWord} is not a valid or acknowledged word.")
                        except Exception as e:
                            #logger.error("Probably just an internet lag..")
                            if Config.killSwitch:
                                if self.chosenWord:
                                    if Config.MODE == Modes.legit:
                                        self.Emulator.altTab()
                                        time.sleep(0.3)
                                        self.IME.forceHangul()
                                    self.Emulator.type(self.Watchdog.inputField, self.chosenWord)
                                    self.turnPhase = TurnPhase.TYPED
                            else:
                                self.turnPhase = TurnPhase.WAIT
                            continue
                        self.turnPhase = TurnPhase.ERROR
                    elif self.turnPhase == TurnPhase.NO_WORD:
                        pass
                    else:
                        self.turnPhase = TurnPhase.SHOULD_TYPE
                elif (self.Watchdog.turn + 1) % self.Watchdog.playerCount == self.Watchdog.myTurn:
                    if Config.PREDICT:
                        self.turnPhase = TurnPhase.SHOULD_PREDICT
                else:
                    if self.turnPhase == TurnPhase.NO_WORD:
                        logger.info("The last round was ended...")
                        displayedWord = self.Watchdog.cCField.text.strip()
                        if displayedWord:
                            Kkutu.markUsed((displayedWord, False))
                            logger.debug(f"Added {displayedWord} to history just in case this word is not on the database.")
                        self.turnPhase = TurnPhase.WAIT
                    elif self.turnPhase == TurnPhase.TYPED:
                        if self.suggestedWord or self.chosenWord:
                            logger.success(f"Confirmed that my turn was passed.")
                        self.turnPhase = TurnPhase.WAIT
                        self.suggestedWord = None
                        self.chosenWord = None
                    
                """Typing begins here"""
                if self.turnPhase == TurnPhase.SHOULD_TYPE or self.turnPhase == TurnPhase.ERROR:
                    displayedChar = self.Watchdog.cCField.text.strip()
                    if self.turnPhase == TurnPhase.ERROR:
                        displayedChar = self.suggestedWord[0]
                    """Check if the prediction was right"""
                    if Config.MODE != Modes.blatant:
                        typedWord = self.Watchdog.inputField.get_attribute("value").strip()
                        if typedWord:
                            if not Config.killSwitch:
                                if typedWord[0] == displayedChar:
                                    logger.success(f"Prediction was correct")
                                    self.Emulator.enter()
                                else:
                                    self.Emulator.flush(self.Watchdog.inputField)
                    """Find word"""
                    self.suggestedWord = Kkutu.chooseWord(displayedChar, self.Watchdog.roomSettings)
                    if self.suggestedWord:
                        if self.suggestedWord == "pass": # When the animations is playing right after you successfully typed a word.
                            self.turnPhase = TurnPhase.WAIT
                            continue
                        if not Config.killSwitch:
                            self.Emulator.type(self.Watchdog.inputField, self.suggestedWord)
                    else:
                        logger.error(f"No words found for '{displayedChar}'")
                        self.turnPhase = TurnPhase.NO_WORD
                        continue
                    if self.turnPhase == TurnPhase.ERROR and Config.killSwitch:
                        continue
                    self.turnPhase = TurnPhase.TYPED
                elif self.turnPhase == TurnPhase.SHOULD_PREDICT:
                    """Check if something is already typed"""
                    if self.Watchdog.inputField.get_attribute("value"):
                        continue
                    """For Blatant Opponents"""
                    displayedChar = self.Watchdog.cCField.text.strip()
                    predictedWord = Kkutu.chooseWord(displayedChar, self.Watchdog.roomSettings)
                    if not predictedWord:
                        logger.error(f"No words found for '{displayedChar}'")
                        self.turnPhase = TurnPhase.NO_WORD
                        continue
                    logger.debug(f"Predicted: {predictedWord}")
                    self.suggestedWord = Kkutu.chooseWord(predictedWord[-1], self.Watchdog.roomSettings)
                    if not self.suggestedWord:
                        logger.error(f"No words found for '{predictedWord[-1]}'")
                        self.turnPhase = TurnPhase.NO_WORD
                        continue
                    if self.suggestedWord == "pass":
                        self.turnPhase = TurnPhase.WAIT
                        continue
                    self.Emulator.type(self.Watchdog.inputField, self.suggestedWord, enter = False)
    def start_running(self):
        if not self.is_running:
            t = threading.Thread(target=self.run)
            t.daemon = True
            t.start()
            self.is_running = True
            logger.info("Pegasus thread initiated.")
    
    def stop_running(self):
        self.Watchdog.stop_listening()
        self.is_running = False
        logger.info("Pegasus thread stopped.")