# FilCalendar - Personal Schedule Generator

Python tool to generate a personalized ICS calendar from the [FIL](https://www.fil.univ-lille.fr/) (University of Lille) class schedule.

## Features

- **Smart filtering**: Keeps only your group's classes (TD/TP) + all lectures (CM)
- **Enhanced location**: Automatic building addresses (M1-M5, P1-P5, etc.) for GPS navigation
- **Stable ICS**: Content-based UID to prevent duplicates in Google Calendar
- **Chronological sorting**: Events always ordered by date for clean Git commits
- **All-day events**: Breaks are automatically converted to all-day events

## Installation

```bash
cd FilCalendar
pip install -r requirements.txt
```

## Configuration

Edit the `MES_CHOIX` dictionary in `calendarGeneratorCedric.py` with your group numbers:

```python
MES_CHOIX = {
    'TEC': 6,      # Your TD/TP group number
    'Projet': 4,
    'RSX2': 2,
    'GL': 5,
    # ... other subjects
    'ARCHI': 0,    # 0 = not enrolled
}
```

## Usage

```bash
python FilCalendar/calendarGeneratorCedric.py
```

The `data_export.ics` file will be generated at the project root.

## Automatic Updates (GitHub Actions)

The GitHub Actions workflow updates the schedule **every hour** and automatically commits changes.

To sync with Google Calendar:
1. Import the raw ICS file URL from GitHub
2. Or manually download the `data_export.ics` file

## Project Structure

```
.
├── FilCalendar/
│   ├── calendarGeneratorCedric.py   # Main script
│   └── requirements.txt             # Python dependencies
├── .github/workflows/
│   └── updateCalendar.yml           # GitHub Actions automation
├── data_export.ics                  # Generated calendar
└── README.md
```

## Dependencies

- `requests` - JSON data fetching
- `ics` - ICS file generation
- `arrow` - Date and timezone handling

## License

Personal project - University of Lille, FIL L3
