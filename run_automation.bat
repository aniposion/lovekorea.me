@echo off
setlocal EnableExtensions

cd /d "%~dp0"
chcp 65001 >nul
set "PYTHONUTF8=1"
set "PYTHONIOENCODING=utf-8"

set "PYTHON_EXE=C:\Users\uesr\anaconda3\python.exe"
if not exist "%PYTHON_EXE%" set "PYTHON_EXE=python"

echo [1/12] Running trend keyword collection...
echo No external trend collector is configured; using create_post.py keyword cache.

echo [2/12] Running blog post creation...
"%PYTHON_EXE%" "%CD%\create_post.py"
if errorlevel 1 goto fail

echo [3/12] Validating cover images...
"%PYTHON_EXE%" "%CD%\tools\validate_covers.py"
if errorlevel 1 goto fail

echo [4/12] Auditing home and category first-screen quality...
"%PYTHON_EXE%" "%CD%\tools\audit_first_screen_quality.py"
if errorlevel 1 goto fail

echo [5/12] Auditing internal links...
"%PYTHON_EXE%" "%CD%\tools\audit_internal_links.py" --warnings-as-errors
if errorlevel 1 goto fail

echo [6/12] Auditing old content quality...
"%PYTHON_EXE%" "%CD%\tools\content_quality_audit.py" --top 25
if errorlevel 1 goto fail

echo [7/12] Auditing Search Console opportunities...
if exist "%CD%\gsc\latest.csv" (
  "%PYTHON_EXE%" "%CD%\tools\gsc_opportunity_audit.py" --input "%CD%\gsc\latest.csv"
  if errorlevel 1 goto fail
) else (
  echo No GSC export found at gsc\latest.csv; skipping opportunity audit.
)
if exist "%CD%\gsc\pages.csv" (
  "%PYTHON_EXE%" "%CD%\tools\gsc_opportunity_audit.py" --input "%CD%\gsc\pages.csv" --output "%CD%\docs\gsc-page-opportunity-audit.md"
  if errorlevel 1 goto fail
)

echo [8/12] Linting monetization compliance...
"%PYTHON_EXE%" "%CD%\tools\lint_monetization.py"
if errorlevel 1 goto fail

echo [9/12] Building Hugo site...
hugo --environment production --minify
if errorlevel 1 goto fail

echo [10/12] Auditing indexing policy...
"%PYTHON_EXE%" "%CD%\tools\audit_indexing_policy.py"
if errorlevel 1 goto fail

echo [11/12] Staging changes...
git add .
if errorlevel 1 goto fail

git diff --cached --quiet
if errorlevel 2 goto fail
if not errorlevel 1 goto no_changes

echo [12/12] Committing and pushing changes...
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
