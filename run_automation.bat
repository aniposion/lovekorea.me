
@echo OFF

echo [1/4] Running trend keyword collection...
echo nothing

echo [2/4] Running blog post creation...
C:\Users\uesr\anaconda3\python.exe C:\Users\uesr\myblog\create_post.py

REM --- Git Automation ---
REM The following commands require the dev folder to be a Git repository
REM and connected to a remote on GitHub.

echo [3/4] Committing changes to Git...
cd C:\Users\uesr\myblog
git add .
git commit -m "Automated blog post update: %date%"

echo [4/4] Pushing changes to GitHub...
git push origin main 

echo Automation complete.
pause
