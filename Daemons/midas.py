from selenium.webdriver.common.by import By
from state import States, TurnPhase
from emulate import emulator
from Daemons.midas import watchdog
from sqlite import sqlite
from config import Config
from loguru import logger
from config import Modes
from kkutu import Kkutu
import threading
import time 

class Midas:
    def __init__(self, driver):
        self.is_running = False
        self.driver = driver
        self.Sqlite = None
        self.Emulator = None
        self.Watchdog = None

        """UI Vars"""
        self.name = ""
        self.inputField = None
        self.cCField = None
        """Pre Game Vars"""
        self.roomSettings = None
        self.players = []
        self.playerCount = 0
        self.roundChars = []
        self.myTurn = 0
        self.rounds = 0
        self.currentRound = 0
        """In Game Vars"""
        self.turnPhase = TurnPhase.WAIT
        self.suggestedWord = None
        self.chosenWord = None

    def run(self):
        self.driver.get("https://kkutu.io/")
        self.Watchdog = watchdog(self.driver)
        self.Sqlite = sqlite()
        self.Emulator = emulator()
        self.Watchdog.start_listening()

        while self.is_running:
            time.sleep(Config.sleepTime)
            event = self.Watchdog.getEvent()
            if event:
                eventType = event["type"]
                if eventType == "INIT_DATA":
                    self.name = event["name"]
                    self.inputField = event["inputField"]
                    logger.debug(f"Received INIT_DATA, Name: {self.name}")
                elif eventType == "PRE_GAME_DATA":
                    self.players = event["players"]
                    self.playerCount = event["playerCount"]
                    self.cCField = event["cCField"]
                    self.roundChars = event["roundChars"]
                    self.myTurn = event["myTurn"]
                    self.rounds = event["rounds"]
                    self.roomSettings = event["roomSettings"]
                    logger.debug(f"Player Count: {self.playerCount}, Rounds: {self.rounds}, My Turn: {self.myTurn}, Acknowledged: {self.roomSettings.ack}, Manner: {self.roomSettings.manner}")
                elif eventType == "ROUND_CHANGE":
                    self.currentRound == event["currentRound"]
                    logger.debug(f"Round Changed: {self.currentRound}")
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
                            continue
                        self.Emulator.type(self.inputField, Config.GG)
            
            gameStates = self.Watchdog.retreive()
            if gameStates.state == States.lobby:
                Kkutu.reset()
            elif gameStates.state == States.in_game:
                """Timing Issue Fix"""
                if not self.players:
                    continue
                """Checking if it's my turn and if the last attempt was a failure"""
                if self.Watchdog.isMyTurn():
                    if self.turnPhase == TurnPhase.TYPED and suggestedWord:
                        try:
                            element = self.cCField.find_element(By.CSS_SELECTOR, ".game-fail-text")
                            text = element.get_attribute("textContent").strip()
                            if "한방 단어:" in text:
                                Kkutu.hanbangs.append(suggestedWord)
                                logger.error(f"{suggestedWord} is a hanbang word.")
                            else:
                                Kkutu.failed.append(suggestedWord)
                                if self.roomSettings.ack:
                                    logger.error(f"{suggestedWord} is not a valid word.")
                                else:
                                    logger.error(f"{suggestedWord} is not a valid or acknowledged word.")
                        except Exception as e:
                            #logger.error("Probably just an internet lag..")
                            if not Config.killSwitch:
                                self.turnPhase = TurnPhase.WAIT
                            continue
                        self.turnPhase = TurnPhase.ERROR
                    else:
                        if self.turnPhase == TurnPhase.NO_WORD:
                            ch = self.cCField.text.strip()
                            if ch and len(ch) != 1 and not '(' in ch:
                                Kkutu.markUsed((ch, False))
                                logger.debug(f"Added {ch} to history just in case this word is not on the database.")
                        self.turnPhase = TurnPhase.SHOULD_TYPE
                elif (gameStates.turn + 1) % self.playerCount == self.myTurn:
                    if Config.PREDICT:
                        self.turnPhase = TurnPhase.SHOULD_PREDICT
                else:
                    if self.turnPhase == TurnPhase.NO_WORD:
                        logger.info("Somehow my turn was passed even though I couldn't fetch a word.")
                        ch = self.cCField.text.strip()
                        if ch:
                            Kkutu.markUsed((ch, False))
                            logger.debug(f"Added {ch} to history just in case this word is not on the database.")
                        self.turnPhase = TurnPhase.WAIT
                    elif self.turnPhase == TurnPhase.TYPED:
                        if suggestedWord:
                            logger.success(f"Confirmed that my turn was passed.")
                        self.turnPhase = TurnPhase.WAIT
                    

                """Typing begins here"""
                if self.turnPhase == TurnPhase.SHOULD_TYPE or self.turnPhase == TurnPhase.ERROR:
                    displayedChar = self.cCField.text.strip()
                    if self.turnPhase == TurnPhase.ERROR:
                        displayedChar = suggestedWord[0]
                    """Check if the prediction was right"""
                    if Config.MODE != Modes.blatant:
                        typedWord = self.inputField.get_attribute("value").strip()
                        if typedWord:
                            if typedWord[0] == displayedChar:
                                logger.success(f"Prediction was correct")
                                self.Emulator.enter()
                            else:
                                self.Emulator.flush(self.inputField)
                    """Find word"""
                    suggestedWord = Kkutu.chooseWord(displayedChar, self.roomSettings)
                    if suggestedWord:
                        if suggestedWord == "pass": # When the animations is playing right after you successfully typed a word.
                            self.turnPhase = TurnPhase.WAIT
                            continue
                        if not Config.killSwitch:
                            self.Emulator.type(self.inputField, suggestedWord)
                    else:
                        logger.error(f"No words found for '{displayedChar}'")
                        self.turnPhase = TurnPhase.NO_WORD
                        continue
                    self.turnPhase = TurnPhase.TYPED
                elif self.turnPhase == TurnPhase.SHOULD_PREDICT:
                    """Check if something is already typed"""
                    if self.inputField.get_attribute("value"):
                        continue
                    """For Blatant Opponents"""
                    displayedChar = self.cCField.text.strip()
                    predictedWord = Kkutu.chooseWord(displayedChar, self.roomSettings)
                    if not predictedWord:
                        logger.error(f"No words found for '{displayedChar}'")
                        self.turnPhase = TurnPhase.NO_WORD
                        continue
                    logger.debug(f"Predicted: {predictedWord}")
                    suggestedWord = Kkutu.chooseWord(predictedWord[-1], self.roomSettings)
                    if not suggestedWord:
                        logger.error(f"No words found for '{predictedWord[-1]}'")
                        self.turnPhase = TurnPhase.NO_WORD
                        continue
                    if suggestedWord == "pass":
                        self.turnPhase = TurnPhase.WAIT
                        continue
                    self.Emulator.type(self.inputField, suggestedWord, enter = False)
    def start_running(self):
        if not self.is_running:
            t = threading.Thread(target=self.run)
            t.daemon = True
            t.start()
            self.is_running = True
            logger.info("Midas thread initiated.")
    
    def stop_running(self):
        self.Watchdog.stop_listening()
        self.is_running = False
        logger.info("Midas thread stopped.")