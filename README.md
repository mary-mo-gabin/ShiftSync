# ShiftSync ⛳📅

> Convert cluttered, multi-page staff roster PDFs into clean `.ics` calendar events in seconds.

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://share.streamlit.io/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![Tests](https://img.shields.io/badge/tests-pytest-green.svg)](https://docs.pytest.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**Live Demo**: [https://shiftsync10.streamlit.app/](https://shiftsync10.streamlit.app/)

ShiftSync eliminates the manual friction of reading weekly PDF shift rosters and manually typing dates into your calendar. Upload one or multiple schedule PDFs, filter by your name, preview your hours, and export a ready-to-import `.ics` file compatible with Google Calendar, Apple Calendar, and Outlook.

---

## ✨ Features

- **Multi-PDF Drag & Drop**: Batch-process multiple weekly rosters at once.
- **Robust Line-Wrap Parsing**: Accurately detects split text across narrow table cells (e.g., `Mary 9-\n3:30`).
- **Flexible Shift Logic**: Handles standard shifts (`9-5`, `9-3:30`) and evening close shifts (`3:30-Close`) with customizable closing times.
- **Smart Deduplication**: Merges overlapping shifts across updated rosters automatically.
- **Instant Metrics**: Real-time breakdown of total shifts and weekly hours worked.
- **One-Click Calendar Sync**: Generates standards-compliant `.ics` files with location and timezone awareness.

---

## 📁 Project Structure

```text
shiftsync/
├── app.py              # Streamlit Web UI (drag-and-drop, metrics, export)
├── parser.py           # Core parsing engine (PDF extraction, regex, .ics generation)
├── test_parser.py      # Pytest test suite covering edge cases
├── requirements.txt    # Dependency specifications
├── .gitignore          # Safeguards sensitive schedule PDFs & cached binaries
└── README.md
```

---

## ☁️ Deployment
Deployed on **Streamlit Community Cloud**: [https://shiftsync10.streamlit.app/](https://shiftsync10.streamlit.app/)

---

## 📄 License
Distributed under the MIT License. See LICENSE for details.
