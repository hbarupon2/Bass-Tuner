#!/usr/bin/env python3
"""Bass tuner — CLI and Qt Quick touchscreen UI.

Run with a USB audio interface::

    python main.py --list-devices
    python main.py --device N
    python main.py --ui --device N
    python main.py --ui-demo

Live keys (CLI): ``1–6`` force string (low→high), ``0`` auto, ``[ ]`` preset, Ctrl+C quit.
"""

from __future__ import annotations

import argparse
import select
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from cli import CliSession, apply_key
from core.presets import load_presets
from core.tuner_engine import TunerReading, TunerSmoother


def format_reading(reading: TunerReading) -> str:
    """Format one tuner frame for a single terminal line.

    Args:
        reading: Output of :class:`~core.tuner_engine.TunerSmoother`.

    Returns:
        Fixed-width status string (note, Hz, cents, lock, confidence).
    """
    if reading.target is None:
        return f"---  {reading.detected_hz:6.1f} Hz  (no lock)  conf={reading.confidence:.2f}"

    lock = "OK" if reading.in_tune else ".."
    cents_disp = int(round(reading.cents))
    return (
        f"{reading.target.note:>3}  {reading.detected_hz:6.1f} Hz  "
        f"{cents_disp:+4d}c  [{lock}]  conf={reading.confidence:.2f}"
    )


def _poll_key() -> str | None:
    """Read one waiting stdin character, or ``None`` if idle."""
    if not sys.stdin.isatty():
        return None
    ready, _, _ = select.select([sys.stdin], [], [], 0)
    if not ready:
        return None
    return sys.stdin.read(1)


def main() -> None:
    """Parse CLI args, stream audio, and print live tuner readings."""
    parser = argparse.ArgumentParser(description="Bass tuner")
    parser.add_argument("--device", type=int, default=None, help="sounddevice input index")
    parser.add_argument("--list-devices", action="store_true")
    parser.add_argument("--preset", default="standard_4", help="preset key from presets.json")
    parser.add_argument("--ui", action="store_true", help="launch Qt Quick touchscreen UI")
    parser.add_argument("--ui-demo", action="store_true", help="UI with fake pitch (no audio)")
    args = parser.parse_args()

    if args.list_devices:
        import sounddevice as sd

        print(sd.query_devices())
        return

    presets = load_presets(ROOT / "config" / "presets.json")
    if args.preset not in presets:
        print(f"Unknown preset {args.preset!r}. Options: {', '.join(presets)}")
        sys.exit(1)

    if args.ui or args.ui_demo:
        from ui.qt_ui import run_ui

        run_ui(
            presets_path=ROOT / "config" / "presets.json",
            preset_key=args.preset,
            device=args.device,
            demo=args.ui_demo,
        )
        return

    session = CliSession(
        presets=presets,
        preset_key=args.preset,
        smoother=TunerSmoother(),
    )
    from audio.capture import stream_audio
    from audio.pitch import PitchDetector

    detector = PitchDetector(44100)
    last_print = 0.0

    def on_audio(samples, sample_rate: float) -> None:
        nonlocal last_print
        pitch_hz, confidence = detector.detect(samples)
        energy = float(np.sqrt(np.mean(np.square(samples))))
        reading = session.smoother.update(
            pitch_hz,
            confidence,
            session.preset,
            energy=energy,
            manual_string=session.manual_string(),
        )

        now = time.monotonic()
        if now - last_print < 0.05:
            return
        last_print = now

        line = format_reading(reading)
        print(
            f"\r{session.preset.name:<16} {session.mode_label():<4} {line}   ",
            end="",
            flush=True,
        )

    print(f"Preset: {session.preset.name}  |  strings: {' '.join(s.note for s in session.preset.strings)}")
    print("Keys: 1-6 string  0 auto  [ ] preset  Ctrl+C quit")
    print("Listening…\n")

    fd = None
    old_term = None
    if sys.stdin.isatty():
        import termios
        import tty

        fd = sys.stdin.fileno()
        old_term = termios.tcgetattr(fd)
        tty.setcbreak(fd)

    try:
        with stream_audio(on_audio, device=args.device, block_size=detector.hop_size):
            try:
                while True:
                    key = _poll_key()
                    if key:
                        message = apply_key(session, key)
                        if message:
                            print(f"\n{message}")
                            print(
                                f"strings: {' '.join(s.note for s in session.preset.strings)}"
                            )
                    time.sleep(0.05)
            except KeyboardInterrupt:
                print("\nStopped.")
    finally:
        if fd is not None and old_term is not None:
            import termios

            termios.tcsetattr(fd, termios.TCSADRAIN, old_term)


if __name__ == "__main__":
    main()
