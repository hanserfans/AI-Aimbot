# AI-Aimbot PowerShell 启动脚本
# 支持虚拟环境激活和依赖检查

param(
    [switch]$SkipDependencyCheck
)

# 设置控制台编码
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host ""
Write-Host "====================================" -ForegroundColor Cyan
Write-Host "      🎯 AI-Aimbot 启动器" -ForegroundColor Yellow
Write-Host "====================================" -ForegroundColor Cyan
Write-Host ""

# 检查并激活虚拟环境
Write-Host "[INFO] 检查虚拟环境..." -ForegroundColor Blue
if (Test-Path ".venv\Scripts\Activate.ps1") {
    Write-Host "[✓] 发现虚拟环境，正在激活..." -ForegroundColor Green
    try {
        & ".venv\Scripts\Activate.ps1"
        Write-Host "[✓] 虚拟环境已激活" -ForegroundColor Green
    }
    catch {
        Write-Host "[!] 虚拟环境激活失败，使用系统Python" -ForegroundColor Yellow
    }
}
elseif (Test-Path ".venv\Scripts\activate.bat") {
    Write-Host "[✓] 发现虚拟环境 (批处理版本)，正在激活..." -ForegroundColor Green
    cmd /c ".venv\Scripts\activate.bat && echo Virtual environment activated"
}
else {
    Write-Host "[!] 未找到虚拟环境，使用系统Python" -ForegroundColor Yellow
}

Write-Host ""

# 检查Python依赖
if (-not $SkipDependencyCheck) {
    Write-Host "[INFO] 检查Python依赖..." -ForegroundColor Blue
    
    $dependencies = @(
        @{Name="tkinter"; Package="tk"; Description="GUI界面库"},
        @{Name="serial"; Package="pyserial"; Description="串口通信库"},
        @{Name="cv2"; Package="opencv-python"; Description="计算机视觉库"},
        @{Name="torch"; Package="torch torchvision"; Description="深度学习框架"}
    )
    
    $missingDeps = @()
    
    foreach ($dep in $dependencies) {
        try {
            $result = python -c "import $($dep.Name)" 2>&1
            if ($LASTEXITCODE -eq 0) {
                Write-Host "[✓] $($dep.Description) 已安装" -ForegroundColor Green
            }
            else {
                Write-Host "[!] $($dep.Description) 未安装" -ForegroundColor Yellow
                $missingDeps += $dep
            }
        }
        catch {
            Write-Host "[!] $($dep.Description) 检查失败" -ForegroundColor Red
            $missingDeps += $dep
        }
    }
    
    # 安装缺失的依赖
    if ($missingDeps.Count -gt 0) {
        Write-Host ""
        Write-Host "[INFO] 安装缺失的依赖..." -ForegroundColor Blue
        
        foreach ($dep in $missingDeps) {
            Write-Host "[INFO] 安装 $($dep.Description)..." -ForegroundColor Blue
            try {
                pip install $dep.Package
                if ($LASTEXITCODE -eq 0) {
                    Write-Host "[✓] $($dep.Description) 安装成功" -ForegroundColor Green
                }
                else {
                    Write-Host "[!] $($dep.Description) 安装失败" -ForegroundColor Red
                }
            }
            catch {
                Write-Host "[!] $($dep.Description) 安装异常: $($_.Exception.Message)" -ForegroundColor Red
            }
        }
    }
    
    Write-Host "[✓] 依赖检查完成" -ForegroundColor Green
}

Write-Host ""
Write-Host "[INFO] 启动 AI-Aimbot GUI..." -ForegroundColor Blue
Write-Host "[INFO] 请在GUI界面中进行配置和控制" -ForegroundColor Cyan
Write-Host ""

# 启动GUI应用
try {
    python aimbot_gui.py
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "[✓] AI-Aimbot 正常退出" -ForegroundColor Green
    }
    else {
        Write-Host ""
        Write-Host "[!] AI-Aimbot 异常退出 (退出码: $LASTEXITCODE)" -ForegroundColor Yellow
    }
}
catch {
    Write-Host ""
    Write-Host "[ERROR] 启动失败: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "[INFO] 请检查Python环境和依赖是否正确安装" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "按任意键退出..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")