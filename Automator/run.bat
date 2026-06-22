@echo off
setlocal

set BASE=C:\Users\virat.arya\ETG\SoftsDatabase - Documents\Database\Hardmine\Non Fundamental\Weather\AGGREGATION OF WEATHER

echo.
echo ========================================
echo  Weather Ingest  ^|  %DATE% %TIME%
echo ========================================

echo [1/2] ECMWF Open Data...
python "%BASE%\Ingest\ingest.py"
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] ECMWF ingest failed.
)

echo [2/2] Maxar WeatherDesk...
python "%BASE%\Ingest\ingest_maxar.py"
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Maxar ingest failed.
)

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
