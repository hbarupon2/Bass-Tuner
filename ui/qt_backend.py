"""Qt Quick backend — exposes TunerController to QML."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import (
    Property,
    QAbstractListModel,
    QModelIndex,
    QObject,
    Qt,
    QTimer,
    QUrl,
    Signal,
    Slot,
)

from config.user_settings import APP_VERSION
from ui.controller import TunerController, device_choices, device_label

_FONTS = Path(__file__).resolve().parent / "fonts"


class DictListModel(QAbstractListModel):
    countChanged = Signal()

    def __init__(self, keys: tuple[str, ...], parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._keys = keys
        self._rows: list[dict] = []
        self._roles = {Qt.UserRole + i: k.encode() for i, k in enumerate(keys)}

    def _count(self) -> int:
        return len(self._rows)

    count = Property(int, _count, notify=countChanged)

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:  # type: ignore[override]
        if parent.isValid():
            return 0
        return len(self._rows)

    def roleNames(self) -> dict[int, bytes]:  # type: ignore[override]
        return self._roles

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole):  # type: ignore[override]
        if not index.isValid() or not (0 <= index.row() < len(self._rows)):
            return None
        key_i = role - int(Qt.UserRole)
        if 0 <= key_i < len(self._keys):
            return self._rows[index.row()].get(self._keys[key_i])
        return None

    def replace(self, rows: list[dict]) -> None:
        # A 60 Hz reset destroys QML MouseAreas mid-click, so skip no-ops.
        if rows == self._rows:
            return
        self.beginResetModel()
        self._rows = list(rows)
        self.endResetModel()
        self.countChanged.emit()


class TunerBackend(QObject):
    frameChanged = Signal()
    settingsChanged = Signal()

    def __init__(self, controller: TunerController, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._c = controller
        self._snap = controller.tick()
        self._string_model = DictListModel(("number", "letter", "accidental", "label", "active"), self)
        self._preset_model = DictListModel(("key", "name", "active"), self)
        self._device_model = DictListModel(("devIndex", "name", "active"), self)
        self._sync_models()
        self._timer = QTimer(self)
        self._timer.setInterval(16)
        self._timer.timeout.connect(self._on_tick)
        self._timer.start()

    def shutdown(self) -> None:
        self._timer.stop()
        self._c.shutdown()

    def _on_tick(self) -> None:
        self._snap = self._c.tick()
        self._sync_models()
        self.frameChanged.emit()

    def _sync_models(self) -> None:
        self._string_model.replace(self._snap.strings)
        self._preset_model.replace(self._snap.presets)
        self._device_model.replace(
            [
                {
                    "devIndex": -1 if idx is None else int(idx),
                    "name": name,
                    "active": idx == self._c.settings.input_device,
                }
                for idx, name in device_choices(self._c.devices)
            ]
        )

    def _settings_tick(self) -> None:
        self._c.settings = self._c.settings.clamped()
        self.settingsChanged.emit()
        self.frameChanged.emit()

    def _strings(self) -> DictListModel:
        return self._string_model

    def _presets(self) -> DictListModel:
        return self._preset_model

    def _devices(self) -> DictListModel:
        return self._device_model

    stringModel = Property(QObject, _strings, constant=True)
    presetModel = Property(QObject, _presets, constant=True)
    deviceModel = Property(QObject, _devices, constant=True)

    @Slot(str, result=str)
    def fontUrl(self, filename: str) -> str:
        return QUrl.fromLocalFile(str(_FONTS / filename)).toString()

    def _note_letter(self) -> str:
        return self._snap.note_letter

    def _note_accidental(self) -> str:
        return self._snap.note_accidental

    def _subtitle(self) -> str:
        return self._snap.subtitle

    def _cents(self) -> float:
        return float(self._snap.cents)

    def _cents_valid(self) -> bool:
        return self._snap.cents_valid

    def _in_tune(self) -> bool:
        return self._snap.in_tune

    def _locked(self) -> bool:
        return self._snap.locked

    def _confidence(self) -> float:
        return float(self._snap.confidence)

    def _energy(self) -> float:
        return float(self._snap.energy)

    def _preset_title(self) -> str:
        return self._snap.preset_title

    def _signal_bars(self) -> int:
        if self._snap.confidence <= 0.05:
            return 0
        return max(1, min(5, round(self._snap.confidence * 5)))

    def _energy_bars(self) -> int:
        if self._snap.energy <= 0.0005:
            return 0
        return max(1, min(5, round(min(1.0, self._snap.energy / 0.05) * 5)))

    def _cents_label(self) -> str:
        if not self._snap.cents_valid:
            return ""
        return f"{int(round(self._snap.cents)):+d}¢"

    def _lock_label(self) -> str:
        return "LOCKED" if self._snap.locked else "LISTENING"

    noteLetter = Property(str, _note_letter, notify=frameChanged)
    noteAccidental = Property(str, _note_accidental, notify=frameChanged)
    subtitle = Property(str, _subtitle, notify=frameChanged)
    cents = Property(float, _cents, notify=frameChanged)
    centsValid = Property(bool, _cents_valid, notify=frameChanged)
    inTune = Property(bool, _in_tune, notify=frameChanged)
    locked = Property(bool, _locked, notify=frameChanged)
    confidence = Property(float, _confidence, notify=frameChanged)
    energy = Property(float, _energy, notify=frameChanged)
    presetTitle = Property(str, _preset_title, notify=frameChanged)
    signalBars = Property(int, _signal_bars, notify=frameChanged)
    energyBars = Property(int, _energy_bars, notify=frameChanged)
    centsLabel = Property(str, _cents_label, notify=frameChanged)
    lockLabel = Property(str, _lock_label, notify=frameChanged)

    def _show_settings(self) -> bool:
        return self._c.show_settings

    def _picking_device(self) -> bool:
        return self._c.picking_device

    def _notice(self) -> str:
        return self._c.notice

    def _a4(self) -> int:
        return int(self._c.settings.a4_hz)

    def _in_tune_cents(self) -> float:
        return float(self._c.settings.in_tune_cents)

    def _string_auto(self) -> bool:
        return self._c.settings.string_auto

    def _response(self) -> str:
        return self._c.settings.response

    def _needle(self) -> bool:
        return self._c.settings.needle_smoothing

    def _show_signal(self) -> bool:
        return self._c.settings.show_signal_meter

    def _cents_range(self) -> int:
        return int(self._c.settings.cents_range)

    def _min_conf(self) -> float:
        return float(self._c.settings.min_confidence)

    def _gate(self) -> float:
        return float(self._c.settings.signal_energy_floor)

    def _ring(self) -> float:
        return float(self._c.settings.ringing_energy_floor)

    def _device_label(self) -> str:
        return device_label(self._c.settings, self._c.devices)

    def _version(self) -> str:
        return APP_VERSION

    showSettings = Property(bool, _show_settings, notify=settingsChanged)
    pickingDevice = Property(bool, _picking_device, notify=settingsChanged)
    notice = Property(str, _notice, notify=settingsChanged)
    a4Hz = Property(int, _a4, notify=settingsChanged)
    inTuneCents = Property(float, _in_tune_cents, notify=settingsChanged)
    stringAuto = Property(bool, _string_auto, notify=settingsChanged)
    response = Property(str, _response, notify=settingsChanged)
    needleSmoothing = Property(bool, _needle, notify=settingsChanged)
    showSignalMeter = Property(bool, _show_signal, notify=settingsChanged)
    centsRange = Property(int, _cents_range, notify=settingsChanged)
    minConfidence = Property(float, _min_conf, notify=settingsChanged)
    signalGate = Property(float, _gate, notify=settingsChanged)
    ringingHold = Property(float, _ring, notify=settingsChanged)
    deviceLabel = Property(str, _device_label, notify=settingsChanged)
    appVersion = Property(str, _version, constant=True)

    @Slot(int)
    def selectString(self, number: int) -> None:
        self._c.select_string(number)
        self._settings_tick()

    @Slot()
    def autoString(self) -> None:
        self._c.auto_string()
        self._settings_tick()

    @Slot(str)
    def selectPreset(self, key: str) -> None:
        self._c.select_preset(key)
        self.frameChanged.emit()

    @Slot(int)
    def cyclePreset(self, step: int) -> None:
        self._c.cycle_preset(step)
        self.frameChanged.emit()

    @Slot()
    def openSettings(self) -> None:
        self._c.open_settings()
        self._sync_models()
        self._settings_tick()

    @Slot()
    def closeSettings(self) -> None:
        self._c.close_settings()
        self._settings_tick()

    @Slot()
    def openDevicePicker(self) -> None:
        self._c.open_device_picker()
        self._sync_models()
        self._settings_tick()

    @Slot()
    def closeDevicePicker(self) -> None:
        self._c.close_device_picker()
        self._settings_tick()

    @Slot(int)
    def selectDevice(self, dev_index: int) -> None:
        self._c.select_device(None if dev_index < 0 else dev_index)
        self._sync_models()
        self._settings_tick()

    @Slot()
    def calibrate(self) -> None:
        self._c.calibrate()
        self._settings_tick()

    @Slot(int)
    def nudgeA4(self, delta: int) -> None:
        self._c.nudge_a4(delta)
        self._settings_tick()

    @Slot(float)
    def setInTune(self, cents: float) -> None:
        self._c.set_in_tune(cents)
        self._settings_tick()

    @Slot(str)
    def setResponse(self, key: str) -> None:
        self._c.set_response(key)
        self._settings_tick()

    @Slot(bool)
    def setStringAuto(self, auto: bool) -> None:
        self._c.set_string_auto(auto)
        self._settings_tick()

    @Slot(bool)
    def setNeedleSmoothing(self, on: bool) -> None:
        self._c.set_needle_smoothing(on)
        self._settings_tick()

    @Slot(bool)
    def setShowSignal(self, on: bool) -> None:
        self._c.set_show_signal(on)
        self._settings_tick()

    @Slot(int)
    def setCentsRange(self, span: int) -> None:
        self._c.set_cents_range(span)
        self._settings_tick()

    @Slot(float)
    def setMinConfidence(self, value: float) -> None:
        self._c.set_min_confidence(value)
        self._settings_tick()

    @Slot(float)
    def setSignalGate(self, value: float) -> None:
        self._c.set_signal_gate(value)
        self._settings_tick()

    @Slot(float)
    def setRingingHold(self, value: float) -> None:
        self._c.set_ringing_hold(value)
        self._settings_tick()

    @Slot()
    def resetDefaults(self) -> None:
        self._c.reset_defaults()
        self._settings_tick()
