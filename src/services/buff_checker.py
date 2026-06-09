from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Iterable

from src.domain.buff_catalog import BUFF_CATALOG
from src.domain.enums import CharacterClass


@dataclass(slots=True)
class BuffCheckResult:
    name: str
    category: str
    covered: bool


class BuffCheckerService:
    def evaluate(self, classes: Iterable[CharacterClass]) -> list[BuffCheckResult]:
        class_set = set(classes)
        results: list[BuffCheckResult] = []
        for buff in BUFF_CATALOG:
            covered = bool(class_set.intersection(buff.providers))
            results.append(BuffCheckResult(buff.name, buff.category, covered))
        return results
