@echo off
echo Starting AdvocAI...

REM ── Ollama (local LLM) ─────────────────────────────────────
start "AdvocAI Ollama" powershell -NoExit -Command "ollama serve"

REM Give Ollama 3 seconds to start before backend tries to connect
timeout /t 3 /nobreak > nul

REM ── Backend ────────────────────────────────────────────────
start "AdvocAI Backend" powershell -NoExit -Command "cd 'D:\Programming Codes\Projects\Advocai'; advocai_env\Scripts\Activate.ps1; uvicorn orchestrator.app:app --reload --host 127.0.0.1 --port 8000"

REM Give backend 3 seconds to load before opening browser
timeout /t 3 /nobreak > nul

REM ── Frontend ───────────────────────────────────────────────
start "AdvocAI Frontend" powershell -NoExit -Command "cd 'D:\Programming Codes\Projects\Advocai\frontend'; npm run dev"

echo.
echo  Ollama   → http://localhost:11434
echo  Backend  → http://localhost:8000
echo  Frontend → http://localhost:3000
echo  API Docs → http://localhost:8000/docs
echo.
timeout /t 5 /nobreak > nul
start http://localhost:3000