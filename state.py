from enum import Enum

class States(Enum):
    title = 0
    lobby = 1
    game_lobby =2
    pre_game = 3
    in_game = 4
    end_screen = 5

class TurnPhase(Enum):
    WAIT = 0
    SHOULD_TYPE = 1
    SHOULD_PREDICT = 2
    TYPED = 3
    ERROR = 4
    NO_WORD = 5
    MANUAL = 6
