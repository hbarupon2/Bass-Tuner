"""Mono input capture via PortAudio / sounddevice."""

from __future__ import annotations

from collections.abc import Callable

import numpy as np
import sounddevice as sd

# Default hop matches audio.pitch.HOP_SIZE.
_DEFAULT_BLOCK = 1024


def stream_audio(
    callback: Callable[[np.ndarray, float], None],
    *,
    sample_rate: int = 44100,
    block_size: int | None = None,
    device: int | None = None,
) -> sd.InputStream:
    """Open a mono input stream and invoke ``callback`` per block.

    ``block_size`` must equal the pitch detector hop size (default 1024,
    :data:`~audio.pitch.HOP_SIZE`). Use as a context manager.

    Args:
        callback: ``callback(samples, sample_rate)`` with mono float32 samples.
        sample_rate: Capture rate in hertz.
        block_size: Frames per callback. Must match :class:`~audio.pitch.PitchDetector.hop_size`.
        device: sounddevice input index, or ``None`` for the default device.

    Returns:
        An unstarted :class:`sounddevice.InputStream` (the ``with`` block starts it).
    """
    if block_size is None:
        try:
            from audio.pitch import HOP_SIZE

            block_size = HOP_SIZE
        except ImportError:
            block_size = _DEFAULT_BLOCK

    def _wrap(indata: np.ndarray, _frames: int, _time, _status) -> None:
        if _status:
            print(_status)
        mono = indata[:, 0].astype(np.float32, copy=False)
        callback(mono, float(sample_rate))

    return sd.InputStream(
        samplerate=sample_rate,
        blocksize=block_size,
        channels=1,
        dtype="float32",
        device=device,
        callback=_wrap,
    )


def list_input_devices() -> list[tuple[int, str]]:
    """Return ``(index, name)`` for devices that have at least one input channel.

    Safe to call without opening a capture stream.
    """
    devices: list[tuple[int, str]] = []
    try:
        raw = sd.query_devices()
    except Exception:
        return devices
    for i, dev in enumerate(raw):
        try:
            channels = int(dev.get("max_input_channels", 0))
        except (TypeError, ValueError, AttributeError):
            continue
        if channels > 0:
            devices.append((i, str(dev["name"])))
    return devices
