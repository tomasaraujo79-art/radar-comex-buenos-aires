$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$Action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$Root\scripts\run_daily.ps1`""
$Trigger = New-ScheduledTaskTrigger -Daily -At 8:00
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -StartWhenAvailable
Register-ScheduledTask -TaskName "Radar COMEX diario" -Action $Action -Trigger $Trigger -Settings $Settings -Description "Busca empleos COMEX entry-level cerca de Belgrano" -Force
Write-Host "Tarea registrada: Radar COMEX diario"
