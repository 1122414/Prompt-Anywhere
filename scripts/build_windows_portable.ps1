# Prompt Anywhere Windows Portable Build Script

Write-Host "Building Prompt Anywhere Portable..." -ForegroundColor Green

# Check Python
python --version > $null 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "Python is not installed or not in PATH." -ForegroundColor Red
    exit 1
}

# Install dependencies
Write-Host "Installing dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt
pip install pyinstaller

# Build
Write-Host "Building with PyInstaller..." -ForegroundColor Yellow
pyinstaller `
    --name "PromptAnywhere" `
    --windowed `
    --onedir `
    --add-data "builtin_templates;builtin_templates" `
    --add-data ".env;.env" `
    --add-data "config.yaml;config.yaml" `
    app/main.py

# Create additional directories
Write-Host "Creating directories..." -ForegroundColor Yellow
New-Item -ItemType Directory -Force -Path "dist/PromptAnywhere/data" | Out-Null
New-Item -ItemType Directory -Force -Path "dist/PromptAnywhere/exports" | Out-Null
New-Item -ItemType Directory -Force -Path "dist/PromptAnywhere/backups" | Out-Null
New-Item -ItemType Directory -Force -Path "dist/PromptAnywhere/logs" | Out-Null

# Create README
@"
# Prompt Anywhere Portable

## 启动

双击 `PromptAnywhere.exe` 启动应用。

## 目录说明

- `data/` - 提示词数据
- `exports/` - 导出文件
- `backups/` - 备份文件
- `logs/` - 日志文件

## 配置

配置文件: `app_config.json` (首次启动自动创建)
"@ | Out-File -FilePath "dist/PromptAnywhere/README_START.md" -Encoding UTF8

Write-Host "Build complete!" -ForegroundColor Green
Write-Host "Output: dist/PromptAnywhere/" -ForegroundColor Cyan
