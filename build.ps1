param(
    [string]$Python = "python"
)

$ErrorActionPreference = "Stop"

Write-Host "[1/3] 安装依赖..."
& $Python -m pip install -r requirements.txt

Write-Host "[2/3] 清理旧产物..."
if (Test-Path build) { Remove-Item -Recurse -Force build }
if (Test-Path dist) { Remove-Item -Recurse -Force dist }

Write-Host "[3/3] 打包 EXE..."
& $Python -m PyInstaller --noconfirm --clean --onefile --windowed --name WowRaidSetupTool src/main.py

Write-Host "打包完成。输出目录: dist/WowRaidSetupTool.exe"
