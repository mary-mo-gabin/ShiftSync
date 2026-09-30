import io
import re
from datetime import date, datetime, time, timedelta
from pathlib import Path
from typing import BinaryIO, Union

import pdfplumber
import pytz
from icalendar import Calendar, Event

LOCATIONS = ["Airdrie", "Brentwood", "Signal Hill"]

def parse_header_date(cell_text: str, year: int):
    """'Mon (09-28)' 또는 'Sat (10-03)' 형태에서 날짜 추출"""
    if not cell_text:
        return None
    m = re.search(r"(\d{1,2})\s*[-/]\s*(\d{1,2})", str(cell_text))
    if m:
        month, day = int(m.group(1)), int(m.group(2))
        try:
            return date(year, month, day)
        except ValueError:
            return None
    return None

def convert_to_time(t_str: str, close_time: time, is_end: bool = False) -> time:
    """'9', '3:30', '5', 'Close' 등을 24시간제 time 객체로 변환"""
    t_str = t_str.strip().lower()
    if t_str == "close":
        return close_time

    if ":" in t_str:
        h, m = map(int, t_str.split(":"))
    else:
        h, m = int(t_str), 0

    if 1 <= h <= 8:
        h += 12
    elif is_end and h < 9:
        h += 12

    return time(h, m)

def find_shifts_in_cell(cell_text: str, name: str, shift_date: date, tz, close_time: time):
    """셀 단위 텍스트에서 줄바꿈(\s*)을 포함한 이름 및 근무 시간 매칭"""
    if not cell_text:
        return []

    pattern = (
        rf"(?i)\b{re.escape(name)}\b\s*"
        r"(\d{1,2}(?::\d{2})?)\s*[-–—]\s*"
        r"(\d{1,2}(?::\d{2})?|[Cc]lose)"
    )

    results = []
    for match in re.finditer(pattern, str(cell_text)):
        start_str, end_str = match.group(1), match.group(2)
        start_t = convert_to_time(start_str, close_time, is_end=False)
        end_t = convert_to_time(end_str, close_time, is_end=True)

        dt_start = tz.localize(datetime.combine(shift_date, start_t))
        dt_end = tz.localize(datetime.combine(shift_date, end_t))

        if dt_end <= dt_start:
            dt_end += timedelta(days=1)

        results.append((dt_start, dt_end))

    return results

def process_pdf_file(pdf_source: Union[bytes, BinaryIO, Path, str], name: str, year: int, tz_str: str, close_time: time):
    """업로드된 단일 PDF 바이트 스트림을 파싱하여 쉬프트 리스트 반환"""
    tz = pytz.timezone(tz_str)
    shifts = []
    
    file_obj = io.BytesIO(pdf_source) if isinstance(pdf_source, bytes) else pdf_source

    with pdfplumber.open(file_obj) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text() or ""
            
            # 지점 식별
            location = "Golf Park"
            for loc in LOCATIONS:
                if loc.lower() in page_text.lower():
                    location = f"Golf Park {loc}"
                    break

            tables = page.extract_tables()
            if not tables:
                continue

            for table in tables:
                date_col_map = {}
                header_row_idx = None

                for r_idx, row in enumerate(table):
                    temp_map = {}
                    for c_idx, cell in enumerate(row):
                        d = parse_header_date(cell, year)
                        if d:
                            temp_map[c_idx] = d
                    if len(temp_map) >= 3:
                        date_col_map = temp_map
                        header_row_idx = r_idx
                        break

                if not date_col_map or header_row_idx is None:
                    continue

                for row in table[header_row_idx + 1:]:
                    for c_idx, cell in enumerate(row):
                        if c_idx not in date_col_map or not cell:
                            continue

                        cell_shifts = find_shifts_in_cell(cell, name, date_col_map[c_idx], tz, close_time)
                        for start_dt, end_dt in cell_shifts:
                            shifts.append({
                                "start": start_dt,
                                "end": end_dt,
                                "location": location,
                                "summary": f"{location}"
                            })
    return shifts

def build_ics_content(shifts: list, tz_str: str) -> bytes:
    """추출된 쉬프트 목록으로 .ics 바이너리 생성"""
    cal = Calendar()
    cal.add("prodid", "-//Screen Golf Multi Scheduler//EN")
    cal.add("version", "2.0")
    cal.add("x-wr-calname", "Work Schedule")
    cal.add("x-wr-timezone", tz_str)

    for s in shifts:
        ev = Event()
        ev.add("summary", s["summary"])
        ev.add("dtstart", s["start"])
        ev.add("dtend", s["end"])
        ev.add("location", s["location"])
        ev.add("description", f"Shift - {s['location']}")
        cal.add_component(ev)

    return cal.to_ical()