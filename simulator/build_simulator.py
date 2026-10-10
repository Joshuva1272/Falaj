"""Build the simulator page: inject aeriva_sim_data.json into simulator_template.html.

Usage:  python simulator/build_simulator.py
Output: simulator/AERIVA_Simulator.html (one self-contained file; open it in a browser)
"""
import json
from pathlib import Path

here = Path(__file__).resolve().parent
template = (here / "simulator_template.html").read_text(encoding="utf-8")
data = (here / "aeriva_sim_data.json").read_text(encoding="utf-8")
json.loads(data)  # fail early if the export is broken
assert "/*DATA*/" in template, "placeholder /*DATA*/ missing from the template"
out = here / "AERIVA_Simulator.html"
out.write_text(template.replace("/*DATA*/", "window.__D=" + data + ";"), encoding="utf-8")
print(f"wrote {out} ({out.stat().st_size:,} bytes)")
