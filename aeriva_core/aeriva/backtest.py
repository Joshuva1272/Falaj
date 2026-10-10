"""Rolling-origin back-test and metrics (brief Section 4G)."""
import numpy as np
import pandas as pd
from .models import L0, L1, L2, LG


def wape(actual, forecast):
    return float(np.abs(forecast - actual).sum() / actual.sum())


def total_error(df, col):
    """Mean absolute % error of the all-market total, per target month."""
    t = df.groupby("month")[["gn", col]].sum()
    return float((t[col] / t["gn"] - 1).abs().mean())


def rolling_backtest(panel, origins, horizons=(1, 3, 6), models=(L0, L1, LG, L2)):
    """Train on months < origin, forecast month origin + h - 1. Returns one row per market x target.

    NOTE: conditional back-test. Every horizon uses the target month's actual seats (a known schedule);
    only the training window changes with h. It is not an unconditional multi-step forecast test.
    """
    out = []
    usable = panel.dropna(subset=["gn_l12", "dln_seats"])
    for o in origins:
        train = usable[usable["month"] < o]
        fitted = {M.name: M().fit(train) for M in models}
        for h in horizons:
            target = o + (h - 1)
            test = usable[usable["month"] == target].copy()
            if test.empty:
                continue
            for name, m in fitted.items():
                test[name] = m.predict(test).values
            test["origin"], test["h"] = o, h
            test["l1_beta"] = fitted["L1"].beta if "L1" in fitted else np.nan
            test["l2_beta"] = fitted["L2"].beta if "L2" in fitted else np.nan
            out.append(test)
    return pd.concat(out, ignore_index=True)


def summary(bt, models=("L0", "L1", "LG", "L2")):
    rows = []
    for h, d in bt.groupby("h"):
        base_m, base_t = wape(d["gn"], d["L0"]), total_error(d, "L0")
        for m in models:
            wm, wt = wape(d["gn"], d[m]), total_error(d, m)
            rows.append({"h": h, "model": m, "market_wape": wm, "total_error": wt,
                         "skill_market": 1 - wm / base_m, "skill_total": 1 - wt / base_t})
    return pd.DataFrame(rows)


def interval_coverage(bt, model="L2", level=0.8, h=1, min_history=6):
    """Empirical interval from past out-of-sample log errors; share of actuals inside it."""
    d = bt[bt["h"] == h].copy()
    d["log_err"] = np.log(d["gn"] / d[model])
    lo_q, hi_q = (1 - level) / 2, 1 - (1 - level) / 2
    hits = []
    origins = sorted(d["origin"].unique())
    for o in origins[min_history:]:
        past = d.loc[d["origin"] < o, "log_err"]
        q_lo, q_hi = past.quantile(lo_q), past.quantile(hi_q)
        cur = d[d["origin"] == o]
        hits.append(((cur["log_err"] >= q_lo) & (cur["log_err"] <= q_hi)).mean())
    return float(np.mean(hits))


def prediction_interval(forecast, past_log_errors, level=0.8):
    lo_q, hi_q = (1 - level) / 2, 1 - (1 - level) / 2
    return (forecast * np.exp(np.quantile(past_log_errors, lo_q)),
            forecast * np.exp(np.quantile(past_log_errors, hi_q)))


def market_table(bt, model="L2", h=1):
    d = bt[bt["h"] == h]
    return (d.groupby("market").apply(lambda x: wape(x["gn"], x[model]))
             .rename("wape").sort_values())


def confidence_grade(wape_value, beta_ci_low=None):
    """F11. A: WAPE < 15% and beta clearly positive; B: 15-25%; C otherwise."""
    if wape_value < 0.15 and (beta_ci_low is None or beta_ci_low > 0):
        return "A"
    if wape_value <= 0.25:
        return "B"
    return "C"


def bias_by_year(bt, model="L2", h=1):
    """Mean signed error of the Abu Dhabi total per calendar year (+ = over-forecast)."""
    d = bt[bt["h"] == h]
    t = d.groupby("month")[["gn", model]].sum()
    e = t[model] / t["gn"] - 1
    return e.groupby(pd.PeriodIndex(t.index, freq="M").year).mean()
