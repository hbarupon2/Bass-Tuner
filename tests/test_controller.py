"""TunerController — UI-agnostic session behavior."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from core.tuner_engine import TunerReading
from ui.controller import TunerController, chip_label, header_title, note_letter

ROOT = Path(__file__).resolve().parents[1]
PRESETS = ROOT / "config" / "presets.json"


class ControllerTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.settings_path = Path(self._tmp.name) / "settings.json"
        self.ctrl = TunerController(
            presets_path=PRESETS,
            preset_key="standard_4",
            demo=True,
            settings_path=self.settings_path,
        )

    def tearDown(self) -> None:
        self.ctrl.shutdown()
        self._tmp.cleanup()

    def test_header_and_note_helpers(self) -> None:
        self.assertEqual(header_title("Standard 4"), "Standard 4-String")
        self.assertEqual(header_title("5-String"), "5-String")
        self.assertEqual(chip_label("Drop D Down"), "Drop D")
        self.assertEqual(note_letter("Eb1"), "E♭")
        self.assertEqual(note_letter("D#1"), "D♯")
        self.assertEqual(note_letter("E1"), "E")

    def test_demo_tick_locks_low_e(self) -> None:
        snap = self.ctrl.tick(0.0)
        self.assertEqual(snap.note_letter, "E")
        self.assertTrue(snap.cents_valid)
        self.assertEqual(len(snap.strings), 4)
        self.assertEqual(snap.strings[0]["number"], 1)

    def test_manual_string_and_auto(self) -> None:
        self.ctrl.select_string(2)
        self.assertFalse(self.ctrl.settings.string_auto)
        self.assertEqual(self.ctrl.session.manual_index, 2)
        self.ctrl.auto_string()
        self.assertTrue(self.ctrl.settings.string_auto)
        self.assertIsNone(self.ctrl.session.manual_index)

    def test_calibrate_silence_keeps_detection_closed(self) -> None:
        self.ctrl._state.set(TunerReading(0.0, None, float("nan"), False, 0.0), 0.0)
        self.ctrl.peak_energy = 0.0
        self.ctrl.calibrate()
        self.assertEqual(self.ctrl.notice, "No signal — play a note")
        self.assertFalse(self.ctrl.detection_open)

    def test_calibrate_signal_opens_detection(self) -> None:
        self.ctrl._state.set(TunerReading(41.2, None, float("nan"), False, 0.8), 0.02)
        self.ctrl.peak_energy = 0.02
        self.ctrl.calibrate()
        self.assertTrue(self.ctrl.notice.startswith("Calibrated"))
        self.assertTrue(self.ctrl.detection_open)

    def test_detection_toggle_and_a4_clamp(self) -> None:
        self.ctrl.toggle_detection()
        self.assertTrue(self.ctrl.detection_open)
        self.ctrl.nudge_a4(-20)
        self.assertEqual(self.ctrl.settings.a4_hz, 435)

    def test_device_picker_and_persist(self) -> None:
        self.ctrl.open_settings()
        self.assertTrue(self.ctrl.show_settings)
        self.ctrl.open_device_picker()
        self.assertTrue(self.ctrl.picking_device)
        self.ctrl.select_device(None)
        self.assertFalse(self.ctrl.picking_device)
        self.ctrl.close_settings()
        self.assertTrue(self.settings_path.is_file())


if __name__ == "__main__":
    unittest.main()
