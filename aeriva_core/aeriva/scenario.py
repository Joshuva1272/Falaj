"""Scenario engine (brief Section 4H).

User changes X -> system recalculates Seats' -> hotel-demand impact
    dGN = GN_base * ((Seats' / Seats_base) ** beta - 1)
Results are conditional associations, not causal effects.
"""
from dataclasses import dataclass

BETA_LOW, BETA_CENTRAL, BETA_HIGH = 0.47, 0.52, 0.57   # pooled seat elasticity and 95% range
BETA_P2P = 0.43                                          # passenger elasticity (stopover scenario)


@dataclass
class Result:
    seats_base: float
    seats_new: float
    gn_base: float
    delta_low: float
    delta_central: float
    delta_high: float

    @property
    def gn_new(self):
        return self.gn_base + self.delta_central


def _delta(gn, ratio, beta):
    return gn * (ratio ** beta - 1)


def seats_change(gn_base, seats_base, pct=None, seats_new=None,
                 beta=(BETA_LOW, BETA_CENTRAL, BETA_HIGH)) -> Result:
    """Change seats by pct (e.g. 0.20 for +20%) or to an absolute seats_new."""
    if seats_new is None:
        seats_new = seats_base * (1 + pct)
    r = seats_new / seats_base
    lo, c, hi = beta
    return Result(seats_base, seats_new, gn_base, _delta(gn_base, r, lo), _delta(gn_base, r, c), _delta(gn_base, r, hi))


def frequency_change(gn_base, seats_base, flights_per_day_new, seats_per_flight, days, **kw) -> Result:
    return seats_change(gn_base, seats_base, seats_new=flights_per_day_new * seats_per_flight * days, **kw)


def route_cut(gn_base, seats_base, route_seats, recapture=0.0, **kw) -> Result:
    """recapture = share of the lost seats replaced by other airlines (default 0, assumption A18)."""
    return seats_change(gn_base, seats_base, seats_new=seats_base - route_seats * (1 - recapture), **kw)


def stopover(gn_base, p2p_base, transfer_base, k, beta=BETA_P2P) -> float:
    """Share k of transfer passengers become P2P (assumption A19). Returns central dGN."""
    return _delta(gn_base, (p2p_base + k * transfer_base) / p2p_base, beta)


def yield_per_1000_seats(gn, seats, beta=BETA_CENTRAL):
    """Guest-nights per 1,000 added seats, for small changes."""
    return 1000 * beta * gn / seats


# ---------- occupancy view (brief Appendix B) ----------
def occupancy_change_pct(delta_gn, gn_all):
    """Level 1: relative change in Abu Dhabi occupancy. gn_all = all guest-nights (international + domestic) in the month."""
    return delta_gn / gn_all


def occupancy_change_points(delta_gn, gn_all, occ_published):
    """Level 2: change in occupancy points, calibrated to DCT's published occupancy for the month (e.g. 0.70).

    Assumes occupied rooms move in proportion to guest-nights (A13) and uncovered guest-nights are unchanged (A14).
    """
    return occ_published * delta_gn / gn_all


# ---------- months without flight data (after Feb 2026) ----------
def future_row(panel, market, month, seats=None):
    """Build the model input for a month the flight file does not cover.

    Seats default to the same month last year (assumption: schedule unchanged, labelled A);
    the user can overwrite them. Needs GN for month-12 in the panel.
    """
    import numpy as np
    import pandas as pd
    from .features import calendar_month_table
    m = pd.Period(month, "M")
    ly = panel[(panel["market"] == market) & (panel["month"] == m - 12)]
    if ly.empty:
        raise ValueError(f"No guest-nights for {market} {m - 12}: month is outside the forecastable window")
    ly = ly.iloc[0]
    cal = calendar_month_table().set_index("month")
    s = float(ly["seats"]) if seats is None else float(seats)
    return pd.DataFrame([{
        "market": market, "month": m, "gn_l12": ly["gn"], "seats_l12": ly["seats"], "seats": s,
        "seats_assumed": seats is None,
        "dln_seats": np.log(s / ly["seats"]),
        "d_ramadan": cal.loc[m, "ramadan_share"] - cal.loc[m - 12, "ramadan_share"],
        "d_eid": cal.loc[m, "eid_count"] - cal.loc[m - 12, "eid_count"],
    }])
