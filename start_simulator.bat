@echo off
echo ===================================================
echo       Starting AERIVA Live Engine Backend
echo ===================================================
echo.
echo Launching the Simulator in your default browser...
echo.
echo (Keep this window open while you use the simulator. 
echo  To stop the engine, close this window or press Ctrl+C.)
echo.

:: Open the simulator page using the FastAPI server address
start http://localhost:8000/

:: Start the Python backend
python -m uvicorn aeriva_api.main:app --port 8000

pause
