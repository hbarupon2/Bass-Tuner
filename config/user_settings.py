"""Persisted tuner settings (OSS-safe). I/O is JSON only — no audio/UI."""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, fields, replace
from pathlib import Path
from typing import Any

from core.tuner_engine import TunerSmoother

APP_VERSION = "0.2.0"

A4_MIN = 435
A4_MAX = 445
IN_TUNE_MIN = 1.0
IN_TUNE_MAX = 10.0
CONF_MIN = 0.10
CONF_MAX = 0.50
GATE_MIN = 0.002
GATE_MAX = 0.020
RING_MIN = 0.006
RING_MAX = 0.030

RESPONSE_PRESETS: dict[str, dict[str, float]] = {
    "slow": {"alpha": 0.10, "cents_alpha": 0.10, "max_cents_step": 1.0},
    "normal": {"alpha": 0.15, "cents_alpha": 0.18, "max_cents_step": 2.0},
    "fast": {"alpha": 0.25, "cents_alpha": 0.35, "max_cents_step": 4.0},
}


def default_settings_path() -> Path:
    xdg = os.environ.get("XDG_CONFIG_HOME")
    root = Path(xdg) if xdg else Path.home() / ".config"
    return root / "bass-tuner" / "settings.json"


@dataclass
class UserSettings:
    a4_hz: float = 440.0
    in_tune_cents: float = 5.0
    string_auto: bool = True
    response: str = "normal"
    min_confidence: float = 0.25
    signal_energy_floor: float = 0.008
    ringing_energy_floor: float = 0.014
    needle_smoothing: bool = True
    show_signal_meter: bool = True
    cents_range: int = 50
    input_device: int | None = None

    def clamped(self) -> UserSettings:
        response = self.response if self.response in RESPONSE_PRESETS else "normal"
        cents_range = 25 if int(self.cents_range) <= 25 else 50
        device = self.input_device
        if device is not None:
            device = int(device)
            if device < 0:
                device = None
        return replace(
            self,
            a4_hz=float(max(A4_MIN, min(A4_MAX, round(self.a4_hz)))),
            in_tune_cents=float(max(IN_TUNE_MIN, min(IN_TUNE_MAX, round(self.in_tune_cents)))),
            string_auto=bool(self.string_auto),
            response=response,
            min_confidence=float(max(CONF_MIN, min(CONF_MAX, self.min_confidence))),
            signal_energy_floor=float(max(GATE_MIN, min(GATE_MAX, self.signal_energy_floor))),
            ringing_energy_floor=float(max(RING_MIN, min(RING_MAX, self.ringing_energy_floor))),
            needle_smoothing=bool(self.needle_smoothing),
            show_signal_meter=bool(self.show_signal_meter),
            cents_range=cents_range,
            input_device=device,
        )


_FIELD_NAMES = {f.name for f in fields(UserSettings)}


def load_settings(path: Path | None = None) -> UserSettings:
    path = path or default_settings_path()
    if not path.is_file():
        return UserSettings()
    try:
        data = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return UserSettings()
    if not isinstance(data, dict):
        return UserSettings()
    raw: dict[str, Any] = {k: data[k] for k in _FIELD_NAMES if k in data}
    try:
        return UserSettings(**raw).clamped()
    except (TypeError, ValueError):
        return UserSettings()


def save_settings(settings: UserSettings, path: Path | None = None) -> None:
    path = path or default_settings_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = asdict(settings.clamped())
    path.write_text(json.dumps(payload, indent=2) + "\n")


def apply_to_smoother(smoother: TunerSmoother, settings: UserSettings) -> None:
    s = settings.clamped()
    params = RESPONSE_PRESETS[s.response]
    smoother.configure(
        alpha=params["alpha"],
        cents_alpha=params["cents_alpha"],
        max_cents_step=params["max_cents_step"],
        in_tune_cents=s.in_tune_cents,
        min_confidence=s.min_confidence,
        signal_energy_floor=s.signal_energy_floor,
        ringing_energy_floor=s.ringing_energy_floor,
    )


def slider_from_range(value: float, lo: float, hi: float) -> float:
    if hi <= lo:
        return 0.0
    return max(0.0, min(1.0, (value - lo) / (hi - lo)))


def slider_to_range(t: float, lo: float, hi: float, *, steps: int | None = None) -> float:
    t = max(0.0, min(1.0, t))
    raw = lo + t * (hi - lo)
    if steps is None:
        return raw
    return round(raw)


def calibrate_floors(energy: float) -> tuple[float, float] | None:
    """Map measured RMS to signal / ringing floors. None if too quiet."""
    if energy < 1e-4:
        return None
    gate = max(GATE_MIN, min(GATE_MAX, energy * 1.25))
    ring = max(RING_MIN, min(RING_MAX, gate * 1.75))
    return gate, ring
