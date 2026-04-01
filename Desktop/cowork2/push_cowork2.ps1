param(
    [Parameter(Position = 0)]
    [string]$Message = "Update cowork2"
)

$ErrorActionPreference = "Stop"

function Run-Git {
    param(
        [Parameter(ValueFromRemainingArguments = $true)]
        [string[]]$Args
    )

    & git @Args
    if ($LASTEXITCODE -ne 0) {
        throw "git $($Args -join ' ') failed"
    }
}

$projectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $projectDir

$repoRoot = (git rev-parse --show-toplevel).Trim()
if (-not $repoRoot) {
    throw "Git repo root not found."
}

$prefix = (git rev-parse --show-prefix).Trim()
$branch = (git branch --show-current).Trim()
if (-not $branch) {
    throw "Current branch not found."
}

$backupDir = Join-Path $env:TEMP "cowork2_push_backup"
$configDir = Join-Path $projectDir "config"
$configFiles = @(
    "auto_export.json",
    "experts.json",
    "insights.json",
    "insights.txt"
)

if (Test-Path $backupDir) {
    Remove-Item -LiteralPath $backupDir -Force -Recurse
}
New-Item -ItemType Directory -Path $backupDir | Out-Null

$stashCreated = $false

try {
    Write-Host "==> Stage cowork2 files"
    Run-Git -C $repoRoot add -- $prefix

    & git -C $repoRoot diff --cached --quiet -- $prefix
    $hasStagedChanges = ($LASTEXITCODE -ne 0)

    if ($hasStagedChanges) {
        Write-Host "==> Commit: $Message"
        Run-Git -C $repoRoot commit -m $Message
    } else {
        Write-Host "==> No new cowork2 changes to commit"
    }

    foreach ($name in $configFiles) {
        $src = Join-Path $configDir $name
        if (Test-Path $src) {
            Move-Item -LiteralPath $src -Destination (Join-Path $backupDir $name) -Force
        }
    }

    Write-Host "==> Stash local working tree"
    $stashOutput = git -C $repoRoot stash push --include-untracked -m "cowork2-auto-push"
    if ($LASTEXITCODE -ne 0) {
        throw "git stash push --include-untracked failed"
    }
    if ($stashOutput -notmatch "No local changes to save") {
        $stashCreated = $true
    }

    Write-Host "==> Pull --rebase origin/$branch"
    Run-Git -C $repoRoot pull --rebase origin $branch

    Write-Host "==> Push origin/$branch"
    Run-Git -C $repoRoot push origin $branch
}
finally {
    foreach ($name in $configFiles) {
        $backup = Join-Path $backupDir $name
        $dst = Join-Path $configDir $name
        if (Test-Path $backup) {
            Move-Item -LiteralPath $backup -Destination $dst -Force
        }
    }

    if (Test-Path $backupDir) {
        Remove-Item -LiteralPath $backupDir -Force -Recurse
    }

    if ($stashCreated) {
        Write-Host "==> Restore stashed working tree"
        & git -C $repoRoot stash pop | Out-Host
    }
}

Write-Host "==> Done"
