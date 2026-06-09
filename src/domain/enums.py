from __future__ import annotations

from enum import Enum


class CharacterClass(str, Enum):
    WARRIOR = "Warrior"
    PALADIN = "Paladin"
    HUNTER = "Hunter"
    ROGUE = "Rogue"
    PRIEST = "Priest"
    DEATH_KNIGHT = "Death Knight"
    SHAMAN = "Shaman"
    MAGE = "Mage"
    WARLOCK = "Warlock"
    DRUID = "Druid"


class Role(str, Enum):
    TANK = "Tank"
    HEALER = "Healer"
    DPS = "DPS"


class ShiftStatus(str, Enum):
    DRAFT = "Draft"
    OPEN = "Open"
    SCHEDULED = "Scheduled"
    CLOSED = "Closed"
