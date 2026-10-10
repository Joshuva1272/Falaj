"""Load and clean the three challenge files (brief Section 4D, steps 1-3 and 6)."""
from pathlib import Path
import pandas as pd
from . import config


def _read(path):
    df = pd.read_excel(path, sheet_name="Export", na_values=["*"])
    df["Date"] = pd.to_datetime(df["Date"])
    return df


def load_flights(data_dir, clean=True) -> pd.DataFrame:
    """FLT: 2022 rows are monthly totals, 2023+ rows are daily."""
    f = _read(Path(data_dir) / config.FLIGHT_FILE)
    f = f.drop(columns=["Arrival City", "Destination"], errors="ignore")
    f["market"] = f["Departure Country Name"].str.strip().str.upper()
    f["grain"] = (f["Date"].dt.year == 2022).map({True: "monthly", False: "daily"})
    f["month"] = f["Date"].dt.to_period("M")
    if clean:
        n0 = len(f)
        f = f[~f["Airline Name"].isin(config.EXCLUDED_AIRLINES)]
        f = f[f["Load Factor"] <= config.MAX_LOAD_FACTOR]
        f.attrs["rows_removed"] = n0 - len(f)
    return f.reset_index(drop=True)


def load_international(data_dir) -> pd.DataFrame:
    """INT: nationality x day. Missing nationality-days are suppressed (< 10 guests), not zero."""
    i = _read(Path(data_dir) / config.INT_FILE)
    i["market"] = i["Nationality"].str.strip().str.upper()
    i["month"] = i["Date"].dt.to_period("M")
    return i


def load_domestic(data_dir) -> pd.DataFrame:
    d = _read(Path(data_dir) / config.DOM_FILE)
    d["month"] = d["Date"].dt.to_period("M")
    return d


def integrity_report(flights, intl, dom) -> dict:
    """Checks quoted in the brief (Phase 1)."""
    f = flights
    return {
        "flight_rows": len(f),
        "flight_rows_removed_by_cleaning": f.attrs.get("rows_removed", 0),
        "pax_identity_violations": int((f["Total PAX"] != f["Total P2P"] + f["Total Transfer"] + f["Total Transit"]).sum()),
        "share_load_factor_above_1": round(float((f["Load Factor"] > 1).mean()), 4),
        "transfer_share_of_pax": round(float(f["Total Transfer"].sum() / f["Total PAX"].sum()), 4),
        "int_rows": len(intl),
        "int_new_arrivals_gt_guests": int((intl["New Arrivals"] > intl["Guests"]).sum()),
        "int_duplicates": int(intl.duplicated(["Date", "market"]).sum()),
        "dom_rows": len(dom),
        "dom_duplicates": int(dom.duplicated(["Date"]).sum()),
        "flight_markets": int(f["market"].nunique()),
        "hotel_nationalities": int(intl["market"].nunique()),
        "markets_without_flights": sorted(set(intl["market"]) - set(f["market"])),
    }
