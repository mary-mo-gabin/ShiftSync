from datetime import date, datetime, time
import pytz
import pytest
from icalendar import Calendar

from parser import (
    parse_header_date,
    convert_to_time,
    find_shifts_in_cell,
    build_ics_content,
)

# -----------------------------------------------------------------------------
# Fixtures
# -----------------------------------------------------------------------------
@pytest.fixture
def tz():
    return pytz.timezone("America/Edmonton")


@pytest.fixture
def default_close():
    return time(23, 0)


# -----------------------------------------------------------------------------
# 1. Date Header Parsing Tests
# -----------------------------------------------------------------------------
@pytest.mark.parametrize(
    "cell_text, year, expected",
    [
        ("Mon (09-28)", 2026, date(2026, 9, 28)),
        ("Sat (10-03)", 2026, date(2026, 10, 3)),
        ("Thur (\n10-01)", 2026, date(2026, 10, 1)),  # Handles newline in headers
        ("10/02", 2026, date(2026, 10, 2)),
        ("Airdrie", 2026, None),                       # Non-date text
        ("", 2026, None),                              # Empty string
        (None, 2026, None),                            # None input
    ],
)
def test_parse_header_date(cell_text, year, expected):
    assert parse_header_date(cell_text, year) == expected


# -----------------------------------------------------------------------------
# 2. Time Conversion Tests (12-hour AM/PM & Close)
# -----------------------------------------------------------------------------
@pytest.mark.parametrize(
    "time_str, is_end, expected",
    [
        ("9", False, time(9, 0)),           # 9 AM start
        ("10:30", False, time(10, 30)),     # 10:30 AM start
        ("3:30", True, time(15, 30)),       # 3:30 PM end
        ("5", True, time(17, 0)),           # 5 PM end
        ("12", False, time(12, 0)),         # 12 PM noon
        ("close", True, time(23, 0)),       # Close keyword
        ("CLOSE", True, time(23, 0)),       # Case-insensitive close
    ],
)
def test_convert_to_time(time_str, is_end, expected, default_close):
    assert convert_to_time(time_str, default_close, is_end=is_end) == expected


# -----------------------------------------------------------------------------
# 3. Cell Shift Extraction Tests (Regex & Multiline)
# -----------------------------------------------------------------------------
def test_find_shifts_single_line(tz, default_close):
    cell = "Mary 9-5"
    shift_date = date(2026, 10, 4)
    shifts = find_shifts_in_cell(cell, "Mary", shift_date, tz, default_close)

    assert len(shifts) == 1
    start, end = shifts[0]
    assert start == tz.localize(datetime(2026, 10, 4, 9, 0))
    assert end == tz.localize(datetime(2026, 10, 4, 17, 0))


def test_find_shifts_multiline_split(tz, default_close):
    """Verifies that line breaks within a shift (e.g., 'Mary 9-\n3:30') are detected."""
    cell = "Mary 9-\n3:30\nMia 3:30-\nClose"
    shift_date = date(2026, 10, 3)
    shifts = find_shifts_in_cell(cell, "Mary", shift_date, tz, default_close)

    assert len(shifts) == 1
    start, end = shifts[0]
    assert start == tz.localize(datetime(2026, 10, 3, 9, 0))
    assert end == tz.localize(datetime(2026, 10, 3, 15, 30))


def test_find_shifts_with_close_keyword(tz, default_close):
    cell = "Mary 3:30-Close"
    shift_date = date(2026, 10, 5)
    shifts = find_shifts_in_cell(cell, "Mary", shift_date, tz, default_close)

    assert len(shifts) == 1
    start, end = shifts[0]
    assert start == tz.localize(datetime(2026, 10, 5, 15, 30))
    assert end == tz.localize(datetime(2026, 10, 5, 23, 0))


def test_find_shifts_overnight_shift(tz, default_close):
    """If end time is earlier than or equal to start time, it rolls to next day."""
    custom_close = time(1, 0)  # 1 AM next day
    cell = "Mary 5-Close"
    shift_date = date(2026, 10, 5)
    shifts = find_shifts_in_cell(cell, "Mary", shift_date, tz, custom_close)

    assert len(shifts) == 1
    start, end = shifts[0]
    assert start == tz.localize(datetime(2026, 10, 5, 17, 0))
    assert end == tz.localize(datetime(2026, 10, 6, 1, 0))  # Rolled to Oct 6


def test_find_shifts_ignore_other_employees(tz, default_close):
    cell = "John 9-3:30\nPaula 3:30-Close"
    shift_date = date(2026, 10, 3)
    shifts = find_shifts_in_cell(cell, "Mary", shift_date, tz, default_close)

    assert shifts == []


def test_find_shifts_empty_cell(tz, default_close):
    assert find_shifts_in_cell("", "Mary", date(2026, 10, 3), tz, default_close) == []
    assert find_shifts_in_cell(None, "Mary", date(2026, 10, 3), tz, default_close) == []


# -----------------------------------------------------------------------------
# 4. Calendar ICS Generation Tests
# -----------------------------------------------------------------------------
def test_build_ics(tz):
    shifts = [
        {
            "start": tz.localize(datetime(2026, 10, 3, 9, 0)),
            "end": tz.localize(datetime(2026, 10, 3, 15, 30)),
            "location": "Golf Park Signal Hill",
            "summary": "근무 (Signal Hill)",
        }
    ]

    ics_bytes = build_ics_content(shifts, "America/Edmonton")
    cal = Calendar.from_ical(ics_bytes)

    assert cal.get("x-wr-calname") == "Work Schedule"
    
    events = [c for c in cal.subcomponents if c.name == "VEVENT"]
    assert len(events) == 1
    assert str(events[0]["SUMMARY"]) == "근무 (Signal Hill)"
    assert str(events[0]["LOCATION"]) == "Golf Park Signal Hill"