"""Fill the Guests column of the challenge test files.

Usage:
    python predict_test.py --data-dir path/to/data --out predictions

Method: stock-flow nowcast (aeriva/nowcast.py). New Arrivals are supplied in the test files,
so Guests are rebuilt from arrivals with a stay kernel fitted on the training period.
"""
import argparse
import numpy as np
from pathlib import Path
import pandas as pd
from aeriva import data, features
from aeriva.models import L2
from aeriva.nowcast import StockFlow, validate, to_daily_wide

WINDOWS = [("2024-12-31", "2025-01-01", "2025-07-31"),
           ("2024-07-31", "2024-08-01", "2025-02-28")]   # same calendar span as the test period


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", required=True)
    ap.add_argument("--out", default="predictions")
    a = ap.parse_args()
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    dd = Path(a.data_dir)

    # ---------- international ----------
    tr = data.load_international(dd)
    te = pd.read_excel(dd / "data_international_test.xlsx", sheet_name="Export")
    te["Date"] = pd.to_datetime(te["Date"]); te["market"] = te["Nationality"].str.strip().str.upper()
    markets = sorted(tr["market"].unique())
    G = to_daily_wide(tr, "Guests", markets)
    A = to_daily_wide(pd.concat([tr[["Date", "market", "New Arrivals"]], te[["Date", "market", "New Arrivals"]]]),
                      "New Arrivals", markets)
    val_i = validate(G, A.loc[:G.index.max()], WINDOWS)
    m = StockFlow().fit(G, A.loc[:G.index.max()])
    P = m.predict(A)
    long = P.stack().rename("Guests_pred").reset_index().rename(columns={"level_0": "Date", "level_1": "market"})
    te = te.merge(long, left_on=["Date", "market"], right_on=["Date", "market"], how="left")
    te.insert(1, "Guests", te.pop("Guests_pred").round().astype(int))
    te.drop(columns="market").to_excel(out / "data_international_test_predicted.xlsx", sheet_name="Export", index=False)
    m.kernel_table().round(3).to_csv(out / "stay_kernel_international.csv")

    # ---------- domestic ----------
    dtr = data.load_domestic(dd).assign(market="DOMESTIC")
    dte = pd.read_excel(dd / "data_domestic_test.xlsx", sheet_name="Export")
    dte["Date"] = pd.to_datetime(dte["Date"])
    Gd = to_daily_wide(dtr, "Guests")
    Ad = to_daily_wide(pd.concat([dtr[["Date", "market", "New Arrivals"]], dte.assign(market="DOMESTIC")[["Date", "market", "New Arrivals"]]]), "New Arrivals")
    val_d = validate(Gd, Ad.loc[:Gd.index.max()], WINDOWS)
    md = StockFlow().fit(Gd, Ad.loc[:Gd.index.max()])
    pdm = md.predict(Ad)["DOMESTIC"]
    dte.insert(1, "Guests", dte["Date"].map(pdm).round().astype(int))
    dte.to_excel(out / "data_domestic_test_predicted.xlsx", sheet_name="Export", index=False)

    # ---------- reconciliation: seats model (L2) vs nowcast, monthly, flight-matched markets ----------
    f = data.load_flights(dd)
    panel = features.build_panel(f, tr)
    fm = features.flight_month(f).merge(features.calendar_month_table(), on="month")
    lag = panel[["market", "month", "gn", "seats", "ramadan_share", "eid_count"]].copy(); lag["month"] = lag["month"] + 12
    fut = fm.merge(lag, on=["market", "month"], suffixes=("", "_l12"))
    fut = fut[(fut["month"] >= pd.Period("2025-08", "M")) & (fut["month"] <= pd.Period("2026-02", "M"))].rename(columns={"gn": "gn_l12"})
    fut["dln_seats"] = np.log(fut["seats"] / fut["seats_l12"])
    fut["d_ramadan"] = fut["ramadan_share"] - fut["ramadan_share_l12"]; fut["d_eid"] = fut["eid_count"] - fut["eid_count_l12"]
    fut["L2"] = L2().fit(panel).predict(fut).values
    nm = te.assign(month=te["Date"].dt.to_period("M")).groupby(["market", "month"])["Guests"].sum().rename("nowcast").reset_index()
    rec = fut.merge(nm, on=["market", "month"])
    rt = rec.groupby("month")[["L2", "nowcast"]].sum(); rt["L2_vs_nowcast"] = rt["L2"] / rt["nowcast"] - 1
    rt.to_csv(out / "reconciliation_L2_vs_nowcast.csv")
    print("\nSeats model (L2) vs nowcast, monthly total of flight-matched markets:")
    print(rt.round(3).to_string())

    val = pd.concat([val_i.assign(file="international"), val_d.assign(file="domestic")])
    val.to_csv(out / "validation.csv", index=False)
    print(val.round(3).to_string(index=False))
    print(f"\nInternational rows predicted: {len(te):,} · Domestic rows: {len(dte)}")


if __name__ == "__main__":
    main()
