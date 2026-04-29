@echo off
echo Building Prompt Anywhere Portable...

python --version >nul 2>&1
if errorlevel 1 (
    echo Python is not installed or not in PATH.
    pause
    exit /b 1
)

echo Installing dependencies...
pip install -r requirements.txt
pip install pyinstaller

echo Building with PyInstaller...
pyinstaller --name "PromptAnywhere" --windowed --onedir --add-data "builtin_templates;builtin_templates" --add-data ".env;.env" --add-data "config.yaml;config.yaml" app/main.py

echo Creating directories...
if not exist "dist\PromptAnywhere\data" mkdir "dist\PromptAnywhere\data"
if not exist "dist\PromptAnywhere\exports" mkdir "dist\PromptAnywhere\exports"
if not exist "dist\PromptAnywhere\backups" mkdir "dist\PromptAnywhere\backups"
if not exist "dist\PromptAnywhere\logs" mkdir "dist\PromptAnywhere\logs"

echo Build complete!
echo Output: dist\PromptAnywhere\
pause
