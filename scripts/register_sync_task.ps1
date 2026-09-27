# scripts/sync_data.py를 Windows 작업 스케줄러에 등록한다.
# 매주 일요일 09:00 실행 (GitHub Actions 수집은 토요일 23:30 KST).
# PC가 꺼져 있어 놓친 경우 다음에 켜졌을 때 바로 실행된다.
#
# 등록:  powershell -ExecutionPolicy Bypass -File scripts\register_sync_task.ps1
# 삭제:  Unregister-ScheduledTask -TaskName "LottoDataSync" -Confirm:$false

$ErrorActionPreference = "Stop"

$TaskName = "LottoDataSync"
$Root = Split-Path -Parent $PSScriptRoot
$Script = Join-Path $Root "scripts\sync_data.py"

$Python = (Get-Command python -ErrorAction SilentlyContinue).Source
if (-not $Python) { throw "python을 찾을 수 없습니다. PATH를 확인하세요." }
# 콘솔 창이 뜨지 않도록 pythonw를 우선 사용
$Pythonw = Join-Path (Split-Path $Python) "pythonw.exe"
if (Test-Path $Pythonw) { $Python = $Pythonw }

$Action = New-ScheduledTaskAction -Execute $Python -Argument "`"$Script`"" -WorkingDirectory $Root
$Trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Sunday -At 9:00am
$Settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -RunOnlyIfNetworkAvailable `
    -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -ExecutionTimeLimit (New-TimeSpan -Minutes 10)

Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Settings $Settings `
    -Description "로또 당첨 번호 DB를 GitHub에서 받아옴 ($Root)" -Force | Out-Null

Write-Output "등록 완료: $TaskName (매주 일요일 09:00, 실행 파일 $Python)"
