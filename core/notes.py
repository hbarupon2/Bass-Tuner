"""Note ↔ frequency conversion for 12-tone equal temperament.

A4 is 440 Hz unless an alternate concert pitch is passed in.
"""

from __future__ import annotations

import math
import re

A4_HZ = 440.0
"""Concert pitch: frequency of A4 in hertz."""

NOTE_PATTERN = re.compile(r"^([A-Ga-g])([#b]?)(-?\d+)$")
"""Scientific pitch notation, e.g. ``E1``, ``Bb0``, ``F#2``."""

CHROMATIC = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
FLAT_TO_SHARP = {"Db": "C#", "Eb": "D#", "Gb": "F#", "Ab": "G#", "Bb": "A#"}


def normalize_note(note: str) -> str:
    """Return scientific pitch with a sharp accidental if needed.

    Args:
        note: Pitch name such as ``E1`` or ``Eb1``.

    Returns:
        Normalized name, e.g. ``Eb1`` → ``D#1``.

    Raises:
        ValueError: If ``note`` is not valid scientific pitch notation.
    """
    match = NOTE_PATTERN.match(note.strip())
    if not match:
        raise ValueError(f"Invalid note: {note!r}")

    letter, accidental, octave = match.groups()
    name = letter.upper() + accidental
    if name in FLAT_TO_SHARP:
        name = FLAT_TO_SHARP[name]

    if name not in CHROMATIC:
        raise ValueError(f"Unknown note name: {note!r}")

    return f"{name}{octave}"


def note_to_midi(note: str) -> int:
    """Convert a note name to a MIDI note number.

    MIDI 69 is A4. MIDI 0 is C-1.

    Args:
        note: Scientific pitch notation.

    Returns:
        MIDI note number.

    Raises:
        ValueError: If ``note`` is invalid.
    """
    normalized = normalize_note(note)
    match = NOTE_PATTERN.match(normalized)
    if not match:
        raise ValueError(f"Invalid note: {note!r}")

    letter, accidental, octave_str = match.groups()
    octave = int(octave_str)
    name = letter.upper() + accidental
    return CHROMATIC.index(name) + (octave + 1) * 12


def note_to_hz(note: str, a4_hz: float = A4_HZ) -> float:
    """Convert a note name to frequency in hertz (12-TET).

    Args:
        note: Scientific pitch notation, e.g. ``E1``.
        a4_hz: Concert pitch for A4. Defaults to 440 Hz.

    Returns:
        Frequency in hertz.
    """
    return a4_hz * (2 ** ((note_to_midi(note) - note_to_midi("A4")) / 12))


def cents_off(detected_hz: float, target_hz: float) -> float:
    """Signed cents deviation of a detected frequency from a target.

    Positive is sharp; negative is flat.

        cents = 1200 * log2(detected / target)

    Args:
        detected_hz: Measured frequency in hertz.
        target_hz: Expected frequency in hertz.

    Returns:
        Cents offset, or ``nan`` if either frequency is not positive.
    """
    if detected_hz <= 0 or target_hz <= 0:
        return float("nan")
    return 1200.0 * math.log2(detected_hz / target_hz)


def octave_cents(detected_hz: float, target_hz: float) -> float:
    """Cents offset ignoring octave errors (YIN often reports 2× or 4×).

    Wraps :func:`cents_off` into ``(-600, 600]``. ``82 Hz`` vs ``E1``
    (41.2 Hz) is ~0¢, not ~1200¢.

    Args:
        detected_hz: Measured frequency in hertz.
        target_hz: Open-string frequency in hertz.

    Returns:
        Wrapped cents, or ``nan`` if either frequency is not positive.
    """
    raw = cents_off(detected_hz, target_hz)
    if math.isnan(raw):
        return raw
    return (raw + 600.0) % 1200.0 - 600.0


def harmonic_cents(
    detected_hz: float,
    target_hz: float,
    *,
    max_n: int = 5,
) -> tuple[float, int]:
    """Cents treating ``detected_hz`` as the n-th harmonic of ``target_hz``.

    YIN on bass D often reports the 3rd harmonic (~220 Hz, A3) instead of
    D2 (~73 Hz). Octave wrapping cannot fix that (3× is a fifth + octave).

    On a near-tie, the **lowest** ``n`` wins so D (n=3) beats A (n=4) at 220 Hz.

    Args:
        detected_hz: Measured frequency in hertz.
        target_hz: Open-string frequency in hertz.
        max_n: Highest harmonic to try (inclusive).

    Returns:
        ``(cents, n)`` for the best n, or ``(nan, 0)`` if inputs are invalid.
    """
    best: tuple[float, int, float] | None = None
    for n in range(1, max_n + 1):
        cents = cents_off(detected_hz, target_hz * n)
        if math.isnan(cents):
            return float("nan"), 0
        cand = (abs(cents), n, cents)
        if best is None or cand < best:
            best = cand
    assert best is not None
    return best[2], best[1]
