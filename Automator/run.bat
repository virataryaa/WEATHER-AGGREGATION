@echo off
setlocal

set BASE=C:\Users\virat.arya\ETG\SoftsDatabase - Documents\Database\Hardmine\Non Fundamental\Weather\AGGREGATION OF WEATHER

echo.
echo ========================================
echo  Weather Ingest  ^|  %DATE% %TIME%
echo ========================================

echo [1/5] ECMWF Open Data...
python "%BASE%\Ingest\ingest.py"
if %ERRORLEVEL% NEQ 0 echo [ERROR] ECMWF ingest failed.

echo [2/5] ECMWF OpenCharts (anomaly/seasonal)...
python "%BASE%\Ingest\ingest_opencharts.py"
if %ERRORLEVEL% NEQ 0 echo [ERROR] OpenCharts ingest failed.

echo [3/5] Maxar WeatherDesk...
python "%BASE%\Ingest\ingest_maxar.py"
if %ERRORLEVEL% NEQ 0 echo [ERROR] Maxar ingest failed.

echo [4/5] Static charts (CPTEC/CPC/GFS)...
python "%BASE%\Ingest\ingest_static.py"
if %ERRORLEVEL% NEQ 0 echo [ERROR] Static ingest failed.

echo [5/5] ERA5 Reanalysis...
python "%BASE%\Ingest\ingest_era5.py"
if %ERRORLEVEL% NEQ 0 echo [ERROR] ERA5 ingest failed.

cd /d "%BASE%"
git add Database\weather_mg.parquet
git add "Database\maps\"
git commit -m "Weather update %DATE%"
git push

echo.
echo ========================================
echo  Done.
echo ========================================
endlocal
