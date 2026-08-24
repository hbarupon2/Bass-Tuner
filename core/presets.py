"""Load named bass tunings from JSON into in-memory presets."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from collections.abc import Sequence

from core.notes import note_to_hz


@dataclass(frozen=True)
class StringTarget:
    """One string in a tuning: display name and target frequency.

    Attributes:
        note: Scientific pitch notation, e.g. ``E1``.
        frequency_hz: 12-TET frequency for ``note`` at the preset A4.
    """

    note: str
    frequency_hz: float


@dataclass(frozen=True)
class TuningPreset:
    """A named set of string targets, low string first.

    Attributes:
        key: Stable id from JSON, e.g. ``standard_4``.
        name: Display name, e.g. ``Standard 4``.
        strings: Targets ordered lowest pitch to highest.
    """

    key: str
    name: str
    strings: tuple[StringTarget, ...]


def load_presets(path: Path, a4_hz: float = 440.0) -> dict[str, TuningPreset]:
    """Parse a presets JSON file into :class:`TuningPreset` objects.

    Expected shape::

        {
          "standard_4": {
            "name": "Standard 4",
            "strings": ["E1", "A1", "D2", "G2"]
          }
        }

    Args:
        path: Path to ``presets.json``.
        a4_hz: Concert pitch used to compute each string frequency.

    Returns:
        Map of preset key → :class:`TuningPreset`.
    """
    data = json.loads(path.read_text())
    presets: dict[str, TuningPreset] = {}

    for key, entry in data.items():
        strings = tuple(
            StringTarget(note=note, frequency_hz=note_to_hz(note, a4_hz))
            for note in entry["strings"]
        )
        presets[key] = TuningPreset(key=key, name=entry["name"], strings=strings)

    return presets


def string_by_number(preset: TuningPreset, number: int) -> StringTarget | None:
    """Return a string by 1-based index (1 = lowest).

    Args:
        preset: Active tuning.
        number: String number as on a tuner (1 = low E on a 4-string).

    Returns:
        The :class:`StringTarget`, or ``None`` if ``number`` is out of range.
    """
    if number < 1 or number > len(preset.strings):
        return None
    return preset.strings[number - 1]


def cycle_preset_key(keys: Sequence[str], current: str, step: int) -> str:
    """Step through preset keys, wrapping at both ends.

    Args:
        keys: Ordered preset ids.
        current: Key to move from.
        step: ``+1`` next, ``-1`` previous.

    Returns:
        The new key.

    Raises:
        ValueError: If ``current`` is not in ``keys``.
    """
    ordered = list(keys)
    index = ordered.index(current)
    return ordered[(index + step) % len(ordered)]
