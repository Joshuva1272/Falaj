"""Shock replay: train only on data before a capacity jump, then forecast it."""
import pandas as pd
from .models import L0, L2


def replay(panel, market, cutoff, months):
    cutoff = pd.Period(cutoff, "M")
    train = panel[panel["month"] < cutoff]
    m = L2().fit(train)
    x = panel[(panel["market"] == market) & panel["month"].astype(str).isin(months)].copy()
    x["L2"] = m.predict(x).values
    x["L0"] = L0().predict(x).values
    return x[["month", "seats_l12", "seats", "gn_l12", "gn", "L2", "L0"]], m
