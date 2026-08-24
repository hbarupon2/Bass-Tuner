# Bass Tuner

Touchscreen-friendly bass guitar tuner (CLI + Qt Quick UI). Pure NumPy YIN pitch detection, built-in tuning presets, settings for A4 / thresholds / input device.

**License:** [Apache License 2.0](LICENSE) — see also [NOTICE](NOTICE) and [THIRD_PARTY.md](THIRD_PARTY.md).

## Requirements

- Python 3.11+
- `numpy`, `sounddevice`, `PySide6-Essentials` (see `requirements.txt`)

## Install

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Raspberry Pi OS

```bash
sudo apt update
# PortAudio for sounddevice; Qt comes via pip PySide6-Essentials
sudo apt install python3-venv libportaudio2
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
python main.py --list-devices
python main.py --device N              # CLI tuner
python main.py --ui --device N         # Qt Quick UI (1024×600)
python main.py --ui-demo              # UI with synthetic pitch (no audio)
```

CLI keys: `1–6` force string (low→high), `0` auto, `[` `]` cycle preset, Ctrl+C quit.

Settings persist under `~/.config/bass-tuner/settings.json`.

## Layout

| Path | Role |
|------|------|
| `core/` | Pure tuner logic (no audio/UI imports) |
| `audio/` | Capture + NumPy YIN |
| `config/` | Built-in presets + user settings |
| `ui/` | Qt Quick UI (`qml/`, controller) |
| `tests/` | Unit tests |

```bash
python -m unittest discover -s tests -v
```
