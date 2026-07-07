@echo off
setlocal EnableDelayedExpansion

set BASE=C:\Users\virat.arya\ETG\SoftsDatabase - Documents\Database\Hardmine\Non Fundamental\Weather\AGGREGATION OF WEATHER
set MAPS=%BASE%\Database\maps
set LOG=%BASE%\Automator\run_morning.log
set PYTHON=python
set INGEST_STATUS=ok
set GIT_STATUS=skipped

set GCM_INTERACTIVE=never
set GIT_TERMINAL_PROMPT=0

echo. >> "%LOG%"
echo ======================================== >> "%LOG%"
echo  MORNING RUN  ^|  %DATE%  %TIME% >> "%LOG%"
echo ======================================== >> "%LOG%"

echo [1/6] ECMWF Open Data...
echo [1/6] ECMWF Open Data... >> "%LOG%"
%PYTHON% "%BASE%\Ingest\ingest.py" >> "%LOG%" 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] ECMWF failed >> "%LOG%"
    set INGEST_STATUS=error
    goto notify
)

echo [2/6] ECMWF OpenCharts...
echo [2/6] ECMWF OpenCharts... >> "%LOG%"
%PYTHON% "%BASE%\Ingest\ingest_opencharts.py" >> "%LOG%" 2>&1
if %ERRORLEVEL% NEQ 0 echo [ERROR] OpenCharts failed >> "%LOG%"

echo [3/6] Maxar WeatherDesk...
echo [3/6] Maxar WeatherDesk... >> "%LOG%"
%PYTHON% "%BASE%\Ingest\ingest_maxar.py" >> "%LOG%" 2>&1
if %ERRORLEVEL% NEQ 0 echo [ERROR] Maxar failed >> "%LOG%"

echo [4/6] Static (CPTEC / CPC / GFS)...
echo [4/6] Static (CPTEC / CPC / GFS)... >> "%LOG%"
%PYTHON% "%BASE%\Ingest\ingest_static.py" >> "%LOG%" 2>&1
if %ERRORLEVEL% NEQ 0 echo [ERROR] Static failed >> "%LOG%"

echo [5/6] ERA5 Reanalysis...
echo [5/6] ERA5 Reanalysis... >> "%LOG%"
%PYTHON% "%BASE%\Ingest\ingest_era5.py" >> "%LOG%" 2>&1
if %ERRORLEVEL% NEQ 0 echo [ERROR] ERA5 failed >> "%LOG%"

echo [6/6] GWI Day 1-15 %% of Normal Precip...
echo [6/6] GWI Day 1-15 %% of Normal Precip... >> "%LOG%"
%PYTHON% "%BASE%\Ingest\ingest_gwi_pnorm.py" >> "%LOG%" 2>&1
if %ERRORLEVEL% NEQ 0 echo [ERROR] GWI pnorm failed >> "%LOG%"

echo [Purge] Removing maps older than 2 days...
echo [Purge] Removing maps older than 2 days... >> "%LOG%"
forfiles /P "%MAPS%" /M *.png /D -2 /C "cmd /c del @path" 2>nul

echo [Git] Committing and pushing...
echo [Git] Committing and pushing... >> "%LOG%"
cd /d "%BASE%"
git add Database\weather_mg.parquet
git add Database\last_run.json
git add -A Database/maps
git diff --cached --quiet
if %ERRORLEVEL% NEQ 0 (
    git commit -m "Morning run %DATE% %TIME%" >> "%LOG%" 2>&1
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
