from fastapi import FastAPI, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import subprocess
import os
import sys
from pathlib import Path

from .state import state
from .schemas import RefitRequest

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

root = Path(__file__).resolve().parent.parent

@app.get("/api/meta")
def get_meta():
    if not state.data:
        return JSONResponse(status_code=503, content={"error": "State not loaded"})
    return {
        "status": "live",
        "data_version": "2026-10-08",
        "months": state.data.get("months", [])
    }

@app.get("/api/data")
def get_data():
    if not state.data:
        return JSONResponse(status_code=503, content={"error": "State not loaded"})
    return state.data

def run_engine_task():
    # Run the refresh_all.py script
    subprocess.run([sys.executable, str(root / "refresh_all.py")], cwd=str(root))
    state.load_state()

@app.post("/api/admin/refit")
def refit_engine(background_tasks: BackgroundTasks):
    background_tasks.add_task(run_engine_task)
    return {"status": "started", "job_id": "refit_1"}

@app.get("/")
def serve_simulator():
    html_path = root / "simulator" / "AERIVA_Simulator.html"
    return FileResponse(html_path)

