"""Dataclasses for language pairs and phrase entries."""

from __future__ import annotations

from dataclasses import dataclass, field


# Categories used across all language pair modules. The TUI and tests rely on
# these exact strings.
CATEGORIES = ("script", "vocab", "phrase", "sentence")

SUBCATEGORIES = (
    # script
    "alphabet",
    "syllabary",
    "tones",
    # numbers + time
    "numbers",
    "days",
    "months",
    "time",
    # vocab buckets
    "colors",
    "family",
    "food",
    "drink",
    "body",
    "weather",
    "animals",
    "house",
    "work",
    "verbs",
    "adjectives",
    "directions",
    "money",
    # phrase buckets
    "greeting",
    "courtesy",
    "introduction",
    "shopping",
    "restaurant",
    "transit",
    "emergency",
    # sentence buckets
    "question",
    "need",
    "opinion",
    "small_talk",
)


@dataclass(frozen=True)
class PhraseEntry:
    source: str
    target: str
    pronunciation: str = ""
    category: str = "vocab"
    subcategory: str = "verbs"
    note: str = ""


@dataclass(frozen=True)
class LanguagePair:
    id: str
    source_lang: str
    target_lang: str
    source_code: str
    target_code: str
    target_native: str
    script: str
    flag: str
    blurb: str
    phrases: tuple[PhraseEntry, ...] = field(default_factory=tuple)

    @property
    def label(self) -> str:
        return f"{self.source_lang} → {self.target_lang}"

    @property
    def display_native(self) -> str:
        return self.target_native or self.target_lang
