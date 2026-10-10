# AERIVA core: reproduction report

Flight rows after cleaning: 117,589 (removed 19)
Markets in panel: 33 · share of international guest-nights covered: 92.2%

## Rolling back-test (h = 1)

| Model | Market WAPE | Error on total | Skill (market / total) |
|---|---|---|---|
| L0 | 24.3% | 19.3% | 0% / 0% |
| L1 | 19.1% | 10.3% | 21% / 46% |
| LG | 20.6% | 8.6% | 15% / 56% |
| L2 | 18.5% | 5.7% | 24% / 70% |

LG = growth + calendar only (no seats); shows how much of L2's gain comes from seats.
All horizons use the target month's actual seats (conditional back-test).

L2 market WAPE by horizon: h=1: 18.5%, h=3: 18.3%, h=6: 18.3%
L1 beta chosen on training data only: 0.55-0.65
80% interval coverage (L2, h=1): 80%
L2 bias on Abu Dhabi total by year (+ = over-forecast): 2024: -2.5%, 2025: +5.4%

## Stability and placebo

Seat elasticity by year: 2023: 0.52 (0.44-0.60), 2024: 0.60 (0.52-0.68), 2025: 0.28 (0.18-0.37)
Placebo: this year's seats 0.59; NEXT year's seats -0.07 (-0.15 to 0.01)
Correlation seats vs guest-nights: Abu Dhabi monthly total 0.88; market-month pooled 0.65

## Full-sample L2

alpha 0.106 · beta 0.520 (95% 0.47-0.57) · gamma (Ramadan) -0.282 · delta (Eid) -0.027

## Kuwait 2023 replay (trained before Jul 2023)

| month   |   seats_l12 |   seats |   gn_l12 |    gn |      L2 |    L0 |
|:--------|------------:|--------:|---------:|------:|--------:|------:|
| 2023-07 |        6065 |   26945 |    14402 | 43177 | 30323.7 | 14402 |
| 2023-08 |        6770 |   30647 |    18011 | 59515 | 38622.3 | 18011 |
| 2023-09 |        6180 |   27166 |    11564 | 23822 | 24524.2 | 11564 |

## Example scenario: Kuwait Aug 2024, +20% seats

Baseline 71,263 guest-nights -> change +7,087 (range +6,376 to +7,804)