"""Tests for persisted settings, clamps, and smoother apply."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from config.user_settings import (
    A4_MAX,
    UserSettings,
    apply_to_smoother,
    calibrate_floors,
    load_settings,
    save_settings,
    slider_from_range,
    slider_to_range,
)
from core.notes import note_to_hz
from core.presets import load_presets
from core.tuner_engine import TunerSmoother

PRESETS = Path(__file__).resolve().parents[1] / "config" / "presets.json"
PLUCK = 0.05


class UserSettingsTest(unittest.TestCase):
    def test_missing_file_is_defaults(self) -> None:
        path = Path(tempfile.mkdtemp()) / "missing.json"
        s = load_settings(path)
        self.assertEqual(s, UserSettings())

    def test_roundtrip(self) -> None:
        path = Path(tempfile.mkdtemp()) / "settings.json"
        original = UserSettings(
            a4_hz=438,
            in_tune_cents=3,
            string_auto=False,
            response="fast",
            needle_smoothing=False,
            show_signal_meter=False,
            cents_range=25,
            input_device=2,
        ).clamped()
        save_settings(original, path)
        loaded = load_settings(path)
        self.assertEqual(loaded, original)

    def test_corrupt_json_falls_back(self) -> None:
        path = Path(tempfile.mkdtemp()) / "settings.json"
        path.write_text("{not json")
        self.assertEqual(load_settings(path), UserSettings())

    def test_clamps_a4_and_range(self) -> None:
        s = UserSettings(a4_hz=400, cents_range=12, response="nope").clamped()
        self.assertEqual(s.a4_hz, 435)
        self.assertEqual(s.cents_range, 25)
        self.assertEqual(s.response, "normal")
        self.assertEqual(UserSettings(a4_hz=480).clamped().a4_hz, A4_MAX)

    def test_unknown_keys_ignored(self) -> None:
        path = Path(tempfile.mkdtemp()) / "settings.json"
        path.write_text(json.dumps({"a4_hz": 442, "theme": "neon"}))
        self.assertEqual(load_settings(path).a4_hz, 442)

    def test_slider_roundtrip_in_tune(self) -> None:
        for cents in (1.0, 5.0, 10.0):
            t = slider_from_range(cents, 1.0, 10.0)
            self.assertEqual(slider_to_range(t, 1.0, 10.0, steps=1), cents)

    def test_calibrate_rejects_silence(self) -> None:
        self.assertIsNone(calibrate_floors(0.0))
        floors = calibrate_floors(0.01)
        self.assertIsNotNone(floors)
        self.assertGreater(floors[1], floors[0])

    def test_a4_changes_string_hz(self) -> None:
        at_440 = load_presets(PRESETS, 440.0)["standard_4"].strings[0].frequency_hz
        at_432 = load_presets(PRESETS, 432.0)["standard_4"].strings[0].frequency_hz
        self.assertAlmostEqual(at_440, note_to_hz("E1", 440.0), places=3)
        self.assertLess(at_432, at_440)

    def test_apply_in_tune_threshold(self) -> None:
        smoother = TunerSmoother()
        apply_to_smoother(smoother, UserSettings(in_tune_cents=8.0, response="slow"))
        self.assertEqual(smoother._in_tune_cents, 8.0)
        self.assertEqual(smoother._in_tune_exit_cents, 10.0)
        self.assertAlmostEqual(smoother._cents_alpha, 0.10)

    def test_apply_confidence_gate(self) -> None:
        preset = load_presets(PRESETS)["standard_4"]
        smoother = TunerSmoother()
        apply_to_smoother(smoother, UserSettings(min_confidence=0.45))
        reading = smoother.update(41.20, 0.20, preset, energy=PLUCK)
        self.assertIsNone(reading.target)


if __name__ == "__main__":
    unittest.main()
