@echo off
rem Build PCScope.exe on Windows. Double-click this file or run it from a
rem terminal in this folder. Requires Python 3.10 - 3.13 (64-bit).

setlocal

where py >nul 2>nul && set "PY=py -3" || set "PY=python"

echo === Installing build dependencies ===
%PY% -m pip install --upgrade pip || goto :error
%PY% -m pip install -r requirements-build.txt || goto :error

echo === Building ===
%PY% -m PyInstaller --noconfirm --clean pcscope.spec || goto :error

echo.
echo Done. Output:
echo   dist\PCScope.exe      - the windowed app
echo   dist\PCScopeCLI.exe   - command line runner
echo.
pause
exit /b 0

:error
echo.
echo Build failed with error %errorlevel%.
pause
exit /b %errorlevel%
