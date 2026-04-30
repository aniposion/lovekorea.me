@echo off
setlocal EnableExtensions

cd /d "%~dp0"
chcp 65001 >nul
set "PYTHONUTF8=1"
set "PYTHONIOENCODING=utf-8"

set "PYTHON_EXE=C:\Users\uesr\anaconda3\python.exe"
if not exist "%PYTHON_EXE%" set "PYTHON_EXE=python"

echo [1/7] Running trend keyword collection...
echo No external trend collector is configured; using create_post.py keyword cache.

echo [2/7] Running blog post creation...
"%PYTHON_EXE%" "%CD%\create_post.py"
if errorlevel 1 goto fail

echo [3/7] Validating cover images...
"%PYTHON_EXE%" "%CD%\tools\validate_covers.py"
if errorlevel 1 goto fail

echo [4/7] Linting monetization compliance...
"%PYTHON_EXE%" "%CD%\tools\lint_monetization.py"
if errorlevel 1 goto fail

echo [5/7] Building Hugo site...
hugo --minify
if errorlevel 1 goto fail

echo [6/7] Staging changes...
git add .
if errorlevel 1 goto fail

git diff --cached --quiet
if errorlevel 2 goto fail
if not errorlevel 1 goto no_changes

echo [7/7] Committing and pushing changes...
git commit -m "Automated blog post update: %date% %time%"
if errorlevel 1 goto fail

git push origin main
if errorlevel 1 goto fail

echo Automation complete.
exit /b 0

:no_changes
echo No changes to commit.
exit /b 0

:fail
echo Automation failed. Review the output above before deploying.
exit /b 1
