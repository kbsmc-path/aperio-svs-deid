@echo off
rem SVS De-identification - double-click to start, or drag a folder onto this file.
rem Uses the first Python 3.8+ that actually runs: .venv\Scripts\python.exe, then python, then the py launcher.
rem No extra packages are needed. If Windows blocks this file ("Smart App Control blocked" / "Dangerous file
rem extension from the web"), right-click the downloaded ZIP > Properties > Unblock and extract again - see README.
setlocal
cd /d "%~dp0"

set "PY=.venv\Scripts\python.exe"
if exist "%PY%" call :usable && goto run
set "PY=python"
call :usable && goto run
set "PY=py -3"
call :usable && goto run

echo Python 3.8 or newer is required.
echo Install it from https://www.python.org/downloads/  ^(tick "Add python.exe to PATH"^), then run this again.
pause
exit /b 1

:usable
rem Succeeds only if %PY% really starts and is 3.8+ (the Microsoft Store "python" stub fails here).
call %PY% -c "import sys; sys.exit(sys.version_info < (3, 8))" >nul 2>nul
exit /b

:run
%PY% svs_meta_gui.py %*
if errorlevel 1 pause
