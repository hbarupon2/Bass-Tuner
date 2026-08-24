"""Tests for preset load, string numbers, and live CLI key handling."""

import unittest
from pathlib import Path

from core.presets import cycle_preset_key, load_presets, string_by_number
from core.tuner_engine import analyze_pitch

PRESETS = Path(__file__).resolve().parents[1] / "config" / "presets.json"


class PresetTest(unittest.TestCase):
    def test_five_presets(self) -> None:
        presets = load_presets(PRESETS)
        self.assertEqual(
            list(presets),
            ["standard_4", "drop_d", "half_step", "five_string", "six_string"],
        )

    def test_string_by_number(self) -> None:
        preset = load_presets(PRESETS)["standard_4"]
        self.assertEqual(string_by_number(preset, 1).note, "E1")
        self.assertEqual(string_by_number(preset, 4).note, "G2")
        self.assertIsNone(string_by_number(preset, 5))
        self.assertIsNone(string_by_number(preset, 0))

    def test_cycle_wraps(self) -> None:
        keys = ("a", "b", "c")
        self.assertEqual(cycle_preset_key(keys, "c", 1), "a")
        self.assertEqual(cycle_preset_key(keys, "a", -1), "c")

    def test_manual_string_overrides_auto(self) -> None:
        preset = load_presets(PRESETS)["standard_4"]
        forced = string_by_number(preset, 1)
        reading = analyze_pitch(55.00, preset, confidence=0.95, manual_string=forced)
        self.assertEqual(reading.target.note, "E1")
        self.assertGreater(abs(reading.cents), 400.0)


class CliKeyTest(unittest.TestCase):
    def _session(self):
        from cli import CliSession
        from core.tuner_engine import TunerSmoother

        presets = load_presets(PRESETS)
        return CliSession(presets=presets, preset_key="standard_4", smoother=TunerSmoother())

    def test_force_string_and_auto(self) -> None:
        from cli import apply_key

        session = self._session()
        self.assertEqual(apply_key(session, "3"), "String 3 (D2)")
        self.assertEqual(session.manual_index, 3)
        self.assertEqual(apply_key(session, "0"), "Auto string")
        self.assertIsNone(session.manual_index)

    def test_string_out_of_range(self) -> None:
        from cli import apply_key

        session = self._session()
        self.assertIn("No string 5", apply_key(session, "5"))
        self.assertIsNone(session.manual_index)

    def test_cycle_preset_clears_manual(self) -> None:
        from cli import apply_key

        session = self._session()
        apply_key(session, "1")
        msg = apply_key(session, "]")
        self.assertEqual(msg, "Preset: Drop D")
        self.assertEqual(session.preset_key, "drop_d")
        self.assertIsNone(session.manual_index)
        apply_key(session, "[")
        self.assertEqual(session.preset_key, "standard_4")


if __name__ == "__main__":
    unittest.main()
