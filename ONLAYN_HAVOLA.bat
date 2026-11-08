@echo off
chcp 65001 >nul
title Natural Oil ERP - internet havolasi
set "ROOT=%~dp0"
set "CF=%ROOT%tools\cloudflared.exe"

echo ============================================================
echo   Natural Oil ERP - boshqa kompyuter va telefondan kirish
echo ============================================================
echo.
echo  OLDIN "ISHGA_TUSHIRISH.bat" ishlab turgan bo'lishi kerak!
echo.

if not exist "%CF%" (
  echo [1/2] cloudflared yuklab olinmoqda ^(bir marta, ~20 MB^)...
  if not exist "%ROOT%tools" mkdir "%ROOT%tools"
  curl.exe -L --fail -o "%CF%" https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe
  if errorlevel 1 (
    echo [XATO] Yuklab bo'lmadi. Internetni tekshiring.
    pause
    exit /b 1
  )
)

echo [2/2] Havola ochilmoqda...
echo.
echo  Pastda "https://....trycloudflare.com" degan manzil chiqadi.
echo  Shu manzilni nusxalab, boshqa kompyuter yoki telefonga yuboring.
echo.
echo  - Havola shu oyna OCHIQ turganda ishlaydi.
echo  - Har safar ishga tushirganda havola YANGI bo'ladi.
echo  - To'xtatish uchun shu oynani yoping.
echo ============================================================
echo.
"%CF%" tunnel --no-autoupdate --url http://localhost:5174
pause
