@echo off
cd /d c:\Users\User\OneDrive\Documents\VSCode\BDS\bds-agent
.\venv\Scripts\python.exe -m uvicorn api.main:app --host 0.0.0.0 --port 8001
pause
