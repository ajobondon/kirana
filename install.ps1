# 🦊 KIRANA CLIENT AUTO-INSTALLER FOR WINDOWS
# ==========================================
# Version: 1.0.0 (Windows PowerShell Edition)
# Target: Windows (PowerShell 5.1 / PowerShell Core 6+)

$installDir = "$HOME\kirana"
$scriptDir = $PSScriptRoot
if ([string]::IsNullOrEmpty($scriptDir)) {
    $scriptDir = Get-Location
}

function print-banner {
    Clear-Host
    Write-Host "    🦊 KIRANA CLIENT INSTALLER" -ForegroundColor Cyan
    Write-Host "    ==========================" -ForegroundColor Cyan
    Write-Host "    Server-Client Architecture (v7.1.1 (PIXEL))" -ForegroundColor Cyan
    Write-Host ""
}

function step($msg) {
    Write-Host "➡️  $msg" -ForegroundColor Cyan
}

function success($msg) {
    Write-Host "✅ $msg" -ForegroundColor Green
}

function fail($msg) {
    Write-Host ""
    Write-Host "❌ FATAL ERROR: $msg" -ForegroundColor Red
    Exit 1
}

function check-os {
    step "Mengecek Kompatibilitas OS..."
    if ($env:OS -notlike "*Windows*") {
        fail "OS tidak didukung oleh installer ini. Harap gunakan install.py di Linux/macOS."
    }
    success "OS Terdeteksi & Didukung: Windows"
}

function check-python {
    step "Mengecek Versi Python (Min 3.11)..."
    try {
        $pyVer = & python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" -ErrorAction Stop
        $pyVer = $pyVer.Trim()
        $parts = $pyVer.Split('.')
        $major = [int]$parts[0]
        $minor = [int]$parts[1]
        
        if ($major -lt 3 -or ($major -eq 3 -and $minor -lt 11)) {
            fail "Versi Python Anda $pyVer. Kirana butuh Python 3.11+"
        }
        success "Python $pyVer OK."
    } catch {
        fail "Python tidak ditemukan di PATH. Silakan instal Python 3.11+ terlebih dahulu."
    }
}

function install-repo {
    $isLocalRun = (Test-Path "$scriptDir\kirana.py") -and (Test-Path "$scriptDir\requirements.txt")
    
    if ($scriptDir -eq $installDir) {
        success "Source code sudah berada di folder tujuan ~/kirana. Melewati fase penyalinan."
        return
    }

    if ($isLocalRun) {
        step "Mendeteksi instalasi lokal. Menyalin berkas dari $scriptDir ke $installDir..."
    } else {
        step "Mengunduh Source Code dari Git ke $installDir..."
    }

    if (Test-Path $installDir) {
        Write-Host "⚠️  Folder $installDir sudah ada." -ForegroundColor Yellow
        $choice = Read-Host "   Timpa (hapus & install ulang)? [y/N]"
        if ($choice -eq 'y' -or $choice -eq 'Y') {
            Remove-Item -Recurse -Force $installDir -ErrorAction SilentlyContinue
            New-Item -ItemType Directory -Path $installDir -Force | Out-Null
        } else {
            Write-Host "   Melanjutkan update di folder existing..."
            if ($isLocalRun) {
                Get-ChildItem -Path $scriptDir | Where-Object { $_.Name -notin @('env', 'venv', '.git', '__pycache__', '.DS_Store', 'install.ps1') } | ForEach-Object {
                    Copy-Item -Path $_.FullName -Destination $installDir -Recurse -Force
                }
            } else {
                Push-Location $installDir
                git pull
                Pop-Location
            }
            return
        }
    }

    try {
        if ($isLocalRun) {
            if (-not (Test-Path $installDir)) {
                New-Item -ItemType Directory -Path $installDir -Force | Out-Null
            }
            Get-ChildItem -Path $scriptDir | Where-Object { $_.Name -notin @('env', 'venv', '.git', '__pycache__', '.DS_Store') } | ForEach-Object {
                Copy-Item -Path $_.FullName -Destination $installDir -Recurse -Force
            }
            success "Penyalinan berkas lokal berhasil."
        } else {
            git clone https://github.com/ajobondon/kirana.git $installDir
            success "Repository berhasil di-clone."
        }
    } catch {
        fail "Gagal menginstall source code: $_"
    }
}

function setup-venv {
    step "Membuat Virtual Environment (env)..."
    $venvDir = "$installDir\env"
    try {
        & python -m venv $venvDir
        success "Venv created."
        
        step "Menginstall Dependencies (pip)..."
        $pipPath = "$venvDir\Scripts\pip.exe"
        $pythonPath = "$venvDir\Scripts\python.exe"
        
        # Upgrade pip
        & $pythonPath -m pip install --upgrade pip --quiet
        
        # Install requirements.txt
        & $pipPath install -r "$installDir\requirements.txt"
        success "Dependencies installed."
    } catch {
        fail "Gagal setup environment: $_"
    }
}

function configure-env {
    step "Konfigurasi Identitas Client..."
    Write-Host ""
    Write-Host "⚠️  PERHATIAN: Anda memerlukan API KEY & CLIENT ID." -ForegroundColor Yellow
    Write-Host "   Jika belum punya, silakan request ke: kirana@palawamaya.com" -ForegroundColor Yellow
    Write-Host ""
    
    $clientId = (Read-Host "👉 Masukkan CLIENT_ID").Trim()
    $apiKey = (Read-Host "👉 Masukkan X_API_KEY").Trim()
    
    if ([string]::IsNullOrEmpty($clientId) -or [string]::IsNullOrEmpty($apiKey)) {
        fail "Setup dibatalkan. Identitas Client wajib diisi."
    }

    $envPath = "$installDir\.env"
    $workspaceDir = "$installDir\workspace"
    
    $envContent = @"
# Target Server
KIRANA_SERVER_URL="https://alaya.palawamaya.com"
# Client Timeout (in seconds) - untuk proses yang lama di sisi server
KIRANA_TIMEOUT="600"

# Client Identity
CLIENT_ID="$clientId"
X_API_KEY="$apiKey"

# Local Workspace
WORKSPACE_DIR="$workspaceDir"
"@

    try {
        [System.IO.File]::WriteAllText($envPath, $envContent)
        success "File .env berhasil dibuat."
    } catch {
        fail "Gagal menulis .env: $_"
    }
}

function inject-shell {
    # Auto-configure ExecutionPolicy to allow running user profiles
    try {
        Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser -Force -ErrorAction SilentlyContinue
    } catch {}

    if (-not $PROFILE) {
        $profileDir = "$HOME\Documents\WindowsPowerShell"
        $profilePath = "$profileDir\Microsoft.PowerShell_profile.ps1"
    } else {
        $profilePath = $PROFILE
    }
    
    $profileDir = Split-Path -Parent $profilePath
    if (-not (Test-Path $profileDir)) {
        New-Item -ItemType Directory -Path $profileDir -Force | Out-Null
    }
    if (-not (Test-Path $profilePath)) {
        New-Item -ItemType File -Path $profilePath -Force | Out-Null
    }
    
    $profileContent = Get-Content -Path $profilePath -Raw -ErrorAction SilentlyContinue
    if ($profileContent -and $profileContent -like "*# 🦊 KIRANA*") {
        success "Konfigurasi profile sudah ada. Skip."
    } else {
        step "Integrasi Terminal (PowerShell Profile - $profilePath)..."
        
        $kiranaShellScript = @"

# =========
# 🦊 KIRANA
# =========

# 1. Define Global Variables
`$env:KIRANA_HOME = "$installDir"
`$env:KIRANA_PYTHON = "`$env:KIRANA_HOME\env\Scripts\python.exe"
`$env:KIRANA_SCRIPT = "`$env:KIRANA_HOME\kirana.py"
`$env:PYTHONIOENCODING = "utf-8"

# 2. Main Function (Chat & One-Shot)
# Usage: 'kirana' (chat loop) or 'kirana <cmd>' (one-shot)
function kirana {
    `$env:PYTHONWARNINGS = "ignore"
    `$env:PYTHONIOENCODING = "utf-8"
    if (`$args.Count -eq 0) {
        # Interactive Chat Mode
        & `$env:KIRANA_PYTHON `$env:KIRANA_SCRIPT
    } else {
        # Explicit One-Shot Mode
        `$query = `$args -join " "
        & `$env:KIRANA_PYTHON `$env:KIRANA_SCRIPT `$query
    }
}

# Helper Aliases/Functions
function tanya {
    kirana @args
}

# 3. Magic Fallback (AI Shell)
`$ExecutionContext.SessionState.InvokeCommand.CommandNotFoundAction = {
    param(`$CommandName, `$CommandLookupEventArgs)
    
    # Safety Check: Do not process empty commands
    if ([string]::IsNullOrEmpty(`$CommandName)) { return }
    
    # Safety Check: Do not process relative/absolute paths or drive letters
    if (`$CommandName -like ".\*" -or `$CommandName -like "/*" -or `$CommandName -like "\*" -or `$CommandName -match "^[A-Za-z]:\\") {
        return
    }

    # Throw to Kirana
    `$CommandLookupEventArgs.CommandScriptBlock = {
        `$fullQuery = `$CommandName
        if (`$args) {
            `$fullQuery += " " + (`$args -join " ")
        }
        kirana `$fullQuery
    }.GetNewClosure()
    `$CommandLookupEventArgs.StopSearch = `$true
}
"@

        Add-Content -Path $profilePath -Value $kiranaShellScript
        success "Magic Shell ditambahkan ke PowerShell Profile."
    }
}

function final-test {
    step "Finalizing & Testing..."
    Write-Host "Fox is waking up..." -ForegroundColor Cyan
    
    $pythonBin = "$installDir\env\Scripts\python.exe"
    $script = "$installDir\kirana.py"
    
    $env:PYTHONIOENCODING = "utf-8"
    try {
        & $pythonBin $script help
    } catch {
        Write-Host "⚠️  Test run warning: $_" -ForegroundColor Yellow
    }

    Write-Host ""
    Write-Host "==================================================" -ForegroundColor Green
    Write-Host "🎉 INSTALASI SUKSES! 🎉" -ForegroundColor Green
    Write-Host "==================================================" -ForegroundColor Green
    Write-Host "Agar Kirana aktif di terminal ini, muat ulang profil:"
    Write-Host ""
    Write-Host "    . `$PROFILE" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Atau tutup dan buka kembali terminal Anda."
    Write-Host "Gunakan command 'kirana' or 'tanya' untuk memulai."
    Write-Host "==================================================" -ForegroundColor Green
    Write-Host ""
}

function main {
    print-banner
    check-os
    check-python
    install-repo
    configure-env
    setup-venv
    inject-shell
    final-test
}

main
