# Copyright (c) 2026, Yasser Bousrih and contributors
# For license information, please see license.txt

"""Time-overlap primitives used by both the Booking controller (validation)
and the availability API (slot generation). Kept dependency-free so they can
be unit-tested without a running Frappe site.
"""

from datetime import time, timedelta
from typing import Iterable, Tuple

# Statuses that do NOT occupy a slot — overlap checks ignore them.
CANCELLED_STATES = frozenset({"Cancelled", "No-Show"})


def to_minutes(t) -> int:
    """Convert a `datetime.time` (or hour*60+min scalar from tests) to minutes since midnight."""
    if isinstance(t, (int, float)):
        return int(t)
    return t.hour * 60 + t.minute + (1 if t.second >= 30 else 0)


def times_overlap(a_start, a_end, b_start, b_end) -> bool:
    """True iff half-open intervals [a_start, a_end) and [b_start, b_end) share any minute.

    Half-open: a booking ending at 10:00 does not conflict with one starting at 10:00.
    """
    a1, a2 = to_minutes(a_start), to_minutes(a_end)
    b1, b2 = to_minutes(b_start), to_minutes(b_end)
    return a1 < b2 and b1 < a2


def add_minutes_to_time(t, minutes: int):
    """Return a `datetime.time` that is `minutes` after `t`. Wraps past midnight."""
    base = timedelta(hours=to_minutes(t) // 60, minutes=to_minutes(t) % 60)
    new = base + timedelta(minutes=int(minutes))
    total_minutes = new.total_seconds() // 60
    return time(hour=int(total_minutes // 60) % 24, minute=int(total_minutes % 60))


def compute_available_slots(
    working_hours: Iterable[Tuple[str, int, int]],
    service_duration_min: int,
    existing_bookings: Iterable[Tuple[int, int]],
    slot_buffer_min: int = 0,
    slot_step_min: int = 5,
) -> list:
    """Pure function: compute the list of free slot start times for one day.

    Args:
        working_hours: iterable of (weekday, start_min, end_min) tuples in minutes
            since midnight. The caller filters by weekday before calling.
        service_duration_min: how long the service runs, in minutes.
        existing_bookings: iterable of (start_min, end_min) tuples (cancelled
            bookings must be filtered out by the caller).
        slot_buffer_min: optional buffer between bookings (e.g. 5 min cleanup).
        slot_step_min: granularity of slot starts (e.g. 5 or 15 minutes).

    Returns:
        Sorted list of start minutes (int) for valid slots. May be empty.
    """
    if service_duration_min <= 0:
        return []

    slots: list = []
    busy = sorted(existing_bookings)  # (start, end)

    for _weekday, wh_start, wh_end in working_hours:
        # Slot can START any time from wh_start up to (wh_end - service_duration).
        latest_start = wh_end - service_duration_min
        if latest_start < wh_start:
            # Service is longer than the working window — no slots possible.
            continue

        t = wh_start
        while t <= latest_start:
            slot_end = t + service_duration_min
            if not _conflicts(t, slot_end, busy, slot_buffer_min):
                slots.append(t)
            t += slot_step_min

    return sorted(set(slots))


def _conflicts(slot_start: int, slot_end: int, busy, buffer: int) -> bool:
    """True if [slot_start, slot_end) collides with any busy interval,
    honoring the buffer (extra minutes applied to BOTH sides of the busy block)."""
    for b_start, b_end in busy:
        if slot_start < b_end + buffer and b_start - buffer < slot_end:
            return True
    return False
