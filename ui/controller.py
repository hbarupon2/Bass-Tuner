"""UI-agnostic tuner session: audio, settings, demo pitch. No Qt."""

from __future__ import annotations

import math
import threading
import time
import re
from dataclasses import dataclass, replace
from pathlib import Path

NOTE_LETTER = re.compile(r"^([A-Ga-g][#b]?)")

import numpy as np

from cli import CliSession
from config.user_settings import (
    A4_MAX,
    A4_MIN,
    CONF_MAX,
    CONF_MIN,
    GATE_MAX,
    GATE_MIN,
    IN_TUNE_MAX,
    IN_TUNE_MIN,
    RING_MAX,
    RING_MIN,
    UserSettings,
    apply_to_smoother,
    calibrate_floors,
    default_settings_path,
    load_settings,
    save_settings,
)
from core.presets import load_presets
from core.tuner_engine import TunerReading, TunerSmoother

NEEDLE_LERP = 0.22


def header_title(preset_name: str) -> str:
    if "string" in preset_name.lower():
        return preset_name
    return f"{preset_name}-String"


def chip_label(name: str) -> str:
    if name.endswith(" Down"):
        return name[:-5]
    return name


def note_parts(note: str) -> tuple[str, str]:
    match = NOTE_LETTER.match(note or "")
    if not match:
        return "—", ""
    raw = match.group(1)
    letter = raw[0].upper()
    if len(raw) > 1 and raw[1] in "bB":
        return letter, "flat"
    if len(raw) > 1 and raw[1] == "#":
        return letter, "sharp"
    return letter, ""


def note_letter(note: str) -> str:
    letter, accidental = note_parts(note)
    if accidental == "flat":
        return letter + "♭"
    if accidental == "sharp":
        return letter + "♯"
    return letter


def device_choices(devices: list[tuple[int, str]]) -> list[tuple[int | None, str]]:
    return [(None, "System Default"), *devices]


def device_label(settings: UserSettings, devices: list[tuple[int, str]]) -> str:
    for index, name in device_choices(devices):
        if index == settings.input_device:
            return name
    if settings.input_device is None:
        return "System Default"
    return f"Device {settings.input_device}"


def list_devices() -> list[tuple[int, str]]:
    from audio.capture import list_input_devices

    return list_input_devices()


class _ReadingState:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._reading = TunerReading(0.0, None, float("nan"), False, 0.0)
        self._energy = 0.0

    def set(self, reading: TunerReading, energy: float = 0.0) -> None:
        with self._lock:
            self._reading = reading
            self._energy = energy

    def get(self) -> tuple[TunerReading, float]:
        with self._lock:
            return self._reading, self._energy


def _demo_reading(session: CliSession, t: float, in_tune_cents: float) -> tuple[TunerReading, float]:
    preset = session.preset
    idx = session.manual_index or 1
    idx = min(idx, len(preset.strings))
    target = preset.strings[idx - 1]
    cents = 8.0 * math.sin(t * 0.8)
    hz = target.frequency_hz * (2 ** (cents / 1200.0))
    in_tune = abs(cents) <= in_tune_cents
    conf = 0.85 if abs(cents) < 20 else 0.55
    energy = 0.02 + 0.02 * abs(math.sin(t * 1.4))
    return TunerReading(hz, target, cents, in_tune, conf), energy


@dataclass
class TunerSnapshot:
    note_letter: str
    note_accidental: str
    subtitle: str
    cents: float
    cents_valid: bool
    in_tune: bool
    locked: bool
    confidence: float
    energy: float
    preset_title: str
    preset_key: str
    strings: list[dict]
    presets: list[dict]
    show_signal: bool
    cents_range: int
    in_tune_cents: float
    needle_smoothing: bool


class TunerController:
    """Live tuner + settings. Call :meth:`tick` from the UI thread."""

    def __init__(
        self,
        *,
        presets_path: Path,
        preset_key: str,
        device: int | None = None,
        demo: bool = False,
        settings_path: Path | None = None,
    ) -> None:
        self.presets_path = presets_path
        self.demo = demo
        self.settings_path = settings_path or default_settings_path()
        self.settings = load_settings(self.settings_path)
        if device is not None:
            self.settings = replace(self.settings, input_device=device)
            save_settings(self.settings, self.settings_path)

        presets = load_presets(presets_path, self.settings.a4_hz)
        if preset_key not in presets:
            raise ValueError(f"Unknown preset {preset_key!r}")
        smoother = TunerSmoother()
        apply_to_smoother(smoother, self.settings)
        self.session = CliSession(presets=presets, preset_key=preset_key, smoother=smoother)
        if not self.settings.string_auto:
            self.session.set_manual_string(1)

        self._state = _ReadingState()
        self._stream = None
        self.display_cents: float | None = None
        self.peak_energy = 0.0
        self.show_settings = False
        self.detection_open = False
        self.picking_device = False
        self.notice = ""
        self.devices: list[tuple[int, str]] = []
        self.last_manual = self.session.manual_index
        self.previous_device: int | None = None
        if not demo:
            self._start_stream(self.settings.input_device)

    def shutdown(self) -> None:
        self._persist()
        self._stop_stream()

    def tick(self, now: float | None = None) -> TunerSnapshot:
        now = time.monotonic() if now is None else now
        if self.demo:
            fake, energy = _demo_reading(self.session, now, self.settings.in_tune_cents)
            self._state.set(fake, energy)
        reading, energy = self._state.get()
        self.peak_energy = max(energy, self.peak_energy * 0.97)
        lerp = NEEDLE_LERP if self.settings.needle_smoothing else 1.0
        cents_valid = reading.target is not None and not math.isnan(reading.cents)
        if cents_valid:
            if self.display_cents is None:
                self.display_cents = reading.cents
            else:
                self.display_cents += (reading.cents - self.display_cents) * lerp
            cents = self.display_cents
        else:
            self.display_cents = None
            cents = 0.0
        return self._snapshot(reading, energy, cents, cents_valid)

    def _snapshot(
        self, reading: TunerReading, energy: float, cents: float, cents_valid: bool,
    ) -> TunerSnapshot:
        preset = self.session.preset
        active_note = reading.target.note if reading.target else None
        strings = []
        n = len(preset.strings)
        for i, target in enumerate(preset.strings, start=1):
            active = (
                self.session.manual_index == i
                or (self.session.manual_index is None and active_note == target.note)
            )
            if i == 1:
                label = "1 (LOW)"
            elif i == n:
                label = f"{i} (HIGH)"
            else:
                label = str(i)
            letter, accidental = note_parts(target.note)
            strings.append({
                "number": i,
                "letter": letter,
                "accidental": accidental,
                "label": label,
                "active": active,
            })
        presets = [
            {
                "key": key,
                "name": chip_label(self.session.presets[key].name),
                "active": key == self.session.preset_key,
            }
            for key in self.session.preset_keys
        ]
        if reading.target is None:
            letter, accidental, subtitle = "—", "", "Listening…"
        else:
            letter, accidental = note_parts(reading.target.note)
            match = NOTE_LETTER.match(reading.target.note)
            rest = reading.target.note[len(match.group(1)):] if match else ""
            subtitle = f"{rest} · {reading.detected_hz:.1f} Hz"
        return TunerSnapshot(
            note_letter=letter,
            note_accidental=accidental,
            subtitle=subtitle,
            cents=cents,
            cents_valid=cents_valid,
            in_tune=reading.in_tune,
            locked=reading.target is not None,
            confidence=reading.confidence,
            energy=energy,
            preset_title=header_title(preset.name),
            preset_key=self.session.preset_key,
            strings=strings,
            presets=presets,
            show_signal=self.settings.show_signal_meter,
            cents_range=self.settings.cents_range,
            in_tune_cents=self.settings.in_tune_cents,
            needle_smoothing=self.settings.needle_smoothing,
        )

    def select_string(self, number: int) -> None:
        self.session.set_manual_string(number)
        self.last_manual = number
        self.settings = replace(self.settings, string_auto=False)
        self._persist()

    def auto_string(self) -> None:
        self.session.set_manual_string(None)
        self.settings = replace(self.settings, string_auto=True)
        self._persist()

    def select_preset(self, key: str) -> None:
        self.session.set_preset(key)

    def cycle_preset(self, step: int) -> None:
        self.session.cycle_preset(step)

    def open_settings(self) -> None:
        self.settings = replace(self.settings, string_auto=self.session.manual_index is None)
        self.devices = list_devices()
        self.picking_device = False
        self.show_settings = True

    def close_settings(self) -> None:
        self.show_settings = False
        self.picking_device = False
        self._persist()

    def toggle_detection(self) -> None:
        self.detection_open = not self.detection_open

    def open_device_picker(self) -> None:
        self.devices = list_devices()
        self.picking_device = True
        self.notice = ""

    def close_device_picker(self) -> None:
        self.picking_device = False

    def select_device(self, index: int | None) -> None:
        self.previous_device = self.settings.input_device
        self.settings = replace(self.settings, input_device=index).clamped()
        self.picking_device = False
        self.notice = device_label(self.settings, self.devices)
        self._apply_engine()
        self._restart_stream(self.settings.input_device, previous=self.previous_device)

    def calibrate(self) -> None:
        energy = max(self._state.get()[1], self.peak_energy)
        floors = calibrate_floors(energy)
        if floors is None:
            self.notice = "No signal — play a note"
            return
        gate, ring = floors
        self.settings = replace(
            self.settings, signal_energy_floor=gate, ringing_energy_floor=ring,
        ).clamped()
        self.notice = f"Calibrated · gate {self.settings.signal_energy_floor:.3f}"
        self.detection_open = True
        self._apply_engine()

    def nudge_a4(self, delta: int) -> None:
        self.settings = replace(self.settings, a4_hz=self.settings.a4_hz + delta).clamped()
        self._apply_engine(reload_a4=True)

    def set_in_tune(self, cents: float) -> None:
        self.settings = replace(self.settings, in_tune_cents=cents).clamped()
        self._apply_engine()

    def set_response(self, key: str) -> None:
        self.settings = replace(self.settings, response=key).clamped()
        self._apply_engine()

    def set_string_auto(self, auto: bool) -> None:
        self.settings = replace(self.settings, string_auto=auto)
        self._apply_engine(sync_string=True)

    def set_needle_smoothing(self, on: bool) -> None:
        self.settings = replace(self.settings, needle_smoothing=on)
        self._persist()

    def set_show_signal(self, on: bool) -> None:
        self.settings = replace(self.settings, show_signal_meter=on)
        self._persist()

    def set_cents_range(self, span: int) -> None:
        self.settings = replace(self.settings, cents_range=span).clamped()
        self._persist()

    def set_min_confidence(self, value: float) -> None:
        self.settings = replace(self.settings, min_confidence=value).clamped()
        self._apply_engine()

    def set_signal_gate(self, value: float) -> None:
        self.settings = replace(self.settings, signal_energy_floor=value).clamped()
        self._apply_engine()

    def set_ringing_hold(self, value: float) -> None:
        self.settings = replace(self.settings, ringing_energy_floor=value).clamped()
        self._apply_engine()

    def reset_defaults(self) -> None:
        device = self.settings.input_device
        self.settings = UserSettings(input_device=device)
        self.detection_open = False
        self.picking_device = False
        self.notice = ""
        self._apply_engine(reload_a4=True, sync_string=True)

    def _persist(self) -> None:
        save_settings(self.settings, self.settings_path)

    def _apply_engine(self, *, reload_a4: bool = False, sync_string: bool = False) -> None:
        self.settings = self.settings.clamped()
        apply_to_smoother(self.session.smoother, self.settings)
        if reload_a4:
            key = self.session.preset_key
            self.session.presets = load_presets(self.presets_path, self.settings.a4_hz)
            if key in self.session.presets:
                self.session.preset_key = key
            self.session.smoother.reset()
        if sync_string:
            if self.settings.string_auto:
                self.session.set_manual_string(None)
            else:
                idx = self.last_manual or self.session.manual_index or 1
                idx = min(idx, len(self.session.preset.strings))
                self.session.set_manual_string(idx)
                self.last_manual = idx
        self._persist()

    def _stop_stream(self) -> None:
        if self._stream is not None:
            self._stream.__exit__(None, None, None)
            self._stream = None

    def _start_stream(self, dev: int | None) -> None:
        if self.demo:
            return
        from audio.capture import stream_audio
        from audio.pitch import PitchDetector

        detector = PitchDetector(44100)

        def on_audio(samples: np.ndarray, _sample_rate: float) -> None:
            pitch_hz, confidence = detector.detect(samples)
            energy = float(np.sqrt(np.mean(np.square(samples))))
            reading = self.session.smoother.update(
                pitch_hz,
                confidence,
                self.session.preset,
                energy=energy,
                manual_string=self.session.manual_string(),
            )
            self._state.set(reading, energy)

        self._stream = stream_audio(on_audio, device=dev, block_size=detector.hop_size)
        self._stream.__enter__()

    def _restart_stream(self, dev: int | None, previous: int | None = None) -> None:
        if self.demo:
            return
        self._stop_stream()
        try:
            self._start_stream(dev)
        except Exception:
            self.settings = replace(self.settings, input_device=previous)
            self.notice = "Couldn't open device — reverted"
            self._start_stream(previous)
            self._persist()
