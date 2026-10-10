"""Forecasting models (brief Section 4F).

All models forecast GN(c,m) from GN(c,m-12) plus changes. Fit on training rows only.
"""
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf


class L0:
    """Seasonal naive: same month last year."""
    name = "L0"

    def fit(self, train):
        return self

    def predict(self, df):
        return df["gn_l12"]


class L1:
    """Last year x (Seats / Seats last year) ** beta, beta chosen on training data only."""
    name = "L1"

    def __init__(self, beta=None, grid=np.round(np.arange(0, 1.01, 0.05), 2)):
        self.beta, self.grid = beta, grid

    def fit(self, train):
        if self.beta is None:
            t = train.dropna(subset=["gn_l12", "dln_seats"])
            errs = [(np.abs(t["gn_l12"] * np.exp(b * t["dln_seats"]) - t["gn"]).sum(), b) for b in self.grid]
            self.beta = min(errs)[1]
        return self

    def predict(self, df):
        return df["gn_l12"] * np.exp(self.beta * df["dln_seats"])


class L2:
    """Weighted log year-on-year regression (selected model).

    ln(GN_m / GN_m-12) = alpha + beta * dln_seats + gamma * d_ramadan + delta * d_eid
    weights = sqrt(GN_m-12)
    """
    name = "L2"
    formula = "dln_gn ~ dln_seats + d_ramadan + d_eid"

    def fit(self, train):
        t = train.dropna(subset=["dln_gn", "dln_seats", "d_ramadan", "d_eid"])
        # drop calendar terms with no variation in a short training window (e.g. no Eid shift yet)
        terms = ["dln_seats"] + [v for v in ("d_ramadan", "d_eid") if t[v].std() > 0]
        self.formula = "dln_gn ~ " + " + ".join(terms)
        self.res = smf.wls(self.formula, data=t, weights=np.sqrt(t["gn_l12"])).fit()
        return self

    @property
    def params(self):
        """Coefficients; calendar terms dropped from a short window are reported as 0."""
        return self.res.params

    @property
    def beta(self):
        return float(self.res.params["dln_seats"])

    def beta_ci(self, alpha=0.05):
        lo, hi = self.res.conf_int(alpha).loc["dln_seats"]
        return float(lo), float(hi)

    def predict(self, df):
        return df["gn_l12"] * np.exp(self.res.predict(df))


class LG(L2):
    """Growth + calendar only (no seats). Shows how much of L2's skill comes from seats."""
    name = "LG"

    def fit(self, train):
        t = train.dropna(subset=["dln_gn", "d_ramadan", "d_eid"])
        terms = [v for v in ("d_ramadan", "d_eid") if t[v].std() > 0] or ["1"]
        self.formula = "dln_gn ~ " + " + ".join(terms)
        self.res = smf.wls(self.formula, data=t, weights=np.sqrt(t["gn_l12"])).fit()
        return self


def market_elasticities(panel, pooled_beta):
    """L2b: per-market seat elasticity, shrunk toward the pooled beta and clipped to [0, 1].

    Not validated in the back-test yet; use only for grade-A markets.
    """
    rows = []
    for m, x in panel.dropna(subset=["dln_gn", "dln_seats"]).groupby("market"):
        if len(x) < 12 or x["dln_seats"].std() < 0.05:
            continue
        r = smf.ols("dln_gn ~ dln_seats + d_ramadan", data=x).fit()
        rows.append((m, r.params["dln_seats"], r.bse["dln_seats"], len(x)))
    e = pd.DataFrame(rows, columns=["market", "beta_raw", "se", "n"]).set_index("market")
    tau2 = max(e["beta_raw"].var() - (e["se"] ** 2).mean(), 0.01)
    e["weight"] = tau2 / (tau2 + e["se"] ** 2)
    e["beta_shrunk"] = (e["weight"] * e["beta_raw"] + (1 - e["weight"]) * pooled_beta).clip(0, 1)
    e["ci_low"] = e["beta_raw"] - 1.96 * e["se"]
    return e
