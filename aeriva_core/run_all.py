"""Reproduce the brief's evidence from the three challenge files.

Usage:
    python run_all.py --data-dir path/to/files --out results
"""
import argparse, json, warnings
warnings.filterwarnings("ignore", category=FutureWarning)
from pathlib import Path
import pandas as pd
from aeriva import data, features, backtest, replay, scenario, evidence
from aeriva.models import L2, market_elasticities


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", required=True)
    ap.add_argument("--out", default="results")
    ap.add_argument("--no-clean", action="store_true", help="skip flight cleaning (raw data)")
    a = ap.parse_args()
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)

    print("Loading data ...")
    f = data.load_flights(a.data_dir, clean=not a.no_clean)
    i = data.load_international(a.data_dir)
    d = data.load_domestic(a.data_dir)
    integ = data.integrity_report(f, i, d)
    json.dump(integ, open(out / "integrity.json", "w"), indent=2, default=str)

    print("Building panel ...")
    p = features.build_panel(f, i)
    p.to_csv(out / "panel.csv", index=False)
    cov = i[i["market"].isin(p["market"].unique())]["Guests"].sum() / i["Guests"].sum()

    print("Rolling back-test (19 origins x 3 horizons) ...")
    origins = pd.period_range("2024-01", "2025-07", freq="M")
    bt = backtest.rolling_backtest(p, origins)
    bt.to_csv(out / "backtest_detail.csv", index=False)
    summ = backtest.summary(bt); summ.to_csv(out / "backtest_summary.csv", index=False)
    covg = backtest.interval_coverage(bt)
    mk = backtest.market_table(bt); mk.to_csv(out / "market_wape.csv")
    bias = backtest.bias_by_year(bt); bias.to_csv(out / "bias_by_year.csv")
    byr = evidence.beta_by_year(p); byr.to_csv(out / "beta_by_year.csv", index=False)
    plc = evidence.placebo_lead(p); plc.to_csv(out / "placebo_test.csv")
    corr = evidence.pooled_correlation(p)

    print("Full-sample L2 and market elasticities ...")
    m = L2().fit(p)
    params = pd.DataFrame({"coef": m.params, "ci_low": m.res.conf_int()[0], "ci_high": m.res.conf_int()[1]})
    params.to_csv(out / "l2_params.csv")
    el = market_elasticities(p, m.beta)
    el["backtest_wape"] = mk.reindex(el.index)
    el["grade"] = [backtest.confidence_grade(w, lo) if pd.notna(w) else "n/a" for w, lo in zip(el["backtest_wape"], el["ci_low"])]
    el.to_csv(out / "market_elasticities.csv")

    print("Shock replays ...")
    kw, _ = replay.replay(p, "KUWAIT", "2023-07", ["2023-07", "2023-08", "2023-09"])
    cn, _ = replay.replay(p, "CHINA", "2023-04", ["2023-04", "2023-05", "2023-06", "2023-07"])
    kw.to_csv(out / "replay_kuwait_2023.csv", index=False); cn.to_csv(out / "replay_china_2023.csv", index=False)

    # example scenario: Kuwait Aug 2024 +20% seats
    row = p[(p["market"] == "KUWAIT") & (p["month"] == pd.Period("2024-08", "M"))].iloc[0]
    sc = scenario.seats_change(row["gn"], row["seats"], pct=0.20)

    h1 = summ[summ["h"] == 1].set_index("model")
    lines = [
        "# AERIVA core: reproduction report", "",
        f"Flight rows after cleaning: {integ['flight_rows']:,} (removed {integ['flight_rows_removed_by_cleaning']})",
        f"Markets in panel: {p['market'].nunique()} · share of international guest-nights covered: {cov:.1%}", "",
        "## Rolling back-test (h = 1)", "",
        "| Model | Market WAPE | Error on total | Skill (market / total) |", "|---|---|---|---|",
    ]
    for mname, r in h1.iterrows():
        lines.append(f"| {mname} | {r.market_wape:.1%} | {r.total_error:.1%} | {r.skill_market:.0%} / {r.skill_total:.0%} |")
    l1b = bt.groupby("origin")["l1_beta"].first()
    lines += ["", "LG = growth + calendar only (no seats); shows how much of L2's gain comes from seats.",
              "All horizons use the target month's actual seats (conditional back-test)."]
    lines += ["", f"L2 market WAPE by horizon: " + ", ".join(f"h={int(r.h)}: {r.market_wape:.1%}" for _, r in summ[summ.model == 'L2'].iterrows()),
              f"L1 beta chosen on training data only: {l1b.min():.2f}-{l1b.max():.2f}",
              f"80% interval coverage (L2, h=1): {covg:.0%}",
              "L2 bias on Abu Dhabi total by year (+ = over-forecast): " + ", ".join(f"{y}: {v:+.1%}" for y, v in bias.items()), "",
              "## Stability and placebo", "",
              "Seat elasticity by year: " + ", ".join(f"{int(r.year)}: {r.beta:.2f} ({r.ci_low:.2f}-{r.ci_high:.2f})" for r in byr.itertuples()),
              f"Placebo: this year's seats {plc.loc['dln_seats','coef']:.2f}; NEXT year's seats {plc.loc['dln_seats_lead','coef']:.2f} "
              f"({plc.loc['dln_seats_lead','ci_low']:.2f} to {plc.loc['dln_seats_lead','ci_high']:.2f})",
              f"Correlation seats vs guest-nights: Abu Dhabi monthly total {corr['abu_dhabi_total_monthly']:.2f}; market-month pooled {corr['market_month_level']:.2f}", "",
              "## Full-sample L2", "",
              f"alpha {m.params['Intercept']:.3f} · beta {m.beta:.3f} (95% {m.beta_ci()[0]:.2f}-{m.beta_ci()[1]:.2f}) · "
              f"gamma (Ramadan) {m.params['d_ramadan']:.3f} · delta (Eid) {m.params['d_eid']:.3f}", "",
              "## Kuwait 2023 replay (trained before Jul 2023)", "", kw.to_markdown(index=False), "",
              "## Example scenario: Kuwait Aug 2024, +20% seats", "",
              f"Baseline {sc.gn_base:,.0f} guest-nights -> change {sc.delta_central:+,.0f} (range {sc.delta_low:+,.0f} to {sc.delta_high:+,.0f})"]
    (out / "report.md").write_text("\n".join(lines))
    print("\n".join(lines))


if __name__ == "__main__":
    main()
