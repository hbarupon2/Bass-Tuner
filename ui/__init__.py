"""Tuner UI (Qt Quick)."""

__all__ = ["run_ui"]


def __getattr__(name: str):
    if name == "run_ui":
        from ui.qt_ui import run_ui

        return run_ui
    raise AttributeError(name)
