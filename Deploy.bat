@echo off
setlocal

:: Today YYYY-MM-DD
for /f %%i in ('powershell -NoProfile -Command "Get-Date -Format yyyy-MM-dd"') do set TODAY=%%i

echo ===============================
echo ✅ Build complete. Deploying...
echo ===============================
git add .
git commit -m "%TODAY% deploy"
git push origin main

echo ===============================
echo 🚀 Deployed successfully!
echo ===============================

endlocal
pause
