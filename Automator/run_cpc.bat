@echo off
setlocal

set BASE=C:\Users\virat.arya\ETG\SoftsDatabase - Documents\Database\Hardmine\Non Fundamental\Weather\AGGREGATION OF WEATHER
set LOG=%BASE%\Automator\run_cpc.log
set PYTHON=python

echo. >> "%LOG%"
echo ======================================== >> "%LOG%"
echo  CPC REFRESH  ^|  %DATE%  %TIME% >> "%LOG%"
echo ======================================== >> "%LOG%"

echo [1/1] Static refresh (CPTEC / CPC / GFS)...
echo [1/1] Static refresh (CPTEC / CPC / GFS)... >> "%LOG%"
%PYTHON% "%BASE%\Ingest\ingest_static.py" >> "%LOG%" 2>&1
if %ERRORLEVEL% NEQ 0 echo [ERROR] Static failed >> "%LOG%"

cd /d "%BASE%"
git add "Database\maps\"
git commit -m "CPC refresh %DATE% %TIME%" >> "%LOG%" 2>&1
git push >> "%LOG%" 2>&1

echo [Done] %DATE% %TIME% >> "%LOG%"
echo.
echo Done. See log: %LOG%
endlocal
