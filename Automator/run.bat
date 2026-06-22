@echo off
setlocal

set BASE=C:\Users\virat.arya\ETG\SoftsDatabase - Documents\Database\Hardmine\Non Fundamental\Weather\AGGREGATION OF WEATHER

echo.
echo ========================================
echo  MG Weather Ingest  ^|  %DATE% %TIME%
echo ========================================

python "%BASE%\Ingest\ingest.py"
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Ingest failed. Aborting git push.
    exit /b 1
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
