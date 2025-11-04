param(
    [string]$Entry = "main_onnx.py",
    [switch]$SkipDependencyCheck,
    [switch]$NoVenv
)

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "===================================="
Write-Host "AI-Aimbot ONNX 启动器"
Write-Host "===================================="

# 选择 Python 与 Pip（优先 .venv）
$pythonExe = "python"
$pipExe = "pip"
if (-not $NoVenv) {
    $venvPython = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
    $venvPip = Join-Path $PSScriptRoot ".venv\Scripts\pip.exe"
    if (Test-Path $venvPython) { $pythonExe = $venvPython; Write-Host "[INFO] 使用虚拟环境 Python: $pythonExe" }
    if (Test-Path $venvPip) { $pipExe = $venvPip; Write-Host "[INFO] 使用虚拟环境 Pip: $pipExe" }
}

function Test-And-InstallPythonModule {
    param(
        [Parameter(Mandatory=$true)][string]$ModuleName,
        [Parameter(Mandatory=$true)][string]$PackageName,
        [Parameter(Mandatory=$true)][string]$Description
    )
    try {
        & $pythonExe -c "import $ModuleName" 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "[OK] $Description 已安装"
        } else {
            Write-Host "[INFO] 安装 $Description..."
            & $pipExe install $PackageName
            if ($LASTEXITCODE -eq 0) { Write-Host "[OK] $Description 安装成功" }
            else { Write-Host "[WARN] $Description 安装失败 (包: $PackageName)" }
        }
    } catch {
        Write-Host "[ERROR] $Description 检查异常: $($_.Exception.Message)"
        & $pipExe install $PackageName
    }
}

if (-not $SkipDependencyCheck) {
    Write-Host "[INFO] 检查Python依赖..."
    $deps = @(
        @{Module="onnxruntime"; Package="onnxruntime-gpu"; Desc="ONNX Runtime (GPU)"},
        @{Module="GPUtil";      Package="GPUtil";          Desc="GPU 监控"},
        @{Module="numpy";       Package="numpy";           Desc="数值计算库"},
        @{Module="win32api";    Package="pywin32";         Desc="Windows API"},
        @{Module="bettercam";   Package="bettercam";       Desc="高性能截图"}
    )
    foreach ($d in $deps) { Test-And-InstallPythonModule -ModuleName $d.Module -PackageName $d.Package -Description $d.Desc }
    Write-Host "[OK] 依赖检查完成"
}

$timestamp = (Get-Date -Format "yyyyMMdd-HHmmss")
$logDir = Join-Path $PSScriptRoot "logs"
$logFile = Join-Path $logDir "run-$timestamp.txt"
if (-not (Test-Path $logDir)) { New-Item -ItemType Directory -Path $logDir | Out-Null }

Write-Host "[INFO] 启动 $Entry..."
Write-Host "[INFO] 日志文件: $logFile"

$start = Get-Date
try {
    & $pythonExe $Entry 2>&1 | Tee-Object -FilePath $logFile
    $code = $LASTEXITCODE
    $dur = (Get-Date) - $start
    Write-Host "[INFO] 退出码: $code，运行用时: $([math]::Round($dur.TotalSeconds,2))秒"
    if ($code -eq 0) { Write-Host "[OK] 程序正常退出" } else { Write-Host "[WARN] 程序异常退出" }
} catch {
    Write-Host "[ERROR] 启动失败: $($_.Exception.Message)"
    Write-Host "[HINT] 请检查Python环境与依赖是否正确安装"
}

Write-Host "按任意键退出..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")