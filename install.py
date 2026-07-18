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
    Server-Client Architecture (v7.0.0 (PIXEL))
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
    
    if system == "windows":
        print(f"\n{C.WARNING}⚠️  OS Windows terdeteksi.{C.ENDC}")
        print("Silakan gunakan PowerShell script untuk instalasi otomatis Kirana Client di Windows.")
        print("Anda dapat menjalankan perintah berikut di PowerShell:")
        print(f"\n    {C.CYAN}powershell -ExecutionPolicy Bypass -c \"irm https://raw.githubusercontent.com/ajobondon/kirana/main/install.ps1 | iex\"{C.ENDC}")
        print("Atau jika Anda sudah men-clone repository ini secara lokal, jalankan:")
        print(f"\n    {C.CYAN}.\\install.ps1{C.ENDC}\n")
        sys.exit(0)
        
    if system not in ["linux", "darwin"]:
        fail(f"OS tidak didukung: {system}")
    
    if system == "linux":
        try:
            with open("/etc/os-release") as f:
                data = f.read().lower()
                supported = ["debian", "ubuntu", "pop", "fedora", "rhel", "centos", "kali", "linuxmint"]
                if not any(distro in data for distro in supported):
                    print(f"{C.WARNING}⚠️  Distro Linux Anda mungkin tidak didukung secara resmi, namun instalasi dilanjutkan.{C.ENDC}")
        except Exception:
            print(f"{C.WARNING}⚠️  Tidak bisa membaca /etc/os-release.{C.ENDC}")
            
    success(f"OS Terdeteksi & Didukung: {platform.system()}")

def check_python():
    step(f"Mengecek Versi Python (Min {MIN_PYTHON[0]}.{MIN_PYTHON[1]})...")
    ver = sys.version_info
    if ver < MIN_PYTHON:
        fail(f"Versi Python Anda {ver.major}.{ver.minor}. Kirana butuh Python {MIN_PYTHON[0]}.{MIN_PYTHON[1]}+")
    success(f"Python {ver.major}.{ver.minor} OK.")

def install_repo():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    is_local_run = os.path.exists(os.path.join(current_dir, "kirana.py")) and os.path.exists(os.path.join(current_dir, "requirements.txt"))
    
    abs_current = os.path.normpath(os.path.abspath(current_dir))
    abs_install = os.path.normpath(os.path.abspath(INSTALL_DIR))
    
    if abs_current == abs_install:
        success("Source code sudah berada di folder tujuan ~/kirana. Melewati fase penyalinan.")
        return

    if is_local_run:
        step(f"Mendeteksi instalasi lokal. Menyalin berkas dari {current_dir} ke {INSTALL_DIR}...")
    else:
        step(f"Mengunduh Source Code dari Git ke {INSTALL_DIR}...")
    
    if os.path.exists(INSTALL_DIR):
        print(f"{C.WARNING}⚠️  Folder {INSTALL_DIR} sudah ada.{C.ENDC}")
        choice = input("   Timpa (hapus & install ulang)? [y/N]: ").lower()
        if choice == 'y':
            shutil.rmtree(INSTALL_DIR)
        else:
            print("   Melanjutkan update di folder existing...")
            if is_local_run:
                # Copy updated files
                for item in os.listdir(current_dir):
                    if item in ['env', 'venv', '.git', '__pycache__']:
                        continue
                    s = os.path.join(current_dir, item)
                    d = os.path.join(INSTALL_DIR, item)
                    if os.path.isdir(s):
                        shutil.copytree(s, d, dirs_exist_ok=True)
                    else:
                        shutil.copy2(s, d)
            else:
                subprocess.run(["git", "pull"], cwd=INSTALL_DIR)
            return

    try:
        if is_local_run:
            shutil.copytree(current_dir, INSTALL_DIR, ignore=shutil.ignore_patterns('env', 'venv', '.git', '__pycache__'))
            success("Penyalinan berkas lokal berhasil.")
        else:
            subprocess.run(["git", "clone", REPO_URL, INSTALL_DIR], check=True)
            success("Repository berhasil di-clone.")
    except Exception as e:
        fail(f"Gagal menginstall source code: {e}")

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
# Client Timeout (in seconds) - untuk proses yang lama di sisi server
KIRANA_TIMEOUT="600"

# Client Identity
CLIENT_ID="{client_id}"
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

def inject_shell():
    # Detect shell config file
    shell = os.getenv("SHELL", "").lower()
    zshrc = os.path.expanduser("~/.zshrc")
    bashrc = os.path.expanduser("~/.bashrc")
    
    config_files = []
    if "zsh" in shell or os.path.exists(zshrc):
        config_files.append((zshrc, "zsh"))
    if "bash" in shell or os.path.exists(bashrc):
        config_files.append((bashrc, "bash"))
        
    if not config_files:
        # Fallback
        config_files.append((bashrc, "bash"))
        
    for rc_file, shell_type in config_files:
        step(f"Integrasi Terminal ({shell_type.upper()} - {rc_file})...")
        try:
            # Check if already installed
            if os.path.exists(rc_file):
                with open(rc_file, "r") as f:
                    if "# 🦊 KIRANA" in f.read():
                        success(f"Konfigurasi {os.path.basename(rc_file)} sudah ada. Skip.")
                        continue
            
            # Setup command not found handler according to shell type
            if shell_type == "zsh":
                handler_name = "command_not_found_handler"
                err_msg = 'printf "zsh: command not found: %s\\n" "$cmd"'
            else:
                handler_name = "command_not_found_handle"
                err_msg = 'printf "bash: %s: No such file or directory\\n" "$cmd"'

            kirana_shell_script = f"""
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
{handler_name}() {{
    local cmd="$*"
    
    # Safety Check: Do not process empty commands
    if [ -z "$cmd" ]; then return 127; fi
    
    # Safety Check: Do not process relative/absolute paths
    if [[ "$cmd" == ./* ]] || [[ "$cmd" == /* ]]; then
        {err_msg}
        return 127
    fi

    # Throw to Kirana (Silent Mode)
    PYTHONWARNINGS="ignore" $KIRANA_PYTHON $KIRANA_SCRIPT "$cmd"
    
    return 0
}}
"""
            with open(rc_file, "a") as f:
                f.write(kirana_shell_script)
            success(f"Magic Shell ditambahkan ke {os.path.basename(rc_file)}")
        except Exception as e:
            print(f"{C.WARNING}Gagal update {rc_file}: {e}. Anda harus setup manual.{C.ENDC}")

def final_test():
    step("Finalizing & Testing...")
    print(f"{C.CYAN}Fox is waking up...{C.ENDC}")
    
    python_bin = os.path.join(VENV_DIR, "bin", "python")
    script = os.path.join(INSTALL_DIR, "kirana.py")
    
    try:
        subprocess.run([python_bin, script, "help"], check=True)
    except Exception as e:
        print(f"{C.WARNING}Test run warning: {e}{C.ENDC}")

    zshrc = os.path.expanduser("~/.zshrc")
    shell_rc = "~/.bashrc"
    if os.path.exists(zshrc):
        shell_rc = "~/.zshrc"

    print("\n" + "="*50)
    print(f"{C.GREEN}{C.BOLD}🎉 INSTALASI SUKSES! 🎉{C.ENDC}")
    print("="*50)
    print(f"Agar Kirana aktif di terminal ini, jalankan perintah:")
    print(f"\n    {C.CYAN}source {shell_rc}{C.ENDC}\n")
    print("Atau tutup dan buka kembali terminal Anda.")
    print("Gunakan command 'kirana' atau 'tanya' untuk memulai.")
    print("="*50 + "\n")

def main():
    try:
        print_banner()
        check_os()
        check_python()
        install_repo()
        configure_env()
        setup_venv()
        inject_shell()
        final_test()
    except KeyboardInterrupt:
        print("\n\n🚫 Instalasi dibatalkan pengguna.")
        sys.exit(0)

if __name__ == "__main__":
    main()

