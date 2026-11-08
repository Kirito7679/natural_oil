@echo off
chcp 65001 >nul
title Natural Oil ERP - ishga tushirish
set "ROOT=%~dp0"
set "BACKEND_PORT=8010"

echo ============================================
echo   Natural Oil ERP ishga tushirilmoqda...
echo ============================================
echo.

where python >nul 2>nul
if errorlevel 1 (
  echo [XATO] Python topilmadi. https://www.python.org dan o'rnating.
  pause
  exit /b 1
)
where npm >nul 2>nul
if errorlevel 1 (
  echo [XATO] Node.js topilmadi. https://nodejs.org dan o'rnating.
  pause
  exit /b 1
)

echo [1/4] Backend kutubxonalari tekshirilmoqda...
python -c "import fastapi,uvicorn,sqlalchemy,jose,passlib,openpyxl,pydantic_settings,multipart" >nul 2>nul
if errorlevel 1 (
  echo       O'rnatilmoqda, biroz kuting...
  python -m pip install fastapi==0.115.0 "uvicorn[standard]==0.30.0" sqlalchemy==2.0.35 pydantic==2.9.0 pydantic-settings==2.5.0 "python-jose[cryptography]==3.3.0" "passlib[bcrypt]==1.7.4" python-multipart==0.0.9 openpyxl==3.1.5
)

echo [2/4] Frontend kutubxonalari tekshirilmoqda...
if not exist "%ROOT%frontend\node_modules" (
  echo       npm install, 1-2 daqiqa kuting...
  pushd "%ROOT%frontend"
  call npm install
  popd
)

echo [3/4] Backend (port %BACKEND_PORT%) va frontend (port 5174) ochilmoqda...
start "Natural Oil - BACKEND (%BACKEND_PORT%)" cmd /k "cd /d "%ROOT%backend" && python -m uvicorn app.main:app --reload --port %BACKEND_PORT%"
start "Natural Oil - FRONTEND (5174)" cmd /k "cd /d "%ROOT%frontend" && npm run dev"

echo [4/4] Brauzer ochilmoqda...
timeout /t 6 /nobreak >nul
start "" http://localhost:5174

echo.
echo Tayyor! Login: 95 810 06 00  Parol: 1234567 (keyin o'zgartiring)
echo To'xtatish uchun "Natural Oil - BACKEND" va "FRONTEND" oynalarini yoping.
timeout /t 10
