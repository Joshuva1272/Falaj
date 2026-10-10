"""Configuration: file names, calendar tables, cleaning rules."""
import pandas as pd

# Default file names as supplied by the challenge
FLIGHT_FILE = "flight_data.xlsx"
INT_FILE = "data_international_train.xlsx"
DOM_FILE = "data_domestic_train.xlsx"

# Operators removed during cleaning (< 0.02% of passengers)
EXCLUDED_AIRLINES = {"Private", "European Cargo Limited", "Unknown"}
# Rows with load factor above this are treated as data errors and dropped
MAX_LOAD_FACTOR = 1.2

# UAE calendar used in the analysis. Confirm 2026 against official announcements.
RAMADAN = {  # first day, last day
    2022: ("2022-04-02", "2022-05-01"),
    2023: ("2023-03-23", "2023-04-20"),
    2024: ("2024-03-11", "2024-04-09"),
    2025: ("2025-03-01", "2025-03-29"),
    2026: ("2026-02-18", "2026-03-19"),
}
EID_FIRST_DAYS = [  # Eid al-Fitr and Eid al-Adha, first day
    "2022-05-02", "2022-07-09",
    "2023-04-21", "2023-06-28",
    "2024-04-10", "2024-06-16",
    "2025-03-30", "2025-06-06",
    "2026-03-20", "2026-05-27",
]
EID_WINDOW_DAYS = 4          # daily Eid window (assumption)
NATIONAL_DAY = ("12-02", "12-03")

# Gateway tier cut-offs on the 12-month Air-to-Hotel Ratio (F10)
GATEWAY_CUTS = (0.3, 1.2)


def ramadan_days() -> pd.DatetimeIndex:
    return pd.DatetimeIndex(
        pd.concat([pd.Series(pd.date_range(a, b)) for a, b in RAMADAN.values()])
    )


def eid_days() -> pd.DatetimeIndex:
    return pd.DatetimeIndex(pd.to_datetime(EID_FIRST_DAYS))
