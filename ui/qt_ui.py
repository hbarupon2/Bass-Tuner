"""Qt Quick tuner UI (Phase 2)."""

from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine

from config.user_settings import default_settings_path
from ui.controller import TunerController
from ui.qt_backend import TunerBackend

DEFAULT_SIZE = (1024, 600)
_QML = Path(__file__).resolve().parent / "qml" / "Main.qml"


def load_engine(backend: TunerBackend) -> QQmlApplicationEngine:
    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty("backend", backend)
    engine.load(QUrl.fromLocalFile(str(_QML)))
    return engine


def run_ui(
    *,
    presets_path: Path,
    preset_key: str,
    device: int | None = None,
    demo: bool = False,
    size: tuple[int, int] = DEFAULT_SIZE,
    settings_path: Path | None = None,
) -> None:
    """Launch the QML tuner. Blocks until the window closes."""
    del size  # QML Window starts at 1024×600; user can resize.
    app = QGuiApplication.instance() or QGuiApplication(sys.argv)
    controller = TunerController(
        presets_path=presets_path,
        preset_key=preset_key,
        device=device,
        demo=demo,
        settings_path=settings_path or default_settings_path(),
    )
    backend = TunerBackend(controller)
    engine = load_engine(backend)
    if not engine.rootObjects():
        controller.shutdown()
        raise RuntimeError(f"Failed to load QML: {_QML}")
    app.aboutToQuit.connect(backend.shutdown)
    raise SystemExit(app.exec())
