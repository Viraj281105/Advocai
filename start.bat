@echo off
echo Starting AdvocAI...

REM Backend
start "AdvocAI Backend" powershell -NoExit -Command "cd 'D:\Programming Codes\Projects\Advocai'; advocai_env\Scripts\Activate.ps1; uvicorn orchestrator.app:app --reload"

REM Frontend
start "AdvocAI Frontend" powershell -NoExit -Command "cd 'D:\Programming Codes\Projects\Advocai\frontend'; npm run dev"

echo.
echo Backend  → http://localhost:8000
echo Frontend → http://localhost:3000
echo API Docs → http://localhost:8000/docs
echo.
timeout /t 3
start http://localhost:3000