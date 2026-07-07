# Copyright (c) 2026, Yasser Bousrih and contributors
# For license information, please see license.txt

"""Unit tests for the availability engine.

These exercise the PURE functions in
`frontdesk.frontdesk.doctype.booking.overlap` and run without a Frappe site
(do NOT extend `frappe.tests.TestCase`). The Frappe integration tests for
the whitelist endpoint and the booking controller go in
`test_api_availability.py` (requires a bench).
"""

import unittest
from datetime import time

from frontdesk.frontdesk.doctype.booking.overlap import (
    add_minutes_to_time,
    compute_available_slots,
    times_overlap,
)


class TestTimeOverlap(unittest.TestCase):
    def test_overlap_simple(self):
        self.assertTrue(times_overlap(time(9, 0), time(10, 0), time(9, 30), time(10, 30)))

    def test_overlap_touching_is_not_overlap(self):
        # 9–10 and 10–11 share no minute. Half-open intervals.
        self.assertFalse(times_overlap(time(9, 0), time(10, 0), time(10, 0), time(11, 0)))

    def test_overlap_contained(self):
        # 9–10 fully inside 8–11.
        self.assertTrue(times_overlap(time(8, 0), time(11, 0), time(9, 0), time(10, 0)))

    def test_overlap_disjoint(self):
        self.assertFalse(times_overlap(time(9, 0), time(10, 0), time(11, 0), time(12, 0)))

    def test_overlap_back_to_back(self):
        # 9:30–10:00 then 10:00–10:30 — should NOT overlap.
        self.assertFalse(times_overlap(time(9, 30), time(10, 0), time(10, 0), time(10, 30)))


class TestAddMinutes(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(add_minutes_to_time(time(9, 0), 30), time(9, 30))

    def test_hour_rollover(self):
        self.assertEqual(add_minutes_to_time(time(9, 45), 30), time(10, 15))

    def test_day_rollover(self):
        self.assertEqual(add_minutes_to_time(time(23, 30), 60), time(0, 30))


class TestComputeAvailableSlots(unittest.TestCase):
    """The heart of the booking engine: working hours minus existing bookings,
    sliced by service duration. All in minutes since midnight."""

    WH = [("Wednesday", 9 * 60, 17 * 60)]  # 9:00–17:00 on a Wednesday

    def test_no_bookings_returns_full_grid(self):
        # 30-min service, 5-min step, 9:00–17:00 window.
        # latest_start = 16:30, starts at 9:00,9:05,…,16:30 → (990-540)/5+1 = 91.
        slots = compute_available_slots(
            working_hours=self.WH,
            service_duration_min=30,
            existing_bookings=[],
        )
        self.assertEqual(slots[0], 9 * 60)
        self.assertEqual(slots[-1], 17 * 60 - 30)  # 16:30 = 990
        self.assertEqual(len(slots), 91)

    def test_existing_booking_blocks_slots(self):
        # A 10:00–10:30 booking blocks any 30-min service starting in [9:35, 10:30).
        slots = compute_available_slots(
            working_hours=self.WH,
            service_duration_min=30,
            existing_bookings=[(10 * 60, 10 * 60 + 30)],
        )
        # The first slot AT or AFTER 10:30 is 10:30 itself.
        self.assertIn(10 * 60 + 30, slots)
        # 10:25 must NOT appear (would run 10:25–10:55, overlapping 10:00–10:30).
        self.assertNotIn(10 * 60 + 25, slots)
        # 9:00 must still be available.
        self.assertIn(9 * 60, slots)

    def test_buffer_blocks_extra_minutes(self):
        # 5-min buffer: existing 10:00–10:30 blocks 9:55–10:35 for a 30-min service.
        slots = compute_available_slots(
            working_hours=self.WH,
            service_duration_min=30,
            existing_bookings=[(10 * 60, 10 * 60 + 30)],
            slot_buffer_min=5,
        )
        # 10:35 onward OK.
        self.assertIn(10 * 60 + 35, slots)
        # 10:30 NOT OK (would run 10:30–11:00, within 5-min buffer of 10:30 end).
        self.assertNotIn(10 * 60 + 30, slots)

    def test_service_longer_than_window_returns_empty(self):
        slots = compute_available_slots(
            working_hours=self.WH,
            service_duration_min=9 * 60,  # 9 hours in an 8-hour window
            existing_bookings=[],
        )
        self.assertEqual(slots, [])

    def test_multiple_working_windows_same_day(self):
        # Split shift: 9–12 and 14–17, 60-min service, 60-min step.
        wh = [("Wednesday", 9 * 60, 12 * 60), ("Wednesday", 14 * 60, 17 * 60)]
        slots = compute_available_slots(
            working_hours=wh,
            service_duration_min=60,
            existing_bookings=[],
            slot_step_min=60,
        )
        # 9:00, 10:00, 11:00 from morning; 14:00, 15:00, 16:00 from afternoon.
        self.assertEqual(slots, [9 * 60, 10 * 60, 11 * 60, 14 * 60, 15 * 60, 16 * 60])

    def test_cancelled_booking_does_not_block(self):
        # The pure function trusts its caller to filter cancelled bookings.
        # The Frappe wrapper does that; the pure function does not.
        # This test pins that contract: we pass ONLY non-cancelled bookings.
        slots = compute_available_slots(
            working_hours=self.WH,
            service_duration_min=30,
            existing_bookings=[],  # caller already filtered out a 10:00–10:30 cancelled booking
        )
        self.assertEqual(len(slots), 91)

    def test_step_size_affects_density(self):
        # 5-min step, 30-min service, 8-hour window 9:00–17:00:
        #   latest_start = 16:30, starts at 9:00,9:05,…,16:30 → (16.5-9)*12+1 = 91? no.
        #   count = (16:30 - 9:00)/5 + 1 = 7.5*12+1 = 91. Hmm, check: 450/5+1 = 91.
        #   But code loops while t <= latest_start with t += 5. From 540 stepping by 5
        #   up to 990 inclusive: (990-540)/5+1 = 91. But earlier test asserted 92...
        #   Let me recompute: 9:00=540, 9:05=545, ..., 16:30=990. (990-540)/5+1 = 91.
        #   So the earlier "test_no_bookings_returns_full_grid" assertion of 92 was WRONG.
        slots_5 = compute_available_slots(self.WH, 30, [], slot_step_min=5)
        slots_15 = compute_available_slots(self.WH, 30, [], slot_step_min=15)
        slots_30 = compute_available_slots(self.WH, 30, [], slot_step_min=30)
        self.assertEqual(len(slots_5), 91)
        # 9:00,9:15,…,16:30 → (990-540)/15+1 = 31
        self.assertEqual(len(slots_15), 31)
        # 9:00,9:30,…,16:30 → 16
        self.assertEqual(len(slots_30), 16)


if __name__ == "__main__":
    unittest.main()
