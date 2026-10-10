"""Market x month panel and engineered features (brief Appendix A).

Notation: c = market, m = month. Trailing features use months before m only.
"""
import numpy as np
import pandas as pd
from . import config


# ---------- calendar features (F16, F17) ----------
def calendar_month_table(start="2021-01", end="2027-12") -> pd.DataFrame:
    months = pd.period_range(start, end, freq="M")
    ram = config.ramadan_days().to_period("M").value_counts()
    eid = config.eid_days().to_period("M").value_counts()
    cal = pd.DataFrame({"month": months})
    cal["ramadan_share"] = cal["month"].map(ram).fillna(0) / cal["month"].dt.days_in_month
    cal["eid_count"] = cal["month"].map(eid).fillna(0).astype(int)
    return cal


# ---------- base aggregates ----------
def flight_month(flights: pd.DataFrame) -> pd.DataFrame:
    """Seats, PAX, P2P, Transfer by market x month (+ F4, F5, F6)."""
    g = flights.groupby(["market", "month"])
    fm = g.agg(seats=("Total Seats", "sum"), pax=("Total PAX", "sum"),
               p2p=("Total P2P", "sum"), transfer=("Total Transfer", "sum")).reset_index()
    # F4, F5: flights per day (daily rows only, 2023+)
    d = flights[flights["grain"] == "daily"].copy()
    d["flights"] = (d["Average Weekly Frequency"] * d["Date"].dt.days_in_month / 7).round()
    fl = d.groupby(["market", "month"])["flights"].sum().rename("flights").reset_index()
    fm = fm.merge(fl, on=["market", "month"], how="left")
    fm["flights_per_day"] = fm["flights"] / fm["month"].dt.days_in_month
    fm["seats_per_flight"] = fm["seats"] / fm["flights"]
    # F6: largest airline's seat share
    a = flights.groupby(["market", "month", "Airline Name"])["Total Seats"].sum()
    top = (a / a.groupby(level=[0, 1]).transform("sum")).groupby(level=[0, 1]).max()
    fm = fm.merge(top.rename("top_airline_share").reset_index(), on=["market", "month"], how="left")
    # F2, F3
    fm["load_factor"] = fm["pax"] / fm["seats"]
    fm["p2p_share"] = fm["p2p"] / fm["pax"]
    return fm


def hotel_month(intl: pd.DataFrame) -> pd.DataFrame:
    """GN = sum of daily Guests; NA = sum of daily New Arrivals."""
    return (intl.groupby(["market", "month"])
                .agg(gn=("Guests", "sum"), na=("New Arrivals", "sum"), days_reported=("Guests", "size"))
                .reset_index())


# ---------- panel ----------
def build_panel(flights, intl) -> pd.DataFrame:
    """Join hotel and flight months for the markets present in both (INT inner-join FLT)."""
    p = hotel_month(intl).merge(flight_month(flights), on=["market", "month"], how="inner")
    p = p.merge(calendar_month_table(), on="month", how="left")
    p = p.sort_values(["market", "month"]).reset_index(drop=True)
    g = p.groupby("market")
    # lag-12 values by calendar month (not by row position)
    lag = p[["market", "month", "gn", "na", "seats", "p2p", "ramadan_share", "eid_count"]].copy()
    lag["month"] = lag["month"] + 12
    p = p.merge(lag, on=["market", "month"], how="left", suffixes=("", "_l12"))
    # F1, F16, F17 (year-on-year changes)
    p["dln_seats"] = np.log(p["seats"] / p["seats_l12"])
    p["dln_p2p"] = np.log(p["p2p"] / p["p2p_l12"])
    p["dln_gn"] = np.log(p["gn"] / p["gn_l12"])
    p["d_ramadan"] = p["ramadan_share"] - p["ramadan_share_l12"]
    p["d_eid"] = p["eid_count"] - p["eid_count_l12"]
    # F8, F9: trailing 12 months, months m-1 ... m-12 only
    for col in ["gn", "na", "p2p"]:
        p[f"{col}_t12"] = g[col].transform(lambda s: s.shift(1).rolling(12, min_periods=12).sum())
    p["alos_12"] = p["gn_t12"] / p["na_t12"]
    p["ahr_12"] = p["na_t12"] / p["p2p_t12"]
    lo, hi = config.GATEWAY_CUTS
    p["gateway_tier"] = pd.cut(p["ahr_12"], [-np.inf, lo, hi, np.inf], labels=["Low", "Mid", "High"])
    p["month_of_year"] = p["month"].dt.month
    return p


def total_guest_nights(intl, dom, month) -> float:
    """GN_all(m): international (all nationalities in the file) + domestic guest-nights for one month (Appendix B)."""
    m = pd.Period(month, "M")
    return float(intl.loc[intl["month"] == m, "Guests"].sum() + dom.loc[dom["month"] == m, "Guests"].sum())
