# 紧急终止AI瞄准系统脚本
# 当程序无法正常退出时使用

Write-Host "🚨 紧急终止AI瞄准系统..." -ForegroundColor Red
Write-Host "=" * 50

# 1. 终止所有Python进程（包含main_onnx）
Write-Host "🔍 查找相关Python进程..." -ForegroundColor Yellow
$pythonProcesses = Get-Process -Name "python*" -ErrorAction SilentlyContinue | Where-Object {
    $_.ProcessName -like "*python*" -or 
    $_.MainWindowTitle -like "*main_onnx*" -or
    $_.MainWindowTitle -like "*AI-Aimbot*"
}

if ($pythonProcesses) {
    Write-Host "发现 $($pythonProcesses.Count) 个相关进程:" -ForegroundColor Yellow
    foreach ($process in $pythonProcesses) {
        Write-Host "  - PID: $($process.Id), 名称: $($process.ProcessName), 窗口: $($process.MainWindowTitle)" -ForegroundColor Cyan
        try {
            Stop-Process -Id $process.Id -Force
            Write-Host "  ✅ 已终止 PID: $($process.Id)" -ForegroundColor Green
        } catch {
            Write-Host "  ❌ 终止失败 PID: $($process.Id) - $($_.Exception.Message)" -ForegroundColor Red
        }
    }
} else {
    Write-Host "未发现相关Python进程" -ForegroundColor Green
}

# 2. 强制关闭OpenCV窗口
Write-Host "`n🖼️ 强制关闭OpenCV窗口..." -ForegroundColor Yellow
$cvWindows = Get-Process -Name "*cv*" -ErrorAction SilentlyContinue
if ($cvWindows) {
    foreach ($window in $cvWindows) {
        try {
            Stop-Process -Id $window.Id -Force
            Write-Host "  ✅ 已关闭OpenCV窗口 PID: $($window.Id)" -ForegroundColor Green
        } catch {
            Write-Host "  ❌ 关闭失败 PID: $($window.Id)" -ForegroundColor Red
        }
    }
}

# 3. 清理可能的僵尸进程
Write-Host "`n🧹 清理僵尸进程..." -ForegroundColor Yellow
$zombieProcesses = Get-Process | Where-Object { 
    $_.ProcessName -like "*onnx*" -or 
    $_.ProcessName -like "*aimbot*" -or
    $_.MainWindowTitle -like "*Live Feed*"
}

if ($zombieProcesses) {
    foreach ($zombie in $zombieProcesses) {
        try {
            Stop-Process -Id $zombie.Id -Force
            Write-Host "  ✅ 已清理僵尸进程 PID: $($zombie.Id)" -ForegroundColor Green
        } catch {
            Write-Host "  ❌ 清理失败 PID: $($zombie.Id)" -ForegroundColor Red
        }
    }
}

# 4. 检查端口占用（如果有网络服务）
Write-Host "`n🌐 检查端口占用..." -ForegroundColor Yellow
$commonPorts = @(8080, 5000, 3000, 8000)
foreach ($port in $commonPorts) {
    $connection = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
    if ($connection) {
        $processId = $connection.OwningProcess
        Write-Host "  发现端口 $port 被进程 $processId 占用" -ForegroundColor Yellow
        try {
            Stop-Process -Id $processId -Force
            Write-Host "  ✅ 已终止占用端口 $port 的进程" -ForegroundColor Green
        } catch {
            Write-Host "  ❌ 终止失败" -ForegroundColor Red
        }
    }
}

Write-Host "`n" + "=" * 50
Write-Host "🎯 紧急终止完成！" -ForegroundColor Green
Write-Host "如果问题仍然存在，请重启计算机。" -ForegroundColor Yellow
Write-Host "=" * 50

# 等待用户确认
Write-Host "`n按任意键退出..." -ForegroundColor Cyan
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")