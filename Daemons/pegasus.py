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
                    self.Watchdog.lastWord = ''
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
                if self.Watchdog.isMyTurn:
                    if self.turnPhase == TurnPhase.SHOULD_TYPE:
                        if not self.Watchdog.lastWord:
                            char = self.Watchdog.cCField.get_attribute("textContent").replace('\n', '').strip()[0]
                        else:
                            char = self.Watchdog.lastWord[-1]
                        # Finding words...
                        self.suggestedWord = Kkutu.chooseWord(char, self.Watchdog.roomSettings)
                        if self.suggestedWord:
                            if Config.autoType:
                                self.Emulator.type(self.Watchdog.inputField, self.suggestedWord, enter=False)
                                while not self.Watchdog.fIsMyTurn(): # Milisec precision?
                                    time.sleep(0.0001)
                                self.Emulator.enter(self.Watchdog.inputField)
                            else:
                                while self.Watchdog.isMyTurn:
                                    if not self.Watchdog.fIsMyTurn():
                                        if self.Watchdog.turn is not None:
                                            nextPlayer = (self.Watchdog.turn + 1) % self.Watchdog.playerCount
                                            if self.Watchdog.myTurn == nextPlayer:
                                                pass
                                            else:
                                                break
                                    time.sleep(0.1)
                                    if self.chosenWord:
                                        if Config.MODE == Modes.legit:
                                            self.Emulator.altTab()
                                            time.sleep(0.3)
                                            self.IME.forceHangul()
                                        self.Emulator.type(self.Watchdog.inputField, self.chosenWord)
                                        break
                            self.turnPhase = TurnPhase.TYPED
                        else:
                            logger.error(f"No words starting with '{char}'")
                            self.turnPhase = TurnPhase.NO_WORD

                    elif self.turnPhase == TurnPhase.TYPED:
                        if not self.Watchdog.fIsMyTurn(): # Checking if the last word got passed...
                            with self.Watchdog.lock:
                                self.Watchdog.isMyTurn = False
                                self.Watchdog.lastWord = self.suggestedWord
                            self.suggestedWord = None
                            self.chosenWord = None
                            self.turnPhase = TurnPhase.WAIT
                            logger.success("Passed my turn")
                        try: # If my turn was not passed:
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
                            self.turnPhase = TurnPhase.SHOULD_TYPE
                        except Exception as e:
                            # When internet is too slow to quickly hide the viewInput element
                            self.turnPhase = TurnPhase.WAIT
                            continue
                    elif self.turnPhase == TurnPhase.NO_WORD:
                        pass
                    else:
                        self.turnPhase = TurnPhase.SHOULD_TYPE

                else:
                    if self.turnPhase == TurnPhase.NO_WORD:
                        displayedWord = self.Watchdog.cCField.text.strip()
                        if displayedWord and len(displayedWord) > 1:
                            Kkutu.markUsed((displayedWord, False))
                            logger.debug(f"Added {displayedWord} to history just in case this word is not on the database.")
                    elif self.turnPhase == TurnPhase.TYPED:
                        if self.suggestedWord or self.chosenWord:
                            logger.success(f"Confirmed that my turn was passed.")
                    self.suggestedWord = None
                    self.chosenWord = None
                    self.turnPhase = TurnPhase.WAIT
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
        logger.warning("Bye :)")