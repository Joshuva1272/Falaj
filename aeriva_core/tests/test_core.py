import numpy as np
import pandas as pd
from aeriva import scenario, features
from aeriva.models import L0, L1


def test_scenario_zero_change():
    r = scenario.seats_change(1000, 5000, pct=0.0)
    assert r.delta_central == 0


def test_scenario_formula():
    r = scenario.seats_change(1000, 5000, pct=0.10)
    assert abs(r.delta_central - 1000 * (1.1 ** 0.52 - 1)) < 1e-9
    assert r.delta_low < r.delta_central < r.delta_high


def test_route_cut_recapture():
    full = scenario.route_cut(1000, 5000, route_seats=1000, recapture=0.0)
    half = scenario.route_cut(1000, 5000, route_seats=1000, recapture=0.5)
    assert full.delta_central < half.delta_central < 0


def test_calendar_shares():
    cal = features.calendar_month_table("2025-03", "2025-03")
    assert abs(cal["ramadan_share"].iloc[0] - 29 / 31) < 1e-9
    assert cal["eid_count"].iloc[0] == 1          # Eid al-Fitr 30 Mar 2025


def test_l0_l1():
    df = pd.DataFrame({"gn": [110.0], "gn_l12": [100.0], "dln_seats": [np.log(1.21)]})
    assert L0().predict(df).iloc[0] == 100
    assert abs(L1(beta=0.5).predict(df).iloc[0] - 110) < 1e-9


def test_trailing_features_exclude_current_month():
    # AHR/ALOS windows must use m-1 ... m-12 only (no leakage)
    months = pd.period_range("2022-01", "2023-06", freq="M")
    p = pd.DataFrame({"market": "X", "month": months, "gn": 1.0, "na": 1.0, "p2p": 1.0})
    p.loc[p.month == pd.Period("2023-06", "M"), "na"] = 1000.0   # spike in the target month
    t = p.groupby("market")["na"].transform(lambda s: s.shift(1).rolling(12, min_periods=12).sum())
    assert t.iloc[-1] == 12.0


def test_stock_flow_recovers_kernel():
    from aeriva.nowcast import StockFlow
    idx = pd.date_range("2023-01-01", periods=400, freq="D")
    rng = np.random.default_rng(0)
    arr = pd.DataFrame({"X": rng.integers(50, 150, len(idx)).astype(float)}, index=idx)
    guests = arr["X"] + 0.8 * arr["X"].shift(1) + 0.5 * arr["X"].shift(2)
    m = StockFlow().fit(pd.DataFrame({"X": guests}), arr)
    w = m.w["X"]
    assert abs(w[0] - 1) < 1e-6 and abs(w[1] - 0.8) < 1e-6 and abs(w[2] - 0.5) < 1e-6


def test_occupancy_view():
    # Appendix B.5: Kuwait +7,087 guest-nights over 1,281,505 all guest-nights
    assert abs(scenario.occupancy_change_pct(7087, 1_281_505) - 0.00553) < 1e-5
    assert abs(scenario.occupancy_change_points(7087, 1_281_505, 0.70) - 0.00387) < 1e-5
