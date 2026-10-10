# Simulator + AerivaCore

Everything needed to go from the DCT data files to the AERIVA four-screen simulator, in one folder.

## Run it

```bash
pip install -r aeriva_core/requirements.txt
python refresh_all.py                 # engine -> export -> build (about 3-4 minutes)
python refresh_all.py --skip-engine   # only re-export and rebuild the page (about 1 minute)
```

Then open `simulator/AERIVA_Simulator.html` in a browser. It is one self-contained file and works offline.

## What is where

| Folder / file | What it holds |
|---|---|
| `data/` | The five DCT Excel files the engine reads (`flight_data.xlsx`, international and domestic train/test). Copies of the files in `01a - DCT Dataset`, renamed to the names the engine expects. |
| `aeriva_core/` | The Python engine (from `aeriva_core_4`): loading, features, models L0/L1/LG/L2, back-test, nowcast, scenarios, replays. `results/` and `predictions/` hold its latest outputs. |
| `export/export_sim_data.py` | Turns the engine's outputs into one JSON file for the page: forecasts, 80% ranges, grades, back-tests, replays, holiday terms. |
| `simulator/simulator_template.html` | The simulator page without data (the `/*DATA*/` placeholder is filled at build time). Edit design and logic here. |
| `simulator/aeriva_sim_data.json` | The exported data the page shows. |
| `simulator/build_simulator.py` | Injects the JSON into the template. |
| `simulator/AERIVA_Simulator.html` | The built simulator: Market Radar, Scenario Studio, Decision Card, Evidence Lab. |
| `refresh_all.py` | Runs every step above in order. |
| `integration/AERIVA_Live_Engine_Plan.html` | Plan for connecting the page to the live engine through a local FastAPI server: architecture, endpoints, screen wireframes, build order. |
| `docs/guide_screenshots/` | Numbered screenshots used in the user guide. |
| `docs/AERIVA_Decision_Card_sample.png` | Example Decision Card export (Kuwait, Aug 2026, +20% seats). |
| `docs/radar_design_demo.html` | The radar design demo approved before it went into the simulator. |

## How the pieces connect

```
data/*.xlsx
   -> aeriva_core/run_all.py        -> aeriva_core/results/      (panel, back-test, elasticities, replays)
   -> aeriva_core/predict_test.py   -> aeriva_core/predictions/  (nowcast for withheld hotel months)
   -> export/export_sim_data.py     -> simulator/aeriva_sim_data.json
   -> simulator/build_simulator.py  -> simulator/AERIVA_Simulator.html
```

Checked on 8 Oct 2026: running `refresh_all.py` from scratch in this folder reproduces the published simulator's data with no differences.

## Feeding in new data

1. Replace the files in `data/` (same names and columns).
2. Run `python refresh_all.py`.
3. Open the rebuilt `simulator/AERIVA_Simulator.html`.

The target months are set in `export/export_sim_data.py` (`--first 2025-08 --last 2026-08`); move them if the data period changes. A few figures are still typed into `simulator_template.html` and need a manual update after a refit: the L2 coefficients, bias by year, elasticity by year, placebo result, nowcast error and the brief-check table. The live-engine plan removes these.

## Online versions (private to the owner until shared)

- Simulator: https://claude.ai/artifact/RaAh5ideSHP9PjcwCdrmdo
- User guide (every screen, button and chart explained): https://claude.ai/code/artifact/b1f05078-b0fb-40af-8cb0-2200f0f0eada
- Live-engine plan: https://claude.ai/artifact/WKWWsmNEQrw4D5kGzmZZ8v

## Next

`aeriva_api/` (FastAPI server so the page calls the engine directly) will be added here, following `integration/AERIVA_Live_Engine_Plan.html`.

## Branding (FALAJ)

- `simulator/simulator_template.html` carries the FALAJ brand (palette, fonts, header, Radar brand band, branded Decision Card and export). Model code and data are unchanged; checked on 9 Oct 2026 against the original (same results on 3,861 scenarios and the brief checks).
- The logo is embedded in the template as base64, so the build still writes one self-contained file. Source logo files are in `simulator/assets/`; `simulator/brand_patch.py` re-applies the brand to an unbranded template.
- Pre-branding copies of the changed files: `..\_backup_pre_FALAJ_2026-10-09\`.
- Colour scheme: **Palm Shade** (approved 9 Oct 2026; replaces Black & Gold; colour only, in the CSS block "FALAJ colour scheme: Palm Shade" (light mode; dark-mode tokens unchanged) plus the chart and Decision Card export colours). Model code, data and layout unchanged. Black & Gold copies: `..\_backup_pre_PalmShade_2026-10-09\`; pre-Black & Gold copies: `..\_backup_pre_BlackGold_2026-10-09\`.

## Notes

- The page is branded **FALAJ | فلج** (since 9 Oct 2026). "AERIVA" remains only in internal names: the output file `AERIVA_Simulator.html` (kept so `aeriva_api` and existing links keep working), `aeriva_core`, `aeriva_sim_data.json`. The online versions listed above still show the earlier AERIVA design until republished.
- Association, not causation. Abu Dhabi hotels only. Occupancy is estimated from guest nights. No room rates.
