#!/usr/bin/env python3
"""
🦊 KIRANA CLIENT AUTO-INSTALLER
================================
Version: 1.0.0 (Semantic Versioning Initiated)
Target: Linux (Debian/Ubuntu/RHEL/Fedora)
"""

import os
import sys
import subprocess
import shutil
import platform
import getpass
import time

# --- KONFIGURASI WARNA (ANSI) ---
class C:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

# --- KONFIGURASI INSTALLER ---
REPO_URL = "https://github.com/ajobondon/kirana.git"
INSTALL_DIR = os.path.expanduser("~/kirana")
VENV_DIR = os.path.join(INSTALL_DIR, "env")
ENV_FILE = os.path.join(INSTALL_DIR, ".env")
BASHRC_FILE = os.path.expanduser("~/.bashrc")
MIN_PYTHON = (3, 11)

def print_banner():
    os.system('clear')
    print(f"{C.CYAN}")
    print(r"""
    🦊 KIRANA CLIENT INSTALLER
    ==========================
    Server-Client Architecture (v5.0)
    """)
    print(f"{C.ENDC}")

def step(msg):
    print(f"{C.BLUE}➡️  {msg}{C.ENDC}")

def success(msg):
    print(f"{C.GREEN}✅ {msg}{C.ENDC}")

def fail(msg):
    print(f"\n{C.FAIL}❌ FATAL ERROR: {msg}{C.ENDC}")
    sys.exit(1)

def check_os():
    step("Mengecek Kompatibilitas OS...")
    system = platform.system().lower()
    if system != "linux":
        fail("Installer ini hanya untuk LINUX.")
    
    try:
        with open("/etc/os-release") as f:
            data = f.read().lower()
            supported = ["debian", "ubuntu", "pop", "fedora", "rhel", "centos", "kali", "linuxmint"]
            if not any(distro in data for distro in supported):
                fail("Distro tidak didukung secara resmi. (Hanya Debian/RedHat based).")
    except Exception:
        fail("Tidak bisa membaca /etc/os-release.")
    success("OS Terdeteksi & Didukung.")

def check_python():
    step(f"Mengecek Versi Python (Min {MIN_PYTHON[0]}.{MIN_PYTHON[1]})...")
    ver = sys.version_info
    if ver < MIN_PYTHON:
        fail(f"Versi Python Anda {ver.major}.{ver.minor}. Kirana butuh Python 3.11+")
    success(f"Python {ver.major}.{ver.minor} OK.")

def install_repo():
    step(f"Mengunduh Source Code ke {INSTALL_DIR}...")
    
    if os.path.exists(INSTALL_DIR):
        print(f"{C.WARNING}⚠️  Folder {INSTALL_DIR} sudah ada.{C.ENDC}")
        choice = input("   Timpa (hapus & clone ulang)? [y/N]: ").lower()
        if choice == 'y':
            shutil.rmtree(INSTALL_DIR)
        else:
            print("   Melanjutkan update di folder existing...")
            subprocess.run(["git", "pull"], cwd=INSTALL_DIR)
            return

    try:
        subprocess.run(["git", "clone", REPO_URL, INSTALL_DIR], check=True)
        success("Repository berhasil di-clone.")
    except subprocess.CalledProcessError:
        fail("Gagal clone repository. Cek koneksi internet.")

def setup_venv():
    step("Membuat Virtual Environment (env)...")
    try:
        subprocess.run([sys.executable, "-m", "venv", VENV_DIR], check=True)
        success("Venv created.")
        
        step("Menginstall Dependencies (pip)...")
        pip_cmd = os.path.join(VENV_DIR, "bin", "pip")
        subprocess.run([pip_cmd, "install", "--upgrade", "pip"], check=True, stdout=subprocess.DEVNULL)
        subprocess.run([pip_cmd, "install", "-r", "requirements.txt"], cwd=INSTALL_DIR, check=True)
        success("Dependencies installed.")
    except subprocess.CalledProcessError as e:
        fail(f"Gagal setup environment: {e}")

def configure_env():
    step("Konfigurasi Identitas Client...")
    print(f"\n{C.WARNING}⚠️  PERHATIAN:{C.ENDC} Anda memerlukan API KEY & CLIENT ID.")
    print("   Jika belum punya, silakan request ke: kirana@palawamaya.com\n")
    
    client_id = input(f"{C.BOLD}👉 Masukkan CLIENT_ID: {C.ENDC}").strip()
    api_key = input(f"{C.BOLD}👉 Masukkan X_API_KEY: {C.ENDC}").strip()

    if not client_id or not api_key:
        fail("Setup dibatalkan. Identitas Client wajib diisi.")

    env_content = f"""# Target Server
KIRANA_SERVER_URL="https://alaya.palawamaya.com"

# Client Identity
# Request Key from: kirana@palawamaya.com
CLIENT_ID="{client_id}"

# --- API KEY ---
# Request Key from: kirana@palawamaya.com
X_API_KEY="{api_key}"

# Local Workspace
WORKSPACE_DIR="{os.path.join(INSTALL_DIR, 'workspace')}"
"""
    try:
        with open(ENV_FILE, "w") as f:
            f.write(env_content)
        success("File .env berhasil dibuat.")
    except Exception as e:
        fail(f"Gagal menulis .env: {e}")

def inject_bashrc():
    step("Integrasi Terminal (Magic Shell)...")
    
    # Cek apakah sudah pernah diinstall
    try:
        with open(BASHRC_FILE, "r") as f:
            if "# 🦊 KIRANA" in f.read():
                success("Konfigurasi .bashrc sudah ada. Skip.")
                return
    except: pass

    kirana_bash_script = f"""
# =========
# 🦊 KIRANA
# =========

# 1. Define Global Variables
export KIRANA_HOME="{INSTALL_DIR}"
export KIRANA_PYTHON="$KIRANA_HOME/env/bin/python"
export KIRANA_SCRIPT="$KIRANA_HOME/kirana.py"

# 2. Main Function (Chat & One-Shot)
# Usage: 'kirana' (chat loop) or 'kirana <cmd>' (one-shot)
kirana() {{
    if [ $# -eq 0 ]; then
        # Interactive Chat Mode
        PYTHONWARNINGS="ignore" $KIRANA_PYTHON $KIRANA_SCRIPT
    else
        # Explicit One-Shot Mode
        PYTHONWARNINGS="ignore" $KIRANA_PYTHON $KIRANA_SCRIPT "$*"
    fi
}}

# Helper Aliases
alias help="kirana help"
alias tanya="kirana"

# 3. Magic Fallback (AI Shell)
# Catches command errors/typos and asks Kirana for help.
command_not_found_handle() {{
    local cmd="$*"
    
    # Safety Check: Do not process empty commands
    if [ -z "$cmd" ]; then return 127; fi
    
    # Safety Check: Do not process relative/absolute paths (let standard errors flow)
    if [[ "$cmd" == ./* ]] || [[ "$cmd" == /* ]]; then
        printf "bash: %s: No such file or directory\\n" "$cmd"
        return 127
    fi

    # Throw to Kirana (Silent Mode)
    PYTHONWARNINGS="ignore" $KIRANA_PYTHON $KIRANA_SCRIPT "$cmd"
    
    return 0
}}
"""
    try:
        with open(BASHRC_FILE, "a") as f:
            f.write(kirana_bash_script)
        success("Magic Shell ditambahkan ke .bashrc")
    except Exception as e:
        print(f"{C.WARNING}Gagal update .bashrc: {e}. Anda harus setup manual.{C.ENDC}")

def final_test():
    step("Finalizing & Testing...")
    print(f"{C.CYAN}Fox is waking up...{C.ENDC}")
    
    # Kita coba jalankan manual pake full path karena .bashrc belum di-source di sesi ini
    python_bin = os.path.join(VENV_DIR, "bin", "python")
    script = os.path.join(INSTALL_DIR, "kirana.py")
    
    try:
        # Jalankan 'kirana help'
        subprocess.run([python_bin, script, "help"], check=True)
    except Exception as e:
        print(f"{C.WARNING}Test run warning: {e}{C.ENDC}")

    print("\n" + "="*50)
    print(f"{C.GREEN}{C.BOLD}🎉 INSTALASI SUKSES! 🎉{C.ENDC}")
    print("="*50)
    print(f"Agar Kirana aktif di terminal ini, jalankan perintah:")
    print(f"\n    {C.CYAN}source ~/.bashrc{C.ENDC}\n")
    print("Atau tutup dan buka kembali terminal Anda.")
    print("Gunakan command 'kirana' atau 'tanya' untuk memulai.")
    print("="*50 + "\n")

def main():
    try:
        print_banner()
        check_os()
        check_python()
        install_repo()
        configure_env() # Prompt Key di sini
        setup_venv()    # Setup dependencies
        inject_bashrc()
        final_test()
    except KeyboardInterrupt:
        print("\n\n🚫 Instalasi dibatalkan pengguna.")
        sys.exit(0)

if __name__ == "__main__":
    main()
