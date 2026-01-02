from enum import Enum

class States(Enum):
    title = 0
    lobby = 1
    pre_game = 2
    in_game = 3
    end_screen = 4

class TurnPhase(Enum):
    WAIT = 0
    SHOULD_TYPE = 1
    SHOULD_PREDICT = 2
    TYPED = 3
    ERROR = 4
    NO_WORD = 5
    MANUAL = 6
