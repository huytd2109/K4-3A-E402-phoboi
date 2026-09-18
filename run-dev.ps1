$ErrorActionPreference = "Stop"

$root = $PSScriptRoot
$webPath = Join-Path $root "web"
$processes = @()

function Require-Command([string]$name, [string]$installHint) {
    if (-not (Get-Command $name -ErrorAction SilentlyContinue)) {
        throw "Không tìm thấy '$name'. $installHint"
    }
}

try {
    Require-Command "python" "Hãy cài Python 3.10+ và thêm vào PATH."
    Require-Command "node" "Hãy cài Node.js trước khi chạy UI."

    $packageManager = Get-Command pnpm -ErrorAction SilentlyContinue
    if (-not $packageManager) {
        $packageManager = Get-Command npm -ErrorAction SilentlyContinue
    }
    if (-not $packageManager) {
        throw "Không tìm thấy 'pnpm' hoặc 'npm'. Hãy cài Node.js trước khi chạy script."
    }
    $isPnpm = $packageManager.Name -like "pnpm*"

    if (-not (Test-Path (Join-Path $webPath "node_modules"))) {
        Write-Host "Đang cài dependencies cho web..." -ForegroundColor Yellow
        if ($isPnpm) {
            & $packageManager.Source --dir $webPath install
        }
        else {
            & $packageManager.Source --prefix $webPath install
        }
    }

    $nodePath = (Get-Command node).Source
    $viteCli = Join-Path $webPath "node_modules\vite\bin\vite.js"
    if (-not (Test-Path $viteCli)) {
        throw "Không tìm thấy Vite tại '$viteCli'. Hãy chạy npm install trong thư mục web."
    }

    $backend = Start-Process `
        -FilePath "python" `
        -ArgumentList "-m", "phoboi.api" `
        -WorkingDirectory $root `
        -PassThru
    $processes += $backend

    $frontend = Start-Process `
        -FilePath $nodePath `
        -ArgumentList $viteCli `
        -WorkingDirectory $webPath `
        -PassThru
    $processes += $frontend

    Write-Host "Backend: http://127.0.0.1:8787" -ForegroundColor Green
    Write-Host "UI:      http://localhost:8443" -ForegroundColor Green
    Write-Host "Nhấn Ctrl+C để dừng cả UI và backend." -ForegroundColor Cyan

    while ($true) {
        if ($backend.HasExited) {
            throw "Backend đã dừng với mã $($backend.ExitCode)."
        }
        if ($frontend.HasExited) {
            throw "UI đã dừng với mã $($frontend.ExitCode)."
        }
        Start-Sleep -Seconds 1
    }
}
finally {
    foreach ($process in $processes) {
        if ($process -and -not $process.HasExited) {
            Stop-Process -Id $process.Id -Force -ErrorAction SilentlyContinue
        }
    }
}