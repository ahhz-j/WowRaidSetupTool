from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from src.domain.enums import CharacterClass


@dataclass(frozen=True, slots=True)
class BuffDefinition:
    name: str
    category: str
    providers: tuple[CharacterClass, ...]


BUFF_CATALOG: tuple[BuffDefinition, ...] = (
    BuffDefinition("Blessing of Kings", "Buff", (CharacterClass.PALADIN,)),
    BuffDefinition("Power Word: Fortitude", "Buff", (CharacterClass.PRIEST,)),
    BuffDefinition("Arcane Intellect", "Buff", (CharacterClass.MAGE,)),
    BuffDefinition("Heroism/Bloodlust", "Buff", (CharacterClass.SHAMAN,)),
    BuffDefinition("Replenishment", "Buff", (CharacterClass.PALADIN, CharacterClass.PRIEST, CharacterClass.HUNTER)),
    BuffDefinition("Sunder Armor / Expose Armor", "Debuff", (CharacterClass.WARRIOR, CharacterClass.ROGUE)),
    BuffDefinition("Curse of Elements", "Debuff", (CharacterClass.WARLOCK,)),
    BuffDefinition("Misery / Improved Faerie Fire", "Debuff", (CharacterClass.PRIEST, CharacterClass.DRUID,)),
)


def provided_buffs(classes: Iterable[CharacterClass]) -> list[BuffDefinition]:
    class_set = set(classes)
    return [buff for buff in BUFF_CATALOG if class_set.intersection(buff.providers)]
