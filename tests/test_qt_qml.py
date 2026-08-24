"""Load the QML shell offscreen."""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import qInstallMessageHandler
from PySide6.QtGui import QGuiApplication
from PySide6.QtTest import QSignalSpy

from ui.controller import TunerController
from ui.qt_backend import DictListModel, TunerBackend
from ui.qt_ui import load_engine

ROOT = Path(__file__).resolve().parents[1]
PRESETS = ROOT / "config" / "presets.json"


class QtQmlTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QGuiApplication.instance() or QGuiApplication(["bass-tuner-test"])

    def test_main_qml_loads(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        msgs: list[str] = []

        def _handler(_mode, _context, message: str) -> None:
            msgs.append(str(message))

        old = qInstallMessageHandler(_handler)
        controller = TunerController(
            presets_path=PRESETS,
            preset_key="standard_4",
            demo=True,
            settings_path=Path(tmp.name) / "settings.json",
        )
        backend = TunerBackend(controller)
        try:
            engine = load_engine(backend)
            self.app.processEvents()
            self.assertTrue(engine.rootObjects(), "Main.qml failed to load")
            qml_errors = [m for m in msgs if "TypeError" in m or "ReferenceError" in m]
            self.assertEqual(qml_errors, [])
            del engine
        finally:
            backend.shutdown()
            qInstallMessageHandler(old)
            tmp.cleanup()

    def test_dict_list_model_skips_identical_replace(self) -> None:
        model = DictListModel(("key", "active"))
        rows = [{"key": "a", "active": True}, {"key": "b", "active": False}]
        model.replace(rows)
        spy = QSignalSpy(model.modelReset)
        model.replace([{"key": "a", "active": True}, {"key": "b", "active": False}])
        self.assertEqual(spy.count(), 0)
        model.replace([{"key": "a", "active": False}, {"key": "b", "active": True}])
        self.assertEqual(spy.count(), 1)

    def test_string_and_preset_survive_ticks(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        controller = TunerController(
            presets_path=PRESETS,
            preset_key="standard_4",
            demo=True,
            settings_path=Path(tmp.name) / "settings.json",
        )
        backend = TunerBackend(controller)
        try:
            resets = QSignalSpy(backend._string_model.modelReset)
            for _ in range(8):
                backend._on_tick()
                self.app.processEvents()
            self.assertEqual(resets.count(), 0)
            backend.selectString(3)
            backend._on_tick()
            self.assertEqual(controller.session.manual_index, 3)
            backend.selectPreset("drop_d")
            backend._on_tick()
            self.assertEqual(controller.session.preset_key, "drop_d")
        finally:
            backend.shutdown()
            tmp.cleanup()


if __name__ == "__main__":
    unittest.main()
