@echo off
setlocal EnableDelayedExpansion

set BASE=C:\Users\virat.arya\ETG\SoftsDatabase - Documents\Database\Hardmine\Non Fundamental\Weather\AGGREGATION OF WEATHER
set LOG=%BASE%\Automator\run_cpc.log
set PYTHON=python
set INGEST_STATUS=ok
set GIT_STATUS=skipped

set GCM_INTERACTIVE=never
set GIT_TERMINAL_PROMPT=0

echo. >> "%LOG%"
echo ======================================== >> "%LOG%"
echo  CPC REFRESH  ^|  %DATE%  %TIME% >> "%LOG%"
echo ======================================== >> "%LOG%"

echo [1/1] Static refresh (CPTEC / CPC / GFS)...
echo [1/1] Static refresh (CPTEC / CPC / GFS)... >> "%LOG%"
%PYTHON% "%BASE%\Ingest\ingest_static.py" >> "%LOG%" 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Static failed >> "%LOG%"
    set INGEST_STATUS=error
    goto notify
)

echo [Git] Committing and pushing...
echo [Git] Committing and pushing... >> "%LOG%"
cd /d "%BASE%"
git add "Database\maps\"
git diff --cached --quiet
if %ERRORLEVEL% NEQ 0 (
    git commit -m "CPC refresh %DATE% %TIME%" >> "%LOG%" 2>&1
    git push >> "%LOG%" 2>&1
    if !ERRORLEVEL! EQU 0 (
        set GIT_STATUS=pushed
        echo Git push done. >> "%LOG%"
    ) else (
        set GIT_STATUS=failed
        echo ERROR: git push failed >> "%LOG%"
    )
) else (
    echo No changes to commit. >> "%LOG%"
    set GIT_STATUS=skipped
)

:notify
echo [Notify] Sending email... >> "%LOG%"
%PYTHON% "%BASE%\Automator\notify.py" %INGEST_STATUS% %GIT_STATUS% >> "%LOG%" 2>&1

echo Run finished: %DATE% %TIME% >> "%LOG%"
echo.
echo Done. Log: %LOG%
endlocal
