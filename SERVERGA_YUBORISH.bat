@echo off
chcp 65001 >nul
title Natural Oil ERP - serverga yuborish
cd /d "%~dp0"

set /p IP=Server IP manzili: 
if "%IP%"=="" exit /b 1

echo.
echo [1/3] Fayllar tayyorlanmoqda...
tar -czf "%TEMP%\nop.tgz" --exclude=node_modules --exclude=__pycache__ --exclude=dist --exclude=.env --exclude=natural_oil.db* --exclude=.pytest_cache backend frontend deploy
if errorlevel 1 goto FAIL

echo [2/3] Serverga yuborilmoqda. Savol chiqsa "yes" deb yozing, keyin server parolini kiriting.
scp "%TEMP%\nop.tgz" root@%IP%:/root/nop.tgz
if errorlevel 1 goto FAIL

echo [3/3] O'rnatilmoqda, 3-7 daqiqa kuting. Parolni yana so'raydi.
ssh -t root@%IP% "rm -rf /opt/nop/src && mkdir -p /opt/nop/src && tar -xzf /root/nop.tgz -C /opt/nop/src && sed -i 's/\r$//' /opt/nop/src/deploy/install.sh && bash /opt/nop/src/deploy/install.sh"
if errorlevel 1 goto FAIL

echo.
echo Tugadi. Yuqoridagi manzil va parolni saqlab oling.
pause
exit /b 0

:FAIL
echo.
echo [XATO] Shu oynaning skrinshotini yuboring.
pause
exit /b 1
