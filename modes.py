from enum import IntEnum
from dataclasses import dataclass

class Modes(IntEnum):
    blatant = 0 # """Pick the longest words"""
    semiBlatant = 1
    legit = 2 # """Randomize options"""

@dataclass
class RoomSettings: 
    ack: bool
    manner: bool