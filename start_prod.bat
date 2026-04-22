@echo off
echo Starting AdvocAI (Production Mode)...

REM ── Ollama (local LLM) ─────────────────────────────────────
start "AdvocAI Ollama" powershell -NoExit -Command "ollama serve"

REM Give Ollama 3 seconds to start before backend tries to connect
timeout /t 3 /nobreak > nul

REM ── Backend ────────────────────────────────────────────────
start "AdvocAI Backend" powershell -NoExit -Command "cd 'D:\Programming Codes\Projects\Advocai'; advocai_env\Scripts\Activate.ps1; uvicorn orchestrator.app:app --host 0.0.0.0 --port 8000"

REM Give backend 3 seconds to load before opening frontend
timeout /t 3 /nobreak > nul

REM ── Frontend ───────────────────────────────────────────────
REM Note: Make sure to run `npm run build` in the frontend directory before running this script for the first time.
start "AdvocAI Frontend" powershell -NoExit -Command "cd 'D:\Programming Codes\Projects\Advocai\frontend'; npm run start"

echo.
echo  Ollama   -> http://localhost:11434
echo  Backend  -> http://localhost:8000
echo  Frontend -> http://localhost:3000
echo.
timeout /t 5 /nobreak > nul
start http://localhost:3000
