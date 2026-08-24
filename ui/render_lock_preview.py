#!/usr/bin/env python3
"""Grab status-row lock icon previews (locked + listening)."""

from __future__ import annotations

import os
import sys
import tempfile
from dataclasses import replace
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from PySide6.QtCore import QEventLoop, QSize, QTimer, QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQuick import QQuickItem, QQuickWindow

from ui.controller import TunerController
from ui.qt_backend import TunerBackend
from ui.qt_ui import load_engine

PRESETS = ROOT / "config" / "presets.json"
OUT = ROOT / "ui" / "_lock_preview"
COMPARE_QML = ROOT / "ui" / "qml" / "LockPreviewCompare.qml"


def _find_lock_any(root) -> QQuickItem | None:
    if hasattr(root, "objectName") and root.objectName() == "lockMark" and isinstance(root, QQuickItem):
        return root
    for child in root.children():
        found = _find_lock_any(child)
        if found is not None:
            return found
    return None


def _grab(item: QQuickItem, path: Path, scale: float = 12.0) -> None:
    size = QSize(max(1, int(item.width() * scale)), max(1, int(item.height() * scale)))
    grab = item.grabToImage(size)
    loop = QEventLoop()
    grab.ready.connect(loop.quit)
    QTimer.singleShot(3000, loop.quit)
    loop.exec()
    result = grab.image()
    if result.isNull():
        raise RuntimeError(f"grab failed: {path}")
    result.save(str(path))


def _render_compare(app: QGuiApplication, name: str, locked: bool, path: Path) -> None:
    from PySide6.QtQuick import QQuickView

    view = QQuickView()
    view.setResizeMode(QQuickView.SizeRootObjectToView)
    view.setSource(QUrl.fromLocalFile(str(COMPARE_QML)))
    view.setColor("#1a1a1a")
    view.resize(320, 96)
    view.show()
    app.processEvents()
    root = view.rootObject()
    if root is None:
        raise RuntimeError("LockPreviewCompare.qml failed to load")
    root.setProperty("locked", locked)
    app.processEvents()
    img = view.grabWindow()
    if img.isNull():
        raise RuntimeError(f"compare grab failed: {path}")
    img.save(str(path))
    view.close()
    app.processEvents()


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    app = QGuiApplication(sys.argv)
    tmp = tempfile.TemporaryDirectory()

    for name, locked in (("listening", False), ("locked", True)):
        controller = TunerController(
            presets_path=PRESETS,
            preset_key="standard_4",
            demo=True,
            settings_path=Path(tmp.name) / f"{name}.json",
        )
        backend = TunerBackend(controller)
        engine = load_engine(backend)
        window = engine.rootObjects()[0]
        if not isinstance(window, QQuickWindow):
            raise RuntimeError("expected QQuickWindow root")

        backend._timer.stop()
        backend._snap = replace(backend._snap, locked=locked, subtitle="Preview")
        backend.frameChanged.emit()
        app.processEvents()

        lock = _find_lock_any(window)
        if lock is None:
            raise RuntimeError("lockMark not found")
        lock.requestPaint()
        app.processEvents()
        _grab(lock, OUT / f"lock-{name}.png")

        content = window.contentItem()
        _grab(content, OUT / f"status-{name}.png", scale=1.0)

        backend.shutdown()
        del engine
        app.processEvents()

    for name, locked in (("listening", False), ("locked", True)):
        _render_compare(app, name, locked, OUT / f"compare-{name}.png")

    tmp.cleanup()
    print(f"Wrote previews to {OUT}/")


if __name__ == "__main__":
    main()
