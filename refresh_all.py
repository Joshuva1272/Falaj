"""One command from DCT files to the simulator page.

    python refresh_all.py                 # engine -> export -> build
    python refresh_all.py --skip-engine   # reuse existing results, only export + build

Steps:
  1. aeriva_core/run_all.py      evidence, back-test, panel        -> aeriva_core/results
  2. aeriva_core/predict_test.py nowcast for withheld hotel months -> aeriva_core/predictions
  3. export/export_sim_data.py   one JSON for the page              -> simulator/aeriva_sim_data.json
  4. simulator/build_simulator.py the page                          -> simulator/AERIVA_Simulator.html
"""
import argparse, subprocess, sys
from pathlib import Path

root = Path(__file__).resolve().parent
ap = argparse.ArgumentParser()
ap.add_argument("--skip-engine", action="store_true")
a = ap.parse_args()

def run(*args):
    print("\n>>", " ".join(str(x) for x in args), flush=True)
    subprocess.run([sys.executable, *map(str, args)], cwd=root, check=True)

if not a.skip_engine:
    run(root / "aeriva_core/run_all.py", "--data-dir", root / "data", "--out", root / "aeriva_core/results")
    run(root / "aeriva_core/predict_test.py", "--data-dir", root / "data", "--out", root / "aeriva_core/predictions")
run(root / "export/export_sim_data.py", "--core", root / "aeriva_core", "--data", root / "data",
    "--out", root / "simulator/aeriva_sim_data.json")
run(root / "simulator/build_simulator.py")
print("\nDone. Open simulator/AERIVA_Simulator.html")
