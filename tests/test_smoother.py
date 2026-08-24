"""Tests for :class:`~core.tuner_engine.TunerSmoother` (median, hold, hysteresis)."""

import unittest
from pathlib import Path

from core.presets import load_presets
from core.tuner_engine import TunerSmoother

PRESET_PATH = Path(__file__).resolve().parents[1] / "config" / "presets.json"
PLUCK = 0.05


def _preset():
    return load_presets(PRESET_PATH)["standard_4"]


class SmootherTest(unittest.TestCase):
    def test_outlier_does_not_jump_cents(self) -> None:
        smoother = TunerSmoother(window=5)
        preset = _preset()
        for _ in range(5):
            smoother.update(41.20, 0.95, preset, energy=PLUCK)
        spike = smoother.update(48.0, 0.95, preset, energy=PLUCK)
        self.assertEqual(spike.target.note, "E1")
        self.assertLess(abs(spike.cents), 15.0)

    def test_mid_confidence_still_locks(self) -> None:
        smoother = TunerSmoother(window=3)
        preset = _preset()
        reading = None
        for _ in range(5):
            reading = smoother.update(41.20, 0.50, preset, energy=PLUCK)
        self.assertIsNotNone(reading)
        self.assertEqual(reading.target.note, "E1")

    def test_hold_through_brief_gate(self) -> None:
        smoother = TunerSmoother(hold_frames=4)
        preset = _preset()
        for _ in range(5):
            smoother.update(41.20, 0.95, preset, energy=PLUCK)
        held = smoother.update(0.0, 0.1, preset)
        self.assertEqual(held.target.note, "E1")
        self.assertTrue(held.in_tune)

    def test_string_does_not_flicker_on_one_hop(self) -> None:
        smoother = TunerSmoother(switch_confirm=3, window=5)
        preset = _preset()
        for _ in range(6):
            smoother.update(41.20, 0.95, preset, energy=PLUCK)
        hop = smoother.update(55.00, 0.95, preset, energy=PLUCK)
        self.assertEqual(hop.target.note, "E1")

    def test_octave_harmonic_smoothed(self) -> None:
        smoother = TunerSmoother(window=3)
        preset = _preset()
        reading = None
        for _ in range(5):
            reading = smoother.update(82.41, 0.96, preset, energy=PLUCK)
        self.assertEqual(reading.target.note, "E1")
        self.assertLess(abs(reading.cents), 5.0)

    def test_d_third_harmonic_smoothed(self) -> None:
        smoother = TunerSmoother(window=3)
        preset = _preset()
        reading = None
        for _ in range(5):
            reading = smoother.update(220.25, 0.35, preset, energy=0.05)
        self.assertEqual(reading.target.note, "D2")
        self.assertLess(abs(reading.cents), 5.0)

    def test_in_tune_hysteresis(self) -> None:
        smoother = TunerSmoother(window=1, alpha=1.0, in_tune_cents=5.0, cents_alpha=1.0)
        preset = _preset()
        on = smoother.update(41.20, 0.95, preset, energy=PLUCK)
        self.assertTrue(on.in_tune)
        slightly_out = smoother.update(41.34, 0.95, preset, energy=PLUCK)  # ~6¢
        self.assertTrue(slightly_out.in_tune)
        clearly_out = smoother.update(41.50, 0.95, preset, energy=PLUCK)  # ~12¢
        self.assertFalse(clearly_out.in_tune)

    def test_loud_unpitched_keeps_lock(self) -> None:
        smoother = TunerSmoother(hold_frames=2)
        preset = _preset()
        for _ in range(5):
            smoother.update(73.42, 0.95, preset, energy=PLUCK)
        for _ in range(20):
            held = smoother.update(0.0, 0.1, preset, energy=0.08)
        self.assertEqual(held.target.note, "D2")

    def test_quiet_unpitched_unlocks(self) -> None:
        smoother = TunerSmoother(hold_frames=2)
        preset = _preset()
        for _ in range(5):
            smoother.update(73.42, 0.95, preset, energy=PLUCK)
        smoother.update(0.0, 0.1, preset, energy=0.0)
        unlocked = smoother.update(0.0, 0.1, preset, energy=0.0)
        unlocked = smoother.update(0.0, 0.1, preset, energy=0.0)
        self.assertIsNone(unlocked.target)

    def test_low_energy_noise_rejected(self) -> None:
        smoother = TunerSmoother()
        preset = _preset()
        reading = smoother.update(120.0, 0.90, preset, energy=0.001)
        self.assertIsNone(reading.target)
        self.assertEqual(reading.detected_hz, 0.0)

    def test_outlier_spike_holds_last_cents(self) -> None:
        smoother = TunerSmoother(window=3, cents_alpha=1.0)
        preset = _preset()
        for _ in range(5):
            smoother.update(41.20, 0.95, preset, energy=PLUCK)
        stable = smoother.update(41.20, 0.95, preset, energy=PLUCK)
        spike = smoother.update(55.00, 0.95, preset, energy=PLUCK)
        self.assertEqual(spike.target.note, "E1")
        self.assertLess(abs(spike.cents - stable.cents), 5.0)

    def test_g_decay_does_not_become_d(self) -> None:
        smoother = TunerSmoother(window=3)
        preset = _preset()
        for _ in range(6):
            smoother.update(98.00, 0.95, preset, energy=PLUCK)
        reading = None
        for _ in range(30):
            reading = smoother.update(146.83, 0.80, preset, energy=PLUCK)
        self.assertEqual(reading.target.note, "G2")

    def test_cents_smoothing_limits_jump(self) -> None:
        smoother = TunerSmoother(window=1, alpha=1.0, cents_alpha=0.5, max_cents_step=2.0)
        preset = _preset()
        for _ in range(3):
            smoother.update(41.20, 0.95, preset, energy=PLUCK)
        before = smoother.update(41.20, 0.95, preset, energy=PLUCK).cents
        after = smoother.update(42.00, 0.95, preset, energy=PLUCK).cents
        self.assertLess(abs(after - before), 3.0)


if __name__ == "__main__":
    unittest.main()
