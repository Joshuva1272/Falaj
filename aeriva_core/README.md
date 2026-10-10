# AERIVA core

Reusable Python code behind the *AERIVA Data Evidence & System Design Brief*. It loads the three challenge files, builds the market × month panel, runs the forecasting models L0/L1/L2 with a rolling back-test, and provides the scenario engine and shock replays.

> AERIVA is a working name only. The data files are **not** included: place the three challenge files in a folder and point the code at it.

## Quick start

```bash
pip install -r requirements.txt
python run_all.py --data-dir path/to/data --out results        # evidence + back-test, ~25 s
python predict_test.py --data-dir path/to/data --out predictions   # fill Guests in the test files
pytest -q                                                        # sanity tests
```

The data folder must contain `flight_data.xlsx`, `data_international_train.xlsx`, `data_domestic_train.xlsx` and, for `predict_test.py`, `data_international_test.xlsx` and `data_domestic_test.xlsx`. For a guided walk-through, open `quickstart.ipynb`, set `DATA_DIR`, and run all cells.

`run_all.py` writes to `results/`:

| File | Content |
|---|---|
| `report.md` | Summary: back-test table, interval coverage, L2 coefficients, Kuwait replay, example scenario |
| `integrity.json` | Data checks from Phase 1 (identities, duplicates, coverage, markets without flights) |
| `panel.csv` | Market × month panel with all monthly features |
| `backtest_detail.csv` | Every forecast: market, target month, origin, horizon, L0/L1/L2, actual |
| `backtest_summary.csv` | WAPE, error on total and skill by model and horizon |
| `market_wape.csv` | L2 back-test WAPE per market |
| `l2_params.csv` | Full-sample L2 coefficients with 95% intervals |
| `market_elasticities.csv` | L2b per-market elasticities (raw, shrunk, grade) |
| `replay_kuwait_2023.csv`, `replay_china_2023.csv` | Shock replays |

## Code map (module → brief section)

| Module | What it does | Brief |
|---|---|---|
| `aeriva/config.py` | File names, Ramadan/Eid calendar, cleaning rules, gateway cut-offs | 4D, Appendix A.3 |
| `aeriva/data.py` | Load and clean the three files; integrity report | 4D steps 1–3, 6 |
| `aeriva/features.py` | Base aggregates and features F1–F10, F16, F17; market × month panel | 4E, Appendix A |
| `aeriva/models.py` | `L0`, `L1`, `L2`, `market_elasticities` (L2b) | 4F |
| `aeriva/backtest.py` | Rolling-origin back-test, WAPE, skill, interval coverage, prediction interval, confidence grade | 4G, 4I |
| `aeriva/scenario.py` | Seats %, frequency, route cut with recapture, stopover, yield per 1,000 seats, occupancy impact | 4H, Appendix B |
| `aeriva/replay.py` | Train before a capacity jump, forecast it | Section 2 |
| `aeriva/daily.py` | Split a monthly forecast into days (same weekday last year) | 4F (daily output) |
| `aeriva/evidence.py` | Elasticity by year, placebo test, correlations | Section 2 (E15–E16) |
| `aeriva/nowcast.py` | Stock-flow nowcast: daily Guests from daily New Arrivals with a fitted stay kernel | Test-file scoring |
| `predict_test.py` | Writes `*_test_predicted.xlsx` with the Guests column filled, plus validation and stay kernels | Test-file scoring |

## Core API

```python
from aeriva import data, features, backtest, scenario
from aeriva.models import L2

f = data.load_flights("data"); i = data.load_international("data")
p = features.build_panel(f, i)                 # market x month panel

m = L2().fit(p[p.month < pd.Period("2025-01", "M")])
forecast = m.predict(p[p.month == pd.Period("2025-03", "M")])

r = scenario.seats_change(gn_base=40_000, seats_base=30_000, pct=0.20)
r.delta_low, r.delta_central, r.delta_high     # change in guest-nights, with range
```

## Results from this code (cleaned data)

| Model | Market WAPE | Error on Abu Dhabi total | Skill (market / total) |
|---|---|---|---|
| L0 same month last year | 24.3% | 19.3% | — |
| L1 last year × seats^β (β chosen on training data: 0.55–0.65) | 19.1% | 10.3% | 21% / 46% |
| LG growth + calendar only (no seats) | 20.6% | 8.6% | 15% / 56% |
| L2 selected regression | 18.5% | 5.7% | 24% / 70% |

- The back-test is conditional on seats: each horizon uses the target month's actual seats. L2 market WAPE at 1, 3 and 6 months: 18.5%, 18.3%, 18.3%. 80% interval coverage: 80%.
- Bias on the Abu Dhabi total: 2024 −2.5%, 2025 +5.4%. Elasticity by year: 0.52, 0.60, 0.28. Placebo (next year's seats): −0.07. See `aeriva/evidence.py`.
- Full-sample L2: α 0.106, β 0.520 (95% 0.47–0.57), Ramadan −0.282, Eid −0.027 (not significant).
- Kuwait replay (trained before July 2023): Jul 30,324 / Aug 38,622 forecast vs 43,177 / 59,515 actual; baseline 14,402 / 18,011.

**Why these differ slightly from the brief:** the brief's figures were computed on the raw flight file. This code applies the cleaning the brief specifies (19 rows removed: private, cargo and unknown operators, and one load factor above 120%). It also fixes a small look-ahead: the L1 factor is now chosen on training data only, instead of 0.5 picked with 2025 in view. With `--no-clean`, L2 reproduces the brief exactly (18.4% / 5.7%, β 0.507, 0.46–0.55).

## Test files and the stock-flow nowcast

The released test files cover **1 Aug 2025 – 28 Feb 2026** for both international (9,202 rows, 45 nationalities) and domestic (212 days). `Guests` is withheld; `New Arrivals` and `Same-Day Guests` are supplied.

Because arrivals are supplied, Guests can be rebuilt from them: guests on day *d* are the people who arrived on *d* or earlier and have not yet left. `nowcast.py` fits a stay kernel per market (weights on arrival lags 0, 1, 2, 3, 4–6, 7–13, 14–29, 30–59, 60–119 days) by non-negative least squares.

Validation on held-out training periods (daily, by nationality):

| Held-out period | File | Stock-flow WAPE | Same weekday last year |
|---|---|---|---|
| Jan – Jul 2025 | International | 12.1% | 27.7% (arrivals baseline 14.1%) |
| Aug 2024 – Feb 2025 (same season as the test) | International | 12.7% | 29.8% (arrivals baseline 15.3%) |
| Jan – Jul 2025 | Domestic | 7.2% | 17.1% (arrivals baseline 15.8%) |
| Aug 2024 – Feb 2025 | Domestic | 8.4% | 19.9% (arrivals baseline 13.7%) |

Per-day stay weights are constrained to decline with lag. Adding weekday and Ramadan adjustments made it worse (13.9%), so they are not used. `predict_test.py` also checks the nowcast against the seats model on the test months (`reconciliation_L2_vs_nowcast.csv`).

## Rules the code enforces

1. `New Arrivals` is used to predict `Guests` **only** when it is known for the target days (test files, months already flown). Forecasts made before arrivals are known use seats (L2). `Same-Day Guests` is never used.
2. Forecasts use seats for the target month, not passengers (passengers are unknown in advance).
3. Trailing features (average stay, Air-to-Hotel Ratio) use months *m−1 … m−12* only (tested in `tests/`).
4. Every model is re-fitted inside each back-test window. Lags are matched by calendar month, not row position.
5. Calendar terms with no variation in a short training window are dropped automatically.

## Not built yet (next steps for the team)

| Item | Status |
|---|---|
| Domestic daily model (weekday, Eid, National Day, Ramadan, lag 364) | Not built |
| Ramadan/Eid adjustment of daily shares in `daily.py` | Not built |
| L2b market elasticities in forecasts; grade cut-offs validated | Estimated only, not back-tested |
| L3 gradient boosting for daily scoring | Only a rough test so far |
| Streamlit screens: Market Radar, Scenario Studio, Decision Card, Evidence Lab | Not built |
| Seats → New Arrivals → Guests scenario chain (uses the stay kernel for timing) | Not built |

## Caveats

- Scenario outputs are associations learned from 2022–2025, not causal effects.
- The flight file covers AUH arrivals only. Visitors via Dubai or by road are not observed.
- The China 2023 replay trains on only three months of year-on-year data, so treat it as illustrative.
- Confirm 2026 Ramadan and Eid dates in `config.py` against official announcements.
