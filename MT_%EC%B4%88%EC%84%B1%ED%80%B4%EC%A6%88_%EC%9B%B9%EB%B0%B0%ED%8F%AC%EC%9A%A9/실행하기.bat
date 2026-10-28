@echo off
chcp 65001 >nul
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel%==0 (set "PY=py -3") else (set "PY=python")
%PY% -m pip install -r requirements.txt
if errorlevel 1 (
 echo Python 설치 및 인터넷 연결을 확인하세요.
 pause
 exit /b 1
)
%PY% server.py
pause
