"""Pitch detection via NumPy YIN (not FFT).

YIN uses an analysis window of :data:`ANALYSIS_SIZE` samples but each
:meth:`PitchDetector.detect` call must pass exactly :data:`HOP_SIZE` samples.
Capture block size must match ``hop_size``.
"""

from __future__ import annotations

import numpy as np

ANALYSIS_SIZE = 4096
"""YIN window in samples (~2.8 periods of B0 at 44.1 kHz)."""

HOP_SIZE = 1024
"""Samples per :meth:`PitchDetector.detect` call (~23 ms at 44.1 kHz)."""

_RMS_FLOOR = 0.006
_YIN_TOLERANCE = 0.15


def _yin_cmndf(frame: np.ndarray, tau_min: int, tau_max: int) -> np.ndarray:
    """Cumulative mean-normalized difference for lags ``tau_min..tau_max``."""
    w = int(frame.shape[0])
    tau_max = min(tau_max, w // 2)
    if tau_max < tau_min:
        return np.empty(0, dtype=np.float64)

    x = frame.astype(np.float64, copy=False)
    d = np.empty(tau_max + 1, dtype=np.float64)
    d[0] = 0.0
    for tau in range(1, tau_max + 1):
        diff = x[: w - tau] - x[tau:w]
        d[tau] = float(np.dot(diff, diff))

    cmndf = np.ones(tau_max + 1, dtype=np.float64)
    running = 0.0
    for tau in range(1, tau_max + 1):
        running += d[tau]
        cmndf[tau] = 1.0 if running == 0.0 else d[tau] * tau / running
    return cmndf


def _parabolic_tau(cmndf: np.ndarray, tau: int) -> float:
    """Sub-sample refine of a CMNDF valley at integer lag ``tau``."""
    if tau <= 0 or tau >= len(cmndf) - 1:
        return float(tau)
    y0 = float(cmndf[tau - 1])
    y1 = float(cmndf[tau])
    y2 = float(cmndf[tau + 1])
    denom = 2.0 * (y0 - 2.0 * y1 + y2)
    if abs(denom) < 1e-12:
        return float(tau)
    return float(tau) + (y0 - y2) / denom


def _yin_hz_confidence(
    frame: np.ndarray,
    sample_rate: float,
    *,
    min_hz: float,
    max_hz: float,
    tolerance: float = _YIN_TOLERANCE,
) -> tuple[float, float]:
    """Return ``(hz, confidence)`` from one analysis window, or ``(0, 0)``."""
    tau_min = max(2, int(sample_rate / max_hz))
    tau_max = int(sample_rate / min_hz)
    cmndf = _yin_cmndf(frame, tau_min, tau_max)
    if cmndf.size <= tau_min + 1:
        return 0.0, 0.0

    tau_max = min(tau_max, len(cmndf) - 1)
    best_tau = 0
    for tau in range(tau_min, tau_max):
        if cmndf[tau] < tolerance:
            while tau + 1 <= tau_max and cmndf[tau + 1] < cmndf[tau]:
                tau += 1
            best_tau = tau
            break

    if best_tau == 0:
        # No valley under tolerance — take global min in range (weaker lock).
        search = cmndf[tau_min : tau_max + 1]
        if search.size == 0:
            return 0.0, 0.0
        best_tau = int(tau_min + int(np.argmin(search)))
        if cmndf[best_tau] >= 1.0:
            return 0.0, 0.0

    tau_f = _parabolic_tau(cmndf, best_tau)
    if tau_f <= 0.0:
        return 0.0, 0.0
    hz = float(sample_rate / tau_f)
    confidence = float(max(0.0, min(1.0, 1.0 - cmndf[best_tau])))
    return hz, confidence


class PitchDetector:
    """Streaming YIN detector for bass fundamentals (~31–220 Hz).

    Args:
        sample_rate: Audio sample rate in hertz (typically 44100).
        buffer_size: YIN analysis window. Must be ≥ ``hop_size``.
        hop_size: Frame length passed to :meth:`detect`. Must match capture.
        min_hz: Reject estimates below this (default covers 5-string B0).
        max_hz: Reject estimates above this. 400 Hz includes D's 3rd harmonic
            (~220 Hz) and G's 3rd (~294 Hz); :func:`~core.notes.harmonic_cents`
            maps those back to the open string.
    """

    def __init__(
        self,
        sample_rate: float,
        *,
        buffer_size: int = ANALYSIS_SIZE,
        hop_size: int = HOP_SIZE,
        min_hz: float = 25.0,
        max_hz: float = 400.0,
    ) -> None:
        if buffer_size < hop_size:
            raise ValueError("buffer_size must be ≥ hop_size")
        self.hop_size = hop_size
        self._sample_rate = float(sample_rate)
        self._buffer_size = buffer_size
        self._min_hz = min_hz
        self._max_hz = max_hz
        self._buf = np.zeros(buffer_size, dtype=np.float32)
        self._filled = 0

    def detect(self, samples: np.ndarray) -> tuple[float, float]:
        """Estimate fundamental frequency for one hop.

        Args:
            samples: Mono float32 frame of length ``self.hop_size``.

        Returns:
            ``(hz, confidence)``. Both are ``0.0`` if the estimate is outside
            ``[min_hz, max_hz]``.

        Raises:
            ValueError: If ``len(samples)`` is not ``hop_size``.
        """
        if len(samples) != self.hop_size:
            raise ValueError(
                f"pitch hop_size is {self.hop_size}, got {len(samples)} samples"
            )

        hop = np.asarray(samples, dtype=np.float32).reshape(-1)
        if self._filled < self._buffer_size:
            start = self._filled
            end = min(self._buffer_size, self._filled + self.hop_size)
            take = end - start
            self._buf[start:end] = hop[:take]
            self._filled = end
            if self._filled < self._buffer_size:
                return 0.0, 0.0
        else:
            self._buf[:-self.hop_size] = self._buf[self.hop_size :]
            self._buf[-self.hop_size :] = hop

        rms = float(np.sqrt(np.mean(np.square(hop))))
        if rms < _RMS_FLOOR:
            return 0.0, 0.0

        pitch_hz, confidence = _yin_hz_confidence(
            self._buf,
            self._sample_rate,
            min_hz=self._min_hz,
            max_hz=self._max_hz,
        )

        if not (self._min_hz <= pitch_hz <= self._max_hz):
            return 0.0, 0.0

        return pitch_hz, confidence
