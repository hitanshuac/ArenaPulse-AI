# watch_ci.ps1
# Runs in the background, polls GitHub Actions every 3 minutes, and syncs errors on failure.

$CacheFile = "data/.last_failed_run"
$LogFetcher = "python src/capabilities/ci_log_fetcher.py"
$PollIntervalSeconds = 180

Write-Host "Starting Zero-Touch CI/CD Watcher..."
Write-Host "Polling GitHub every $PollIntervalSeconds seconds. Keep this window minimized."

function Show-Notification {
    Add-Type -AssemblyName System.Windows.Forms
    $balloon = New-Object System.Windows.Forms.NotifyIcon
    $balloon.Icon = [System.Drawing.SystemIcons]::Error
    $balloon.BalloonTipIcon = "Error"
    $balloon.BalloonTipTitle = "CI/CD Pipeline Failed"
    $balloon.BalloonTipText = "Remote logs automatically synced to error_logs.json. Agent is ready."
    $balloon.Visible = $true
    $balloon.ShowBalloonTip(10000)
    Start-Sleep -Seconds 5
    $balloon.Dispose()
}

if (!(Test-Path "data")) {
    New-Item -ItemType Directory -Force -Path "data" | Out-Null
}

while ($true) {
    try {
        $runOutput = gh run list --status failure --limit 1 --json databaseId 2>$null
        if (![string]::IsNullOrWhiteSpace($runOutput)) {
            $runJson = $runOutput | ConvertFrom-Json
            if ($runJson -and $runJson.Count -gt 0) {
                $latestRunId = $runJson[0].databaseId
                $lastRunId = ""
                if (Test-Path $CacheFile) {
                    $lastRunId = Get-Content $CacheFile
                }

                if ([string]$latestRunId -ne [string]$lastRunId) {
                    Write-Host "New pipeline failure detected (Run ID: $latestRunId). Syncing logs locally..."
                    Invoke-Expression $LogFetcher
                    Out-File -FilePath $CacheFile -InputObject $latestRunId -Force
                    Show-Notification
                }
            }
        }
    } catch {
        Write-Host "Warning: Error polling GitHub API. Retrying next cycle..."
    }

    Start-Sleep -Seconds $PollIntervalSeconds
}
