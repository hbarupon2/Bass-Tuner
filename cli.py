"""Phase 1 CLI key commands (no audio I/O).

Keys::

    1–6   force string (1 = lowest)
    0     auto string detect
    [ ]   previous / next preset
"""

from __future__ import annotations

from dataclasses import dataclass

from core.presets import TuningPreset, cycle_preset_key, string_by_number
from core.tuner_engine import TunerSmoother


@dataclass
class CliSession:
    """Mutable live-tuner state for keyboard control."""

    presets: dict[str, TuningPreset]
    preset_key: str
    smoother: TunerSmoother
    manual_index: int | None = None

    @property
    def preset(self) -> TuningPreset:
        return self.presets[self.preset_key]

    @property
    def preset_keys(self) -> tuple[str, ...]:
        return tuple(self.presets)

    def manual_string(self):
        if self.manual_index is None:
            return None
        return string_by_number(self.preset, self.manual_index)

    def mode_label(self) -> str:
        if self.manual_index is None:
            return "auto"
        return f"s{self.manual_index}"

    def set_preset(self, key: str) -> bool:
        """Switch preset by key. Returns False if unknown."""
        if key not in self.presets:
            return False
        self.preset_key = key
        self.manual_index = None
        self.smoother.reset()
        return True

    def cycle_preset(self, step: int) -> None:
        self.preset_key = cycle_preset_key(self.preset_keys, self.preset_key, step)
        self.manual_index = None
        self.smoother.reset()

    def set_manual_string(self, number: int | None) -> None:
        """``None`` = auto detect; 1 = lowest string."""
        self.manual_index = number
        self.smoother.reset()


def apply_key(session: CliSession, key: str) -> str | None:
    """Apply one stdin character. Returns a status line, or ``None``.

    Args:
        session: Live CLI state (mutated in place).
        key: Single character from the keyboard.

    Returns:
        Human-readable confirmation, or ``None`` if the key is ignored.
    """
    if key in "123456":
        number = int(key)
        target = string_by_number(session.preset, number)
        if target is None:
            return f"No string {number} in {session.preset.name}"
        session.set_manual_string(number)
        return f"String {number} ({target.note})"

    if key in ("0", "a", "A"):
        session.set_manual_string(None)
        return "Auto string"

    if key in ("]", ".", "n"):
        session.cycle_preset(1)
        return f"Preset: {session.preset.name}"

    if key in ("[", ",", "p"):
        session.cycle_preset(-1)
        return f"Preset: {session.preset.name}"

    return None
