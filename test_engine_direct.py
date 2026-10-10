import sys
from pathlib import Path
import json

root = Path(__file__).resolve().parent
sys.path.insert(0, str(root / "aeriva_core"))

from aeriva import scenario
import pandas as pd

# Load the exported JSON to get the exact base values for gn_base, seats_base, beta.
# (This is equivalent to what the engine produces for the base forecast)
with open("simulator/aeriva_sim_data.json", "r") as f:
    data = json.load(f)

months = data["months"]

cases = [
    ("KUWAIT", "2026-08", "Seats +%", {"pct": 20}),
    ("UNITED KINGDOM", "2025-12", "Seats +%", {"pct": -15}),
    ("SAUDI ARABIA", "2026-03", "New route", {"new": 5000}),
    ("INDIA", "2026-01", "Seats +%", {"pct": 10}),
    ("CHINA", "2026-02", "Seats +%", {"pct": -10}),
    ("RUSSIAN FEDERATION", "2025-11", "New route", {"new": 2000}),
    ("GERMANY", "2026-05", "Seats +%", {"pct": 25}),
    ("UNITED STATES OF AMERICA", "2026-04", "Seats +%", {"pct": -5}),
    ("QATAR", "2025-10", "New route", {"new": 1000}),
    ("OMAN", "2026-06", "Seats +%", {"pct": 15}),
]

print("Market | Month | Lever | Input | Engine Delta GN")
print("-" * 60)
for market, month, lever, vals in cases:
    if market not in data["mk"] or month not in months:
        continue
    
    idx = months.index(month)
    row = data["mk"][market]["r"][idx]
    if not row: continue
    
    s_base = row[0]
    gn_l12 = row[2]
    
    # We use the precise base calculation logic from the UI using the precomputed values
    AL=0.106; GAM=-0.282; DEL=-0.027; B0=0.52
    import math
    dl = math.log(s_base / row[1]) if row[1] > 0 else 0
    cr = GAM * data["dram"][idx]
    ce = DEL * data["deid"][idx]
    gn_base = gn_l12 * math.exp(AL + B0 * dl + cr + ce)
    
    mk = data["mk"][market]
    beta = mk["b"] if mk["g"] == "A" else 0.52
    beta_range = (mk["lo"] if mk["g"]=="A" and mk["lo"] is not None else 0.47, beta, 0.57)

    # Use the aeriva_core engine function!
    if lever == "Seats +%":
        # The engine accepts pct as 0.20 for 20%
        res = scenario.seats_change(gn_base=gn_base, seats_base=s_base, pct=vals["pct"]/100.0, beta=beta_range)
    elif lever == "New route":
        # We model this by passing seats_new explicitly
        res = scenario.seats_change(gn_base=gn_base, seats_base=s_base, seats_new=s_base + vals["new"], beta=beta_range)
    
    # In some cases the frontend restricts the cut to max 95% (seats * 0.05). Let's see raw engine output.
    delta = res.delta_central
    print(f"{market} | {month} | {lever} | {vals} | {int(round(delta))}")
