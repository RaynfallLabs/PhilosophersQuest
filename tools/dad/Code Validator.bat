@echo off
rem Dad's Code Validator: double-click to open it.
rem pyw opens the window with no console behind it; without pyw, py runs it
rem in this console and keeps it open if anything goes wrong.
where pyw >nul 2>nul
if %errorlevel%==0 (
    start "" pyw "%~dp0code_validator.py"
    exit /b 0
)
py "%~dp0code_validator.py"
if errorlevel 1 pause
