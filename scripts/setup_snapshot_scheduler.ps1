param(
    [string]$ProjectRoot = "d:\usr\百信公司项目\pdfsc"
)

# 定义任务参数
$TaskName = "PDF智转器快照监控"
$TaskDescription = "每15分钟自动生成会话快照"
$ScriptPath = Join-Path $ProjectRoot "scripts\gen_snapshot.py"
$LogPath = Join-Path $ProjectRoot "logs\snapshot_scheduler.log"
$PythonExe = "python"

# 检查脚本是否存在
if (-not (Test-Path $ScriptPath)) {
    Write-Error "快照脚本不存在: $ScriptPath"
    exit 1
}

# 创建Task Scheduler任务
$Action = New-ScheduledTaskAction `
    -Execute $PythonExe `
    -Argument $ScriptPath `
    -WorkingDirectory $ProjectRoot

$Trigger = New-ScheduledTaskTrigger `
    -Once `
    -At (Get-Date).AddMinutes(1) `
    -RepetitionInterval (New-TimeSpan -Minutes 15) `
    -RepetitionDuration (New-TimeSpan -Days 36500)

$Settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -Compatibility Win8 `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable:$false

# 创建或更新任务
$Task = New-ScheduledTask `
    -Action $Action `
    -Trigger $Trigger `
    -Settings $Settings `
    -Description $TaskDescription

try {
    # 删除旧任务（如果存在）
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue

    # 创建新任务
    Register-ScheduledTask -TaskName $TaskName -InputObject $Task -Force
    Write-Host "✅ 定时任务已创建: $TaskName"
    Write-Host "   执行频率: 每15分钟一次"
    Write-Host "   脚本路径: $ScriptPath"
    Write-Host "   日志路径: $LogPath"
} catch {
    Write-Error "创建任务失败: $_"
    exit 1
}

# 验证任务
$VerifyTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($VerifyTask) {
    Write-Host ""
    Write-Host "✅ 任务验证成功"
    Write-Host "任务详情:"
    $VerifyTask | Format-List TaskName, Description, State
} else {
    Write-Error "任务验证失败"
    exit 1
}
