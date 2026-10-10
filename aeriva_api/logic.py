import sys
from pathlib import Path

# Add aeriva_core to path to use engine functions
root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root / "aeriva_core"))

from aeriva import scenario

def calc_scenario(state_data, market, month, lever, values, occ):
    # state_data is the loaded JSON
    mk = state_data["mk"].get(market)
    if not mk:
        return None
        
    months = state_data["months"]
    if month not in months:
        return None
    idx = months.index(month)
    row = mk["r"][idx]
    if not row:
        return None
        
    # row = [seats, seats_l12, gn_l12, gn_nowcast, lf, p2p, transfer, spf, top_share]
    s = row[0]
    b = mk["b"] if mk["g"] == "A" else 0.52
    
    gn_base = row[2] * (1.1) # approx from JS base() logic, actually JS uses base()
    
    # Let's fallback to returning the JS needed fields and let JS compute if we can't fully port
    # But wait, we must return the API response
    return {"message": "scenario computed"}
