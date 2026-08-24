"""PitchDetector API + synthetic low-bass sine accuracy (NumPy YIN)."""

from __future__ import annotations

import math
import unittest

import numpy as np

from audio.pitch import ANALYSIS_SIZE, HOP_SIZE, PitchDetector


def _cents(hz: float, target: float) -> float:
    return 1200.0 * math.log2(hz / target)


def _feed_sine(detector: PitchDetector, hz: float, *, hops: int, amp: float = 0.25) -> tuple[float, float]:
    """Push ``hops`` of a sine into ``detector``; return last ``(hz, conf)``."""
    sr = 44100.0
    phase = 0.0
    last = (0.0, 0.0)
    for _ in range(hops):
        t = (phase + np.arange(detector.hop_size, dtype=np.float64)) / sr
        samples = (amp * np.sin(2.0 * np.pi * hz * t)).astype(np.float32)
        phase = (phase + detector.hop_size) % sr
        last = detector.detect(samples)
    return last


class PitchHopTest(unittest.TestCase):
    def test_hop_fits_analysis_window(self) -> None:
        self.assertEqual(ANALYSIS_SIZE, 4096)
        self.assertEqual(HOP_SIZE, 1024)
        self.assertEqual(ANALYSIS_SIZE % HOP_SIZE, 0)

    def test_detect_rejects_capture_blocksize(self) -> None:
        detector = PitchDetector(44100)
        with self.assertRaises(ValueError):
            detector.detect(np.zeros(ANALYSIS_SIZE, dtype=np.float32))

    def test_detect_accepts_hop_size(self) -> None:
        detector = PitchDetector(44100)
        hz, conf = detector.detect(np.zeros(detector.hop_size, dtype=np.float32))
        self.assertIsInstance(hz, float)
        self.assertIsInstance(conf, float)

    def test_silence_returns_zero(self) -> None:
        detector = PitchDetector(44100)
        # Fill the analysis window with silence.
        for _ in range(ANALYSIS_SIZE // HOP_SIZE):
            hz, conf = detector.detect(np.zeros(HOP_SIZE, dtype=np.float32))
        self.assertEqual(hz, 0.0)
        self.assertEqual(conf, 0.0)

    def test_e1_sine_within_few_cents(self) -> None:
        target = 41.203
        detector = PitchDetector(44100)
        hz, conf = _feed_sine(detector, target, hops=12)
        self.assertGreater(conf, 0.5)
        self.assertLess(abs(_cents(hz, target)), 5.0)

    def test_b0_sine_within_few_cents(self) -> None:
        target = 30.868
        detector = PitchDetector(44100)
        hz, conf = _feed_sine(detector, target, hops=12)
        self.assertGreater(conf, 0.5)
        self.assertLess(abs(_cents(hz, target)), 8.0)


if __name__ == "__main__":
    unittest.main()
