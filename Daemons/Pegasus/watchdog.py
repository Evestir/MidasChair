from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.by import By
from collections import namedtuple
from modes import RoomSettings
from loguru import logger
from state import States
from kkutu import Kkutu
import threading
import queue
import time

def getRoundElements(self):
    elements = self.driver.find_elements(By.CSS_SELECTOR, "div.rounds > *")
    return elements

def getCurrentRound(self):
    if not self.roundElements:
        self.roundElements = self._failSafe(getRoundElements)
        self.rounds = len(self.roundElements)

    """Check if it's still valid"""
    try:
        self.roundElements[0].is_enabled()
    except StaleElementReferenceException:
        self.roundElements = self._failSafe(getRoundElements)
        #logger.debug("roundElements are not valid anymore.")
    currentRound = -1
    for i, child in enumerate(self.roundElements):
        if child.get_attribute("class") == "rounds-current":
            currentRound = i
    return currentRound

def getcCField(self):
    element = self.driver.find_element(By.CSS_SELECTOR, ".jjo-display.ellipse")
    return element
        
def getInput(self):
    inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[id^='UserMassage']")
    for inp in inputs:
        style = inp.get_attribute("style")
        if style and "float: left" in style and "border-top-right-radius" in style:
            return inp

def getViewInput(self):
    element = self.driver.find_element(By.CSS_SELECTOR, ".game-input")
    return element

def getPracticeBtn(self):
    btn = self.driver.find_element(By.ID, "PracticeBtn")
    return btn

def getRoomSettings(self):
    elements = self.driver.find_elements(By.CSS_SELECTOR, ".room-head-mode")
    text = elements[0].get_attribute("textContent")
    ack = "어인정" in text
    manner = "매너" in text
    return RoomSettings(ack=ack, manner=manner)

def fetchHistory(self):
    history = []
    historyItems = self.driver.find_elements(By.CSS_SELECTOR, ".history-item.expl-mother")
    for element in historyItems:
        word = element.get_attribute("innerHTML")
        if word:
            word = word.split('<')[0].strip()
        else:
            continue
        acked = "word-injeong" in element.get_attribute("innerHTML")
        history.append((word, acked))
    return history
    
def updateHistory(self):
    updated = False
    history = fetchHistory(self)
    for tup in history:
        if Kkutu.markUsed(tup) and not updated:
            updated = True
    if updated: logger.debug(f"Added {Kkutu.history[-1]} to history")

def getState(self):
    state = self.state
    if self.state == States.title:
        elements = self.driver.find_elements(By.ID, "ReplayBtn")
        if elements:
            state = States.lobby
            self.replayBtn = elements[0]
    elif self.state == States.lobby:
        if self.practiceBtn.is_displayed():
            state = States.game_lobby
    elif self.state == States.game_lobby:
        if not self.practiceBtn.is_displayed():
            state = States.pre_game
    elif self.state == States.pre_game:
        placeholder = self.cCField.text
        if placeholder and placeholder != "잠시 후 게임이 시작됩니다!":
            state = States.in_game
    elif self.state == States.in_game or self.state == States.end_screen:
        if self.practiceBtn.is_displayed():
            state = States.lobby
    if state is not self.state:
        logger.debug(f"Game State: {state.name}")
    return state
    
def getMyName(self):
    element = self.driver.find_element(By.CSS_SELECTOR, ".my-stat-name.ellipse")
    name = element.get_attribute("textContent").strip()
    return name

def getMyTurn(self):
    for i, player in enumerate(self.players):
        element = player.find_element(By.CSS_SELECTOR, ".game-user-title.expl-mother")
        child = element.find_element(By.CSS_SELECTOR, ".game-user-name.ellipse")
        name = child.get_attribute("textContent").strip()
        if self.name == name:
            return i

def getTurn(self):
    for i, player in enumerate(self.players):
        class_val = player.get_attribute("class")
        if class_val and "game-user-current" in class_val:
            return i
    return self.turn

def getPlayers(self):
    while True:
        players = self.driver.find_elements(By.CSS_SELECTOR, ".game-body > *")
        if players: break
    return players

def getEndDialog(self):
    dialog = self.driver.find_element(By.CSS_SELECTOR, ".dialog.dialog-front")
    return dialog

def isEnded(self):
    endDialog = self._failSafe(getEndDialog)
    if endDialog:
        if endDialog.is_displayed():
            return True
    return False

gameStates = namedtuple('gameStates', ['state', 'turn'])

class Watchdog:
    def __init__(self, driver):
        self.driver = driver
        self.is_running = False
        self.lock = threading.Lock()
        self.event_queue = queue.Queue()

        """lobby (events)"""
        self.name = ""
        self.inputField = None
        self.replayBtn = None

        """in_game (events)"""
        self.players = []
        self.playerCount = 0
        self.currentRound = 0
        self.rounds = 0
        self.roundElements = None
        self.cCField = None
        self.viewInput = None
        self.practiceBtn = None
        self.roomSettings = None
        """typing mechanisms (states)"""
        self.state = States.title
        self.turn = 0
        self.myTurn = 0

    def _failSafe(self, function, timeout=2.0, interval=0.05):
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                res = function(self)
                if res is not None:
                    return res
            except Exception:
                pass
            time.sleep(interval)
        logger.error(f"Failsafe triggered for {function}")
        return None

    def _watchdog(self):
        while self.is_running:
            time.sleep(0.05)
            try:
                state = getState(self)
                with self.lock:
                    self.state = state
                if self.state == States.lobby:
                    if self.players:
                        with self.lock:
                            self.players = []
                            self.roundElements = None
                            self.turn = 0
                    if not self.inputField:
                        with self.lock:
                            self.inputField = self._failSafe(getInput)
                    if not self.cCField:
                        with self.lock:
                            self.cCField = self._failSafe(getcCField)
                    if not self.practiceBtn:
                        with self.lock:
                            self.practiceBtn = self._failSafe(getPracticeBtn)
                    if not self.name:
                        with self.lock:
                            self.name = self._failSafe(getMyName)
                elif self.state == States.pre_game:
                    if not self.players:
                        with self.lock:
                            self.players = self._failSafe(getPlayers)
                            self.playerCount = len(self.players)
                            self.viewInput = self._failSafe(getViewInput)
                            self.myTurn = self._failSafe(getMyTurn)
                            self.roomSettings = self._failSafe(getRoomSettings)
                        logger.debug(f"Player Count: {self.playerCount}, My Turn: {self.myTurn}, Acknowledged: {self.roomSettings.ack}, Manner: {self.roomSettings.manner}")
                elif self.state == States.in_game:
                    if isEnded(self):
                        self.event_queue.put({"type": "GAME_ENDED"})
                        with self.lock:
                            self.state = States.end_screen
                        continue
                    updateHistory(self)
                    currentRound = getCurrentRound(self)
                    if self.currentRound != currentRound:
                        with self.lock:
                            self.currentRound = currentRound
                        self.event_queue.put({"type": "ROUND_CHANGE"})
                    with self.lock:
                        self.turn = getTurn(self)
            except StaleElementReferenceException:
                pass
            except Exception as e:
                logger.error(e)
                time.sleep(5)
    
    def start_listening(self):
        if not self.is_running:
            self.is_running = True
            t = threading.Thread(target=self._watchdog)
            t.daemon = True
            t.start()
            logger.info("Watchdog thread initiated.")

    def stop_listening(self):
        self.is_running = False
        logger.warning("Bye :)")

    def getEvent(self):
        try: 
            return self.event_queue.get_nowait()
        except queue.Empty:
            return
        
    def isMyTurn(self):
        displayed = self.viewInput.is_displayed()
        if displayed:
            return True
        return False
