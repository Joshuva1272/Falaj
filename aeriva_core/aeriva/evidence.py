"""Extra evidence for the Evidence Lab: stability by year and a placebo (lead) test."""
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

F = "dln_gn ~ dln_seats + d_ramadan + d_eid"


def beta_by_year(panel):
    rows = []
    u = panel.dropna(subset=["dln_gn", "dln_seats", "gn_l12"])
    for y, x in u.groupby(u["month"].dt.year):
        r = smf.wls(F, data=x, weights=np.sqrt(x["gn_l12"])).fit()
        lo, hi = r.conf_int().loc["dln_seats"]
        rows.append({"year": y, "beta": r.params["dln_seats"], "ci_low": lo, "ci_high": hi, "n": len(x)})
    return pd.DataFrame(rows)


def placebo_lead(panel):
    """Does NEXT year's seat change 'predict' this year's guest-night change? It should not."""
    lead = panel[["market", "month", "dln_seats"]].copy()
    lead["month"] = lead["month"] - 12
    p = panel.merge(lead.rename(columns={"dln_seats": "dln_seats_lead"}), on=["market", "month"], how="left")
    u = p.dropna(subset=["dln_gn", "dln_seats", "dln_seats_lead", "gn_l12"])
    r = smf.wls("dln_gn ~ dln_seats + dln_seats_lead + d_ramadan + d_eid", data=u, weights=np.sqrt(u["gn_l12"])).fit()
    ci = r.conf_int()
    return pd.DataFrame({"coef": r.params[["dln_seats", "dln_seats_lead"]],
                         "ci_low": ci.loc[["dln_seats", "dln_seats_lead"], 0],
                         "ci_high": ci.loc[["dln_seats", "dln_seats_lead"], 1]}).assign(n=len(u))


def pooled_correlation(panel):
    u = panel.dropna(subset=["gn", "seats"])
    tot = panel.groupby("month")[["gn", "seats"]].sum()
    return {"market_month_level": float(np.corrcoef(u["gn"], u["seats"])[0, 1]),
            "abu_dhabi_total_monthly": float(np.corrcoef(tot["gn"], tot["seats"])[0, 1])}
