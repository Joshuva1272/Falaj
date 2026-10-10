"""Stock-flow nowcast of daily Guests from daily New Arrivals.

Guests on day d are the people who arrived on d or earlier and have not yet left:
    Guests(c,d) = sum_k w_k(c) * NewArrivals(c, d-k)
The stay kernel w(c) is fitted per market with non-negative least squares on lag buckets.
By default the per-day weights are constrained to be non-increasing with lag (people leave, they do not return),
which keeps the kernel a plausible stay pattern at no cost in accuracy.

Use this ONLY when New Arrivals for the target days are known (e.g. the challenge test files,
or a month already flown). For forecasts before arrivals are known, use the L2 seat model.
"""
import numpy as np
import pandas as pd
from scipy.optimize import nnls

BUCKETS = [(0, 0), (1, 1), (2, 2), (3, 3), (4, 6), (7, 13), (14, 29), (30, 59), (60, 119)]
WARMUP = max(b for _, b in BUCKETS) + 1   # days of arrivals history needed


def design(arrivals: pd.Series, buckets=BUCKETS) -> pd.DataFrame:
    """Sum of arrivals in each lag bucket (arrivals must be a complete daily series)."""
    cols = {f"lag_{a}_{b}": sum(arrivals.shift(k) for k in range(a, b + 1)) for a, b in buckets}
    return pd.DataFrame(cols, index=arrivals.index)


def to_daily_wide(df, value, markets=None):
    w = df.pivot_table(index="Date", columns="market", values=value)
    w = w.reindex(pd.date_range(w.index.min(), w.index.max(), freq="D"))
    return w if markets is None else w.reindex(columns=markets)


# w = L @ v with v >= 0 gives w_0 >= w_1 >= ... >= w_last >= 0
_L = np.array([[1.0 if j >= b else 0.0 for j in range(len(BUCKETS))] for b in range(len(BUCKETS))])


class StockFlow:
    def __init__(self, monotone=True):
        self.monotone = monotone

    def fit(self, guests: pd.DataFrame, arrivals: pd.DataFrame, end=None):
        """guests, arrivals: wide daily frames (date x market). Missing arrivals = suppressed (< 10) -> 0."""
        self.w = {}
        for c in guests.columns:
            X = design(arrivals[c].fillna(0))
            y = guests[c]
            ok = X.notna().all(axis=1) & y.notna() & (X.index >= X.index[0] + pd.Timedelta(days=WARMUP))
            if end is not None:
                ok &= X.index <= pd.Timestamp(end)
            if self.monotone:
                v, _ = nnls(X[ok].values @ _L, y[ok].values)
                self.w[c] = _L @ v
            else:
                self.w[c], _ = nnls(X[ok].values, y[ok].values)
        return self

    def predict(self, arrivals: pd.DataFrame) -> pd.DataFrame:
        out = {c: design(arrivals[c].fillna(0)).values @ w for c, w in self.w.items() if c in arrivals}
        return pd.DataFrame(out, index=arrivals.index)

    def kernel_table(self):
        return pd.DataFrame(self.w, index=[f"lag_{a}_{b}" for a, b in BUCKETS]).T


def arrivals_baseline(guests, arrivals, end, days=5):
    """Fair simple comparator: Guests = k * (arrivals over the last `days` days), k fitted per market."""
    out = {}
    for c in guests.columns:
        s = sum(arrivals[c].fillna(0).shift(k) for k in range(days))
        ok = s.notna() & guests[c].notna() & (s.index <= pd.Timestamp(end))
        k_ = (guests[c][ok] * s[ok]).sum() / (s[ok] ** 2).sum()
        out[c] = s * k_
    return pd.DataFrame(out)


def validate(guests, arrivals, windows):
    """windows: list of (train_end, test_start, test_end).
    Returns WAPE of the stock-flow nowcast vs two baselines: same weekday last year, and 5-day arrivals x constant."""
    rows = []
    for tr_end, t0, t1 in windows:
        m = StockFlow().fit(guests, arrivals, end=tr_end)
        pred = m.predict(arrivals)
        sl = slice(t0, t1)
        y, p = guests.loc[sl], pred.loc[sl]
        b = guests.shift(364).loc[sl]
        mask = y.notna()
        b = b.where(b.notna(), guests.loc[:tr_end].mean(), axis=1)
        a5 = arrivals_baseline(guests, arrivals, tr_end).loc[sl]
        w = lambda f: float((f[mask] - y[mask]).abs().sum().sum() / y[mask].sum().sum())
        rows.append({"test": f"{t0} to {t1}", "stock_flow_wape": w(p),
                     "baseline_last_year_wape": w(b), "baseline_arrivals5_wape": w(a5)})
    return pd.DataFrame(rows)
