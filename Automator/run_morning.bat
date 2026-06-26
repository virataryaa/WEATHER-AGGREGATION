@echo off
setlocal

set BASE=C:\Users\virat.arya\ETG\SoftsDatabase - Documents\Database\Hardmine\Non Fundamental\Weather\AGGREGATION OF WEATHER
set MAPS=%BASE%\Database\maps
set LOG=%BASE%\Automator\run_morning.log
set PYTHON=python

echo. >> "%LOG%"
echo ======================================== >> "%LOG%"
echo  MORNING RUN  ^|  %DATE%  %TIME% >> "%LOG%"
echo ======================================== >> "%LOG%"

echo [1/5] ECMWF Open Data...
echo [1/5] ECMWF Open Data... >> "%LOG%"
%PYTHON% "%BASE%\Ingest\ingest.py" >> "%LOG%" 2>&1
if %ERRORLEVEL% NEQ 0 echo [ERROR] ECMWF failed >> "%LOG%"

echo [2/5] ECMWF OpenCharts...
echo [2/5] ECMWF OpenCharts... >> "%LOG%"
%PYTHON% "%BASE%\Ingest\ingest_opencharts.py" >> "%LOG%" 2>&1
if %ERRORLEVEL% NEQ 0 echo [ERROR] OpenCharts failed >> "%LOG%"

echo [3/5] Maxar WeatherDesk...
echo [3/5] Maxar WeatherDesk... >> "%LOG%"
%PYTHON% "%BASE%\Ingest\ingest_maxar.py" >> "%LOG%" 2>&1
if %ERRORLEVEL% NEQ 0 echo [ERROR] Maxar failed >> "%LOG%"

echo [4/5] Static (CPTEC / CPC / GFS)...
echo [4/5] Static (CPTEC / CPC / GFS)... >> "%LOG%"
%PYTHON% "%BASE%\Ingest\ingest_static.py" >> "%LOG%" 2>&1
if %ERRORLEVEL% NEQ 0 echo [ERROR] Static failed >> "%LOG%"

echo [5/5] ERA5 Reanalysis...
echo [5/5] ERA5 Reanalysis... >> "%LOG%"
%PYTHON% "%BASE%\Ingest\ingest_era5.py" >> "%LOG%" 2>&1
if %ERRORLEVEL% NEQ 0 echo [ERROR] ERA5 failed >> "%LOG%"

echo [Purge] Removing maps older than 2 days...
echo [Purge] Removing maps older than 2 days... >> "%LOG%"
forfiles /P "%MAPS%" /M *.png /D -2 /C "cmd /c del @path" 2>nul

cd /d "%BASE%"
git add Database\weather_mg.parquet
git add "Database\maps\"
git commit -m "Morning run %DATE% %TIME%" >> "%LOG%" 2>&1
git push >> "%LOG%" 2>&1

echo [Done] %DATE% %TIME% >> "%LOG%"
echo.
echo Done. See log: %LOG%
endlocal
