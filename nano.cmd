@echo off
setlocal

:: KaiNova Nano-CMD — Professional CLI Wrapper
:: Stamped with Phase 14 Stabilization Logic

if "%1"=="" goto status
if "%1"=="onboard" goto onboard
if "%1"=="config" goto config
if "%1"=="logs" goto logs
if "%1"=="start" goto start
if "%1"=="status" goto status
if "%1"=="doctor" goto doctor

:status
py nano.py
goto end

:onboard
py onboard_ui.py
goto end

:config
if exist .env (
    echo [OPENING] .env in Notepad...
    notepad .env
) else (
    echo [ERROR] .env missing. Run 'nano onboard' first.
)
goto end

:logs
if exist logs (
    echo [OPENING] Latest Bot Logs...
    powershell -Command "Get-Content -Path logs/bot.log -Tail 20 -Wait"
) else (
    echo [ERROR] No logs found. Run 'nano start' first.
)
goto end

:start
py start_all.py
goto end

:doctor
py diagnose.py
goto end

:end
endlocal
