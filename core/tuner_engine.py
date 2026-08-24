"""Pure tuner logic — no audio or UI imports.

Port this module to C/C++ for pedal-module firmware; keep I/O in ``audio`` / ``ui``.
"""

from __future__ import annotations

import math
import statistics
from collections import deque
from dataclasses import dataclass

from core.notes import harmonic_cents
from core.presets import StringTarget, TuningPreset


@dataclass(frozen=True)
class TunerReading:
    """One analysis frame after gating, string match, and in-tune check.

    Attributes:
        detected_hz: Pitch estimate from the detector (may be 0 when gated).
        target: Matched string, or ``None`` if unlocked / ungated.
        cents: Signed cents vs ``target`` (harmonic-folded); ``nan`` when unlocked.
        in_tune: True when ``abs(cents)`` is within the in-tune threshold.
        confidence: Detector confidence in ``[0, 1]``.
    """

    detected_hz: float
    target: StringTarget | None
    cents: float
    in_tune: bool
    confidence: float


def nearest_string(
    detected_hz: float,
    preset: TuningPreset,
    *,
    max_cents: float = 150.0,
) -> tuple[StringTarget, float] | None:
    """Pick the preset string closest to ``detected_hz``.

    Compares against harmonics 1–5 of each open string (YIN often reports
    2× or 3×; D's 3rd harmonic is ~220 Hz and would otherwise look like A).

    Args:
        detected_hz: Estimated frequency in hertz.
        preset: Active tuning.
        max_cents: Ignore strings farther than this after harmonic match
            (default 150¢, 1.5 semitones).

    Returns:
        ``(target, cents)`` for the nearest string, or ``None`` if none are
        within ``max_cents``.
    """
    best: tuple[StringTarget, float] | None = None
    best_n = 99

    for target in preset.strings:
        cents, n = harmonic_cents(detected_hz, target.frequency_hz)
        if math.isnan(cents) or abs(cents) > max_cents:
            continue
        if best is None or abs(cents) < abs(best[1]) - 1.0 or (
            abs(cents) <= abs(best[1]) + 1.0 and n < best_n
        ):
            best = (target, cents)
            best_n = n

    return best


def analyze_pitch(
    detected_hz: float,
    preset: TuningPreset,
    *,
    confidence: float,
    min_confidence: float = 0.25,
    in_tune_cents: float = 5.0,
    manual_string: StringTarget | None = None,
) -> TunerReading:
    """Gate a pitch estimate and map it onto the active tuning.

    Args:
        detected_hz: Estimated fundamental in hertz.
        preset: Active tuning used for auto string detect.
        confidence: Detector confidence in ``[0, 1]``.
        min_confidence: Below this, return an unlocked reading.
        in_tune_cents: ``in_tune`` if ``abs(cents)`` is at most this value.
        manual_string: If set, skip auto-detect and compare against this string.

    Returns:
        A :class:`TunerReading`. ``target`` is ``None`` when gated or unmatched.
    """
    if confidence < min_confidence or detected_hz <= 0:
        return TunerReading(
            detected_hz=detected_hz,
            target=None,
            cents=float("nan"),
            in_tune=False,
            confidence=confidence,
        )

    if manual_string is not None:
        target = manual_string
        cents = harmonic_cents(detected_hz, target.frequency_hz)[0]
    else:
        match = nearest_string(detected_hz, preset)
        if match is None:
            return TunerReading(
                detected_hz=detected_hz,
                target=None,
                cents=float("nan"),
                in_tune=False,
                confidence=confidence,
            )
        target, cents = match

    return TunerReading(
        detected_hz=detected_hz,
        target=target,
        cents=cents,
        in_tune=abs(cents) <= in_tune_cents,
        confidence=confidence,
    )


class TunerSmoother:
    """Stabilize pitch for a usable tuner needle.

    Applies a median window, EMA, lock-until-silence, in-tune Schmitt
    trigger, and hold-last on brief dropouts. I/O-free.

    Args:
        window: Median length in hops (odd recommended).
        alpha: EMA mix after the median. ``1.0`` = no extra smoothing.
        hold_frames: Keep the last good lock this many gated hops.
        switch_confirm: Unused for auto-switch (lock holds until silence).
        string_hysteresis_cents: Unused for auto-switch (lock holds until silence).
        min_confidence: Gate; hops below this are treated as dropouts.
        in_tune_cents: Enter in-tune at this |cents|. Exit at +2¢ more.
        signal_energy_floor: Minimum RMS to accept a pitch (blocks room noise).
        ringing_energy_floor: Hold last lock while RMS stays above this during decay.
        cents_alpha: EMA weight for displayed cents.
        max_cents_step: Max cents change per hop (limits display jumps).
        max_outlier_cents: Ignore frames farther than this; hold last reading.
    """

    def __init__(
        self,
        *,
        window: int = 9,
        alpha: float = 0.15,
        hold_frames: int = 18,
        switch_confirm: int = 4,
        string_hysteresis_cents: float = 35.0,
        min_confidence: float = 0.25,
        in_tune_cents: float = 5.0,
        signal_energy_floor: float = 0.008,
        ringing_energy_floor: float = 0.014,
        cents_alpha: float = 0.18,
        max_cents_step: float = 2.0,
        max_outlier_cents: float = 50.0,
    ) -> None:
        self._window = window
        self._alpha = alpha
        self._hold_frames = hold_frames
        self._switch_confirm = switch_confirm
        self._string_hysteresis_cents = string_hysteresis_cents
        self._min_confidence = min_confidence
        self._in_tune_cents = in_tune_cents
        self._in_tune_exit_cents = in_tune_cents + 2.0
        self._signal_energy_floor = signal_energy_floor
        self._ringing_energy_floor = ringing_energy_floor
        self._cents_alpha = cents_alpha
        self._max_cents_step = max_cents_step
        self._max_outlier_cents = max_outlier_cents

        self._hz_window: deque[float] = deque(maxlen=window)
        self._smoothed_hz: float | None = None
        self._smoothed_cents: float | None = None
        self._locked: StringTarget | None = None
        self._switch_votes = 0
        self._misses = 0
        self._was_in_tune = False
        self._last: TunerReading | None = None

    def configure(
        self,
        *,
        alpha: float | None = None,
        min_confidence: float | None = None,
        in_tune_cents: float | None = None,
        signal_energy_floor: float | None = None,
        ringing_energy_floor: float | None = None,
        cents_alpha: float | None = None,
        max_cents_step: float | None = None,
    ) -> None:
        """Update live parameters without clearing lock/window state."""
        if alpha is not None:
            self._alpha = alpha
        if min_confidence is not None:
            self._min_confidence = min_confidence
        if in_tune_cents is not None:
            self._in_tune_cents = in_tune_cents
            self._in_tune_exit_cents = in_tune_cents + 2.0
        if signal_energy_floor is not None:
            self._signal_energy_floor = signal_energy_floor
        if ringing_energy_floor is not None:
            self._ringing_energy_floor = ringing_energy_floor
        if cents_alpha is not None:
            self._cents_alpha = cents_alpha
        if max_cents_step is not None:
            self._max_cents_step = max_cents_step

    def reset(self) -> None:
        """Clear window, lock, and hold state (e.g. after a preset change)."""
        self._hz_window.clear()
        self._smoothed_hz = None
        self._smoothed_cents = None
        self._locked = None
        self._switch_votes = 0
        self._misses = 0
        self._was_in_tune = False
        self._last = None

    def update(
        self,
        detected_hz: float,
        confidence: float,
        preset: TuningPreset,
        *,
        manual_string: StringTarget | None = None,
        energy: float = 0.0,
    ) -> TunerReading:
        """Ingest one detector hop and return a display-stable reading.

        Args:
            detected_hz: Raw YIN estimate in hertz.
            confidence: Detector confidence in ``[0, 1]``.
            preset: Active tuning.
            manual_string: Force this string; still smoothed.
            energy: RMS of the capture hop. Loud but unpitched frames keep
                the last lock (typical as a bass string decays).

        Returns:
            Smoothed :class:`TunerReading`.
        """
        valid = (
            detected_hz > 0
            and energy >= self._signal_energy_floor
            and confidence >= self._min_confidence
        )

        if not valid:
            if (
                energy >= self._ringing_energy_floor
                and self._last is not None
                and self._last.target is not None
            ):
                return self._last
            self._misses += 1
            if (
                self._last is not None
                and self._last.target is not None
                and self._misses <= self._hold_frames
            ):
                return self._last
            self.reset()
            return TunerReading(
                detected_hz=0.0,
                target=None,
                cents=float("nan"),
                in_tune=False,
                confidence=confidence,
            )

        self._misses = 0

        if self._locked is not None:
            preview, _ = harmonic_cents(detected_hz, self._locked.frequency_hz)
            if not math.isnan(preview) and abs(preview) > self._max_outlier_cents:
                if self._last is not None and self._last.target is not None:
                    return self._last

        self._hz_window.append(detected_hz)
        median_hz = statistics.median(self._hz_window)
        if self._smoothed_hz is None:
            self._smoothed_hz = median_hz
        else:
            self._smoothed_hz = (
                self._alpha * median_hz + (1.0 - self._alpha) * self._smoothed_hz
            )

        target = self._resolve_string(self._smoothed_hz, preset, manual_string)
        if target is None:
            reading = TunerReading(
                detected_hz=self._smoothed_hz,
                target=None,
                cents=float("nan"),
                in_tune=False,
                confidence=confidence,
            )
            self._last = reading
            return reading

        raw_cents = harmonic_cents(self._smoothed_hz, target.frequency_hz)[0]
        if abs(raw_cents) > self._max_outlier_cents:
            if (
                self._last is not None
                and self._last.target is not None
                and self._last.target.note == target.note
            ):
                return self._last
        cents = self._smooth_cents(raw_cents, target)
        in_tune = self._schmitt_in_tune(raw_cents)
        self._was_in_tune = in_tune
        reading = TunerReading(
            detected_hz=self._smoothed_hz,
            target=target,
            cents=cents,
            in_tune=in_tune,
            confidence=confidence,
        )
        self._last = reading
        return reading

    def _smooth_cents(self, cents: float, target: StringTarget) -> float:
        if math.isnan(cents):
            return cents
        if (
            self._smoothed_cents is None
            or self._locked is None
            or self._locked.note != target.note
        ):
            if abs(cents) <= self._max_outlier_cents:
                self._smoothed_cents = cents
                return cents
            if (
                self._last is not None
                and self._last.target is not None
                and self._last.target.note == target.note
            ):
                return self._last.cents
            self._smoothed_cents = 0.0
            return 0.0
        delta = cents - self._smoothed_cents
        step = max(-self._max_cents_step, min(self._max_cents_step, delta))
        self._smoothed_cents += self._cents_alpha * step
        return self._smoothed_cents

    def _schmitt_in_tune(self, cents: float) -> bool:
        if math.isnan(cents):
            return False
        limit = (
            self._in_tune_exit_cents if self._was_in_tune else self._in_tune_cents
        )
        return abs(cents) <= limit

    def _resolve_string(
        self,
        hz: float,
        preset: TuningPreset,
        manual_string: StringTarget | None,
    ) -> StringTarget | None:
        if manual_string is not None:
            self._locked = manual_string
            self._switch_votes = 0
            return manual_string

        if self._locked is not None:
            return self._locked

        match = nearest_string(hz, preset)
        if match is None:
            return None
        self._locked = match[0]
        self._switch_votes = 0
        return self._locked

