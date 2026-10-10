import json

with open("simulator/aeriva_sim_data.json", "r") as f:
    data = json.load(f)

months = data["months"]

cases = [
    # (Market, Month, Lever, Values)
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

print("Market | Month | Lever | Input | Expected Delta GN")
print("-" * 60)
for market, month, lever, vals in cases:
    if market not in data["mk"]: continue
    if month not in months: continue
    
    idx = months.index(month)
    row = data["mk"][market]["r"][idx]
    if not row: continue
    
    # row = [seats, seats_l12, gn_l12, gn_nowcast, lf, p2p, transfer, spf, top_share]
    s_base = row[0]
    gn_l12 = row[2]
    
    beta = data["mk"][market]["b"] if data["mk"][market]["g"] == "A" else 0.52
    
    # We need to approximate the gn_base as done in the JS frontend
    # JS: dl = Math.log(s/r[1]), cr=GAM*DR[i], ce=DEL*DE[i], fc=r[2]*Math.exp(AL+B0*dl+cr+ce)
    # JS: fc is the base forecast.
    AL=0.106; GAM=-0.282; DEL=-0.027; B0=0.52
    import math
    dl = math.log(s_base / row[1]) if row[1] > 0 else 0
    cr = GAM * data["dram"][idx]
    ce = DEL * data["deid"][idx]
    fc = gn_l12 * math.exp(AL + B0 * dl + cr + ce)
    
    if lever == "Seats +%":
        s_new = max(s_base * (1 + vals["pct"]/100), s_base * 0.05)
    elif lever == "New route":
        s_new = max(s_base + vals["new"], s_base * 0.05)
    
    ratio = s_new / s_base if s_base > 0 else 1
    dgn = fc * (ratio ** beta - 1)
    
    print(f"{market} | {month} | {lever} | {vals} | {int(round(dgn))}")
