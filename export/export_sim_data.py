"""Export aeriva_core results into the single JSON file the simulator page reads.

Usage (from the "Simulator + AerivaCore" folder):
    python export/export_sim_data.py --core aeriva_core --data data --out simulator/aeriva_sim_data.json

Needs: run_all.py and predict_test.py already run, so aeriva_core/results and
aeriva_core/predictions exist. Rebuilds every number the four screens show.
"""
import argparse, json, sys, warnings
from pathlib import Path
import numpy as np
import pandas as pd
warnings.filterwarnings("ignore")

ap = argparse.ArgumentParser()
ap.add_argument("--core", default="aeriva_core")
ap.add_argument("--data", default="data")
ap.add_argument("--out", default="simulator/aeriva_sim_data.json")
ap.add_argument("--first", default="2025-08", help="first target month")
ap.add_argument("--last", default="2026-08", help="last target month")
a = ap.parse_args()
core, dd = Path(a.core), Path(a.data)
sys.path.insert(0, str(core))
from aeriva import data, features
res, pred = core / "results", core / "predictions"

P = lambda s: pd.Period(s, "M")
months = pd.period_range(a.first, a.last, freq="M")

# ---------- data: train + nowcast-filled test months ----------
f = data.load_flights(dd)
tr = data.load_international(dd)
te = pd.read_excel(pred / "data_international_test_predicted.xlsx", sheet_name="Export")
te["Date"] = pd.to_datetime(te["Date"]); te["market"] = te["Nationality"].str.strip().str.upper(); te["month"] = te["Date"].dt.to_period("M")
intl = pd.concat([tr, te], ignore_index=True)
dtr = data.load_domestic(dd)
dte = pd.read_excel(pred / "data_domestic_test_predicted.xlsx", sheet_name="Export")
dte["Date"] = pd.to_datetime(dte["Date"]); dte["month"] = dte["Date"].dt.to_period("M")
dom = pd.concat([dtr, dte], ignore_index=True)
last_obs = tr["month"].max()                      # last month with observed guests
panel = features.build_panel(f, intl)             # gn after last_obs = nowcast
last_flt = f["month"].max()

cal = features.calendar_month_table().set_index("month")
dram = [round(float(cal.loc[m, "ramadan_share"] - cal.loc[m - 12, "ramadan_share"]), 4) for m in months]
deid = [int(cal.loc[m, "eid_count"] - cal.loc[m - 12, "eid_count"]) for m in months]
gnall = [int(round(features.total_guest_nights(intl, dom, str(m - 12)))) for m in months]

el = pd.read_csv(res / "market_elasticities.csv").set_index("market")
mk = {}
for m in sorted(panel["market"].unique()):
    pm = panel[panel["market"] == m].set_index("month")
    rows = []
    for t in months:
        if t <= last_flt:
            if t not in pm.index or pd.isna(pm.loc[t, "gn_l12"]):
                rows.append(None); continue
            r = pm.loc[t]
            rows.append([int(r.seats), int(r.seats_l12), int(r.gn_l12), int(r.gn) if t > last_obs else 0,
                         round(float(r.load_factor), 3), int(r.p2p), int(r.transfer),
                         round(float(r.seats_per_flight), 1) if pd.notna(r.seats_per_flight) else 0,
                         round(float(r.top_airline_share), 3)])
        else:
            ly = t - 12
            if ly not in pm.index:
                rows.append(None); continue
            r = pm.loc[ly]
            rows.append([int(r.seats), int(r.seats), int(r.gn), 0, round(float(r.load_factor), 3), int(r.p2p),
                         int(r.transfer), round(float(r.seats_per_flight), 1) if pd.notna(r.seats_per_flight) else 0,
                         round(float(r.top_airline_share), 3)])
    po = pm[pm.index <= last_obs].dropna(subset=["ahr_12"])   # descriptors from observed months only
    lastr = po.iloc[-1] if len(po) else None
    e = el.loc[m] if m in el.index else None
    mk[m] = {"b": round(float(e.beta_shrunk), 3) if e is not None else 0.52,
             "lo": round(float(e.ci_low), 3) if e is not None else None,
             "g": e.grade if e is not None else "C",
             "w": round(float(e.backtest_wape), 3) if e is not None else None,
             "t": str(lastr.gateway_tier) if lastr is not None else "Mid",
             "ahr": round(float(lastr.ahr_12), 3) if lastr is not None else None,
             "alos": round(float(lastr.alos_12), 2) if lastr is not None else None,
             "r": rows}

hist0 = P("2023-01")
hm = pd.period_range(hist0, last_flt if last_flt > last_obs else last_obs, freq="M")
hist = {m: [int(panel[(panel.market == m) & (panel.month == x)].gn.sum()) for x in hm] for m in mk}

# ---------- back-test (h = 1) ----------
bt = pd.read_csv(res / "backtest_detail.csv"); bt["month"] = bt["month"].astype(str); bt["origin"] = bt["origin"].astype(str)
b1 = bt[bt.h == 1].copy(); b1["lerr"] = np.log(b1["gn"] / b1["L2"])
q = [round(float(b1["lerr"].quantile(0.1)), 4), round(float(b1["lerr"].quantile(0.9)), 4)]
origins = sorted(b1["origin"].unique()); band = {}
for k, o in enumerate(origins):
    if k < 6: band[o] = (None, None); continue
    past = b1.loc[b1["origin"] < o, "lerr"]; band[o] = (past.quantile(0.1), past.quantile(0.9))
btm = {}
for m, d in b1.sort_values("month").groupby("market"):
    out = []
    for r in d.itertuples():
        lo, hi = band[r.origin]
        out.append([r.month, int(r.gn), int(round(r.L0)), int(round(r.L1)), int(round(r.LG)), int(round(r.L2)),
                    int(round(r.L2 * np.exp(lo))) if lo is not None else 0, int(round(r.L2 * np.exp(hi))) if hi is not None else 0])
    btm[m] = out
tot = b1.groupby("month")[["gn", "L0", "L1", "LG", "L2"]].sum().reset_index()
bttot = [[r.month, int(r.gn), int(round(r.L0)), int(round(r.L1)), int(round(r.LG)), int(round(r.L2))] for r in tot.itertuples()]
wapeM = {m: {k: round(float(np.abs(d[k] - d.gn).sum() / d.gn.sum()), 3) for k in ["L0", "L1", "LG", "L2"]} for m, d in b1.groupby("market")}
sm = pd.read_csv(res / "backtest_summary.csv")
skill = {f"{int(r.h)}|{r.model}": [round(r.market_wape * 100, 1), round(r.total_error * 100, 1), round(r.skill_market * 100, 1), round(r.skill_total * 100, 1)] for r in sm.itertuples()}

def rp(name):
    r = pd.read_csv(res / f"replay_{name}_2023.csv")
    return {"m": [s[5:7] for s in r.month.astype(str)], "a": r.gn.round().astype(int).tolist(), "l2": r.L2.round().astype(int).tolist(),
            "l0": r.L0.round().astype(int).tolist(), "seats": r.seats.round().astype(int).tolist(), "seats_l12": r.seats_l12.round().astype(int).tolist()}

def yld(m, a, b):
    d = panel[(panel.market == m) & (panel.month >= P(a)) & (panel.month <= P(b))]
    return int(round(1000 * 0.52 * d.gn.sum() / d.seats.sum()))
kw = panel[(panel.market == "KUWAIT") & (panel.month == P("2024-08"))].iloc[0]
chk = {"kw_gn": int(kw.gn), "kw_seats": int(kw.seats), "gnall_aug24": int(round(features.total_guest_nights(intl, dom, "2024-08"))),
       "yield": {m: [yld(m, "2024-08", "2024-08"), yld(m, "2024-01", "2024-12")] for m in ["UNITED KINGDOM", "KUWAIT", "INDIA"]}}

D = {"months": [str(m) for m in months], "dram": dram, "deid": deid, "gnall": gnall, "mk": mk, "hist": hist, "hist0": str(hist0),
     "bt": btm, "q": q, "bttot": bttot, "wapeM": wapeM, "skill": skill, "rp_kuwait": rp("kuwait"), "rp_china": rp("china"), "chk": chk}
Path(a.out).parent.mkdir(parents=True, exist_ok=True)
json.dump(D, open(a.out, "w"), separators=(",", ":"))
print("wrote", a.out, Path(a.out).stat().st_size, "bytes;", len(mk), "markets;", len(months), "months")
