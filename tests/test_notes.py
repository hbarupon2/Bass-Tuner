"""Unit tests for 12-TET note math and :func:`~core.tuner_engine.analyze_pitch`."""

import unittest

from core.notes import cents_off, note_to_hz, octave_cents
from core.presets import load_presets
from core.tuner_engine import analyze_pitch
from pathlib import Path


class NotesTest(unittest.TestCase):
    def test_open_e(self) -> None:
        self.assertAlmostEqual(note_to_hz("E1"), 41.20, places=1)

    def test_five_string_b(self) -> None:
        self.assertAlmostEqual(note_to_hz("B0"), 30.87, places=1)

    def test_a4(self) -> None:
        self.assertAlmostEqual(note_to_hz("A4"), 440.0, places=2)

    def test_d_sharp_not_d(self) -> None:
        self.assertGreater(note_to_hz("D#1"), note_to_hz("D1"))

    def test_flats(self) -> None:
        self.assertAlmostEqual(note_to_hz("Eb1"), note_to_hz("D#1"), places=2)


class EngineTest(unittest.TestCase):
    def test_in_tune_detection(self) -> None:
        presets = load_presets(Path(__file__).resolve().parents[1] / "config" / "presets.json")
        preset = presets["standard_4"]
        reading = analyze_pitch(41.20, preset, confidence=0.95)
        self.assertTrue(reading.in_tune)
        self.assertEqual(reading.target.note, "E1")

    def test_cents(self) -> None:
        self.assertAlmostEqual(cents_off(42.0, 41.20), 33.2, delta=1.0)

    def test_octave_harmonic_locks_e_string(self) -> None:
        presets = load_presets(Path(__file__).resolve().parents[1] / "config" / "presets.json")
        preset = presets["standard_4"]
        reading = analyze_pitch(82.41, preset, confidence=0.96)
        self.assertEqual(reading.target.note, "E1")
        self.assertTrue(reading.in_tune)

    def test_d_third_harmonic_locks_d_not_a(self) -> None:
        presets = load_presets(Path(__file__).resolve().parents[1] / "config" / "presets.json")
        preset = presets["standard_4"]
        reading = analyze_pitch(220.25, preset, confidence=0.40)
        self.assertEqual(reading.target.note, "D2")
        self.assertLess(abs(reading.cents), 5.0)


if __name__ == "__main__":
    unittest.main()
