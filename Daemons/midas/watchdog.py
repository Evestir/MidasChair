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

def findRounds(self):
    rounds = []
    children = self.driver.find_elements(By.CSS_SELECTOR, "div.rounds > *")

    currentRound = 0
    for i, child in enumerate(children):
        if child.get_attribute("class") == "rounds-current":
            currentRound = i
        rounds.append(child.text)
    return (rounds, currentRound)

def findcCField(self):
        elements = self.driver.find_elements(By.CSS_SELECTOR, ".jjo-display.ellipse")
        if not elements: return
        for element in elements:
            if element.value_of_css_property("display") == "block":
                return element
        
def getInput(self):
    inp = self.driver.find_element(By.CSS_SELECTOR, "input[autocapitalize='off'][id^='ClientMessage']")
    if inp is not None:
        return inp
    
def getViewInput(self):
    element = self.driver.find_element(By.CSS_SELECTOR, ".game-input")
    return element

def getResExitBtn(self):
    btn = self.driver.find_element(By.ID, "ReserveExitBtn")
    return btn

def getRoomSettings(self):
    element = self.driver.find_element(By.CSS_SELECTOR, ".room-head-mode.expl-mother")
    text = element.get_attribute("textContent")
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
        elements = self.driver.find_elements(By.CSS_SELECTOR, ".fa-solid.fa-gear")
        if len(elements) != 0:
            state = States.lobby
    elif self.state == States.lobby:
        placeholder = self.inputField.get_attribute("placeholder")
        """↩ 자신이 직접 단어를 입력하지 않는 모든 행위(자동완성·매크로·붙여넣기 등)는 금지됩니다"""
        if placeholder and placeholder[0] == "↩":
            self.event_queue.put({"type": "INIT_DATA", "name": self.name, "inputField": self.inputField})
            state = States.pre_game
    elif self.state == States.pre_game:
        placeholder = self.cCField.text
        if placeholder != None and placeholder != "잠시 후 게임이 시작됩니다!" and self.roundChars:
            self.event_queue.put({"type": "PRE_GAME_DATA", "players": self.players, "playerCount": self.playerCount, "cCField": self.cCField, "roundChars": self.roundChars, "myTurn": self.myTurn, "rounds": self.rounds, "roomSettings": self.roomSettings})
            state = States.in_game
    elif self.state == States.in_game or self.state == States.end_screen:
        displayed = self.resExitBtn.is_displayed()
        if not displayed:
            state = States.lobby
    if state is not self.state:
        logger.debug(f"Game State: {state.name}")
    return state
    
def getMyName(self):
    element = self.driver.find_element(By.CSS_SELECTOR, ".my-stat-name.ellipse")
    name = element.get_attribute("textContent").strip()
    return name

def getMyTurn(self):
    if not self.players:
        logger.error("No players found at getMyTurn()")
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

class watchdog:
    def __init__(self, driver):
        self.driver = driver
        self.is_running = False
        self.lock = threading.Lock()
        self.event_queue = queue.Queue()

        """lobby (events)"""
        self.name = ""
        self.inputField = None

        """in_game (events)"""
        self.players = []
        self.playerCount = 0
        self.roundChars = []
        self.currentRound = 0
        self.rounds = 0
        self.cCField = None
        self.viewInput = None
        self.resExitBtn = None
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
                with self.lock:
                    self.state = getState(self)
                if self.state == States.lobby:
                    if self.players:
                        with self.lock:
                            self.players = []
                            self.turn = 0
                    elif not self.inputField:
                        with self.lock:
                            self.inputField = self._failSafe(getInput)
                    elif not self.resExitBtn:
                        with self.lock:
                            self.resExitBtn =  self._failSafe(getResExitBtn)
                    elif not self.name:
                        with self.lock:
                            self.name = self._failSafe(getMyName)
                elif self.state == States.pre_game:
                    if not self.players:
                        with self.lock:
                            self.players = self._failSafe(getPlayers)
                            self.playerCount = len(self.players)
                            self.cCField = self._failSafe(findcCField)
                            self.viewInput = self._failSafe(getViewInput)
                            self.myTurn = self._failSafe(getMyTurn)
                            self.roomSettings = self._failSafe(getRoomSettings)
                    with self.lock:
                        self.roundChars = findRounds(self)[0]
                        self.rounds = len(self.roundChars)
                elif self.state == States.in_game:
                    r = findRounds(self)
                    updateHistory(self)
                    with self.lock:
                        if isEnded(self):
                            self.event_queue.put({"type": "GAME_ENDED"})
                            self.state = States.end_screen
                            continue
                        if self.currentRound != r[1]:
                            self.currentRound = r[1]
                            self.event_queue.put({"type": "ROUND_CHANGE", "currentRound": self.currentRound})
                        self.turn = getTurn(self)
            except StaleElementReferenceException:
                pass
            except Exception as e:
                logger.error(f"Something Wrong?")
                print(e)
                time.sleep(5)
                pass
    
    def start_listening(self):
        if not self.is_running:
            self.is_running = True
            t = threading.Thread(target=self._watchdog)
            t.daemon = True
            t.start()
            logger.info("Watchdog thread initiated.")

    def stop_listening(self):
        self.is_running = False
        logger.info("Watchdog thread stopped.")

    def retreive(self):
        with self.lock:
            return gameStates(state = self.state, turn=self.turn)

    def getEvent(self):
        try: 
            return self.event_queue.get_nowait()
        except queue.Empty:
            return None
        
    def isMyTurn(self):
        displayed = self.viewInput.is_displayed()
        if displayed:
            return True
        return False
