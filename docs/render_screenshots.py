#!/usr/bin/env python3
"""Render static PNGs for README (offscreen Qt, demo mode)."""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from PySide6.QtCore import QEventLoop, QTimer  # noqa: E402
from PySide6.QtGui import QGuiApplication  # noqa: E402
from PySide6.QtQuick import QQuickWindow  # noqa: E402

from core.presets import load_presets  # noqa: E402
from core.tuner_engine import TunerReading  # noqa: E402
from ui.controller import TunerController  # noqa: E402
from ui.qt_backend import TunerBackend  # noqa: E402
from ui.qt_ui import load_engine  # noqa: E402

PRESETS = ROOT / "config" / "presets.json"
OUT = Path(__file__).resolve().parent / "screenshots"


def _grab(window: QQuickWindow, path: Path) -> None:
    app = QGuiApplication.instance()
    assert app is not None
    for _ in range(3):
        app.processEvents()
    img = window.grabWindow()
    if img.isNull():
        raise RuntimeError(f"grab failed: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(str(path))


def _wait(app: QGuiApplication, ms: int = 120) -> None:
    loop = QEventLoop()
    QTimer.singleShot(ms, loop.quit)
    loop.exec()


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    app = QGuiApplication(sys.argv)
    tmp = tempfile.TemporaryDirectory()

    controller = TunerController(
        presets_path=PRESETS,
        preset_key="standard_4",
        demo=True,
        settings_path=Path(tmp.name) / "demo.json",
    )
    backend = TunerBackend(controller)
    engine = load_engine(backend)
    window = engine.rootObjects()[0]
    if not isinstance(window, QQuickWindow):
        raise RuntimeError("expected QQuickWindow root")

    preset = load_presets(PRESETS)["standard_4"]
    e1 = preset.strings[0]
    a1 = preset.strings[1]

    backend._timer.stop()

    def show(reading: TunerReading, energy: float = 0.022) -> None:
        controller._state.set(reading, energy)
        backend._snap = controller._snapshot(reading, energy, reading.cents, True)
        backend.frameChanged.emit()
        app.processEvents()
        _wait(app)

    show(TunerReading(82.4, e1, 0.0, True, 0.92))
    _grab(window, OUT / "tuner-locked.png")

    show(TunerReading(84.2, a1, 12.0, False, 0.58))
    _grab(window, OUT / "tuner-listening.png")

    backend.openSettings()
    app.processEvents()
    _wait(app, 180)
    _grab(window, OUT / "settings.png")

    backend.shutdown()
    tmp.cleanup()
    print(f"Wrote README screenshots to {OUT}/")


if __name__ == "__main__":
    main()
