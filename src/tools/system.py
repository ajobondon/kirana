import platform
import subprocess
import sys
import os
from rich.console import Console

console = Console()

def get_distro_id():
    """Deteksi Distro Linux"""
    try:
        with open("/etc/os-release") as f:
            for line in f:
                if line.startswith("ID="):
                    return line.split("=")[1].strip().strip('"')
    except:
        return "unknown"

def run_command(cmd):
    """Jalankan command shell"""
    try:
        # shell=True agar bisa chain command (&&)
        subprocess.run(cmd, shell=True, check=True)
        return True
    except subprocess.CalledProcessError:
        return False

def handle_system_update(prompt):
    """
    Handler Cerdas untuk Update System.
    Support: Debian/Ubuntu, RHEL/Fedora, Windows.
    """
    os_type = platform.system().lower()
    
    console.print(f"[bold cyan]⚙️ Mendeteksi OS: {os_type.upper()}[/bold cyan]")

    update_cmd = ""
    upgrade_cmd = ""
    check_cmd = ""

    # --- 1. LINUX LOGIC ---
    if os_type == "linux":
        distro = get_distro_id()
        console.print(f"[dim]🐧 Distro detected: {distro}[/dim]")

        if any(x in distro for x in ["ubuntu", "debian", "kali", "parrot", "mint", "pop"]):
            # APT Family
            check_cmd = "sudo apt update"
            list_cmd = "apt list --upgradable"
            upgrade_cmd = "sudo apt upgrade -y"
        
        elif any(x in distro for x in ["fedora", "rhel", "centos", "rocky", "alma"]):
            # DNF Family
            check_cmd = "sudo dnf check-update" # Exit code 100 means updates available
            list_cmd = None # dnf check-update sudah nge-list
            upgrade_cmd = "sudo dnf upgrade -y"
            
        elif "arch" in distro or "manjaro" in distro:
            # Pacman Family
            check_cmd = "sudo pacman -Sy"
            list_cmd = "pacman -Qu"
            upgrade_cmd = "sudo pacman -Syu --noconfirm"
        
        else:
            console.print(f"[red]❌ Distro '{distro}' belum didukung otomatis.[/red]")
            return

        # EKSEKUSI LINUX
        console.print("\n[bold yellow]1️⃣  Mengecek Update Repository...[/bold yellow]")
        # Khusus DNF, return code 100 itu normal (ada update)
        try:
            subprocess.run(check_cmd, shell=True)
        except: pass 
        
        if list_cmd:
            console.print("\n[bold yellow]2️⃣  Daftar Paket yang akan diupdate:[/bold yellow]")
            subprocess.run(list_cmd, shell=True)

    # --- 2. WINDOWS LOGIC (Trickiest Part) ---
    elif os_type == "windows":
        console.print("[dim]🪟 Menggunakan 'winget' package manager...[/dim]")
        # Cek ketersediaan winget
        if subprocess.call("where winget >nul 2>nul", shell=True) != 0:
            console.print("[red]❌ 'winget' tidak ditemukan. Pastikan App Installer terinstall.[/red]")
            return

        console.print("\n[bold yellow]1️⃣  Mengecek Update via Winget...[/bold yellow]")
        # Winget upgrade list
        subprocess.run("winget upgrade", shell=True)
        
        upgrade_cmd = "winget upgrade --all"

    # --- 3. MACOS LOGIC ---
    elif os_type == "darwin":
        console.print("[dim]🍎 MacOS detected (Brew)[/dim]")
        console.print("\n[bold yellow]1️⃣  Brew Update...[/bold yellow]")
        subprocess.run("brew update", shell=True)
        subprocess.run("brew outdated", shell=True)
        upgrade_cmd = "brew upgrade"

    else:
        console.print("[red]❌ OS tidak dikenali.[/red]")
        return

    # --- KONFIRMASI USER ---
    console.print("\n" + "="*40)
    user_input = input("👉 Apakah Anda ingin melanjutkan proses UPGRADE? (y/n): ").lower().strip()
    
    if user_input == 'y':
        console.print(f"\n[bold green]🚀 Menjalankan: {upgrade_cmd}[/bold green]")
        success = run_command(upgrade_cmd)
        
        if success:
            console.print("\n[bold green]✅ System Upgrade Selesai![/bold green]")
            # Optional: Auto-remove sampah
            if "apt" in upgrade_cmd:
                console.print("[dim]🧹 Cleaning up (autoremove)...[/dim]")
                subprocess.run("sudo apt autoremove -y", shell=True)
        else:
            console.print("\n[bold red]❌ Gagal saat upgrade.[/bold red]")
    else:
        console.print("\n[yellow]🚫 Upgrade dibatalkan user.[/yellow]")

# Fungsi Cek System Biasa (CPU/RAM)
def run_system_check(prompt=""):
    import psutil
    cpu = psutil.cpu_percent(interval=1)
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    console.print(f"\n🖥️  [bold]SYSTEM STATUS[/bold]")
    console.print(f"   CPU Usage : {cpu}%")
    console.print(f"   RAM Usage : {mem.percent}% ({mem.used // (1024**3)}GB / {mem.total // (1024**3)}GB)")
    console.print(f"   Disk Root : {disk.percent}% ({disk.free // (1024**3)}GB Free)")
