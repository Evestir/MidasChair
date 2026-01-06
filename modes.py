from enum import IntEnum
from dataclasses import dataclass

class Modes(IntEnum):
    blatant = 0 # """Pick the longest words"""
    semiBlatant = 1
    legit = 2 # """Randomize options"""

class Versions(IntEnum):
    Korea = 0 
    Io = 1

class WordSelModes(IntEnum):
    longest = 0
    random = 1

@dataclass
class RoomSettings: 
    ack: bool
    manner: bool