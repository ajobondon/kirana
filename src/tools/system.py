import os
import sys
import platform
import subprocess
import shutil
import psutil
from rich.console import Console
from rich.panel import Panel

console = Console()

class SystemTool:
    @staticmethod
    def get_os_type():
        """Mendeteksi OS secara spesifik"""
        system = platform.system().lower()
        if system == "windows": 
            return "windows"
        elif system == "linux":
            # Cek keberadaan file rilis untuk membedakan Distro
            if os.path.exists("/etc/debian_version"): 
                return "debian_based"
            if os.path.exists("/etc/redhat-release") or os.path.exists("/etc/centos-release") or os.path.exists("/etc/fedora-release"): 
                return "rhel_based"
            return "linux_generic"
        return "unsupported"

    @staticmethod
    def check_health():
        """Cek Resource Laptop (CPU, RAM, Disk) - Universal"""
        console.print("[bold cyan]🔍 Memeriksa Kesehatan Laptop...[/bold cyan]")
        
        # 1. CPU
        cpu_usage = psutil.cpu_percent(interval=1)
        
        # 2. RAM
        mem = psutil.virtual_memory()
        ram_total_gb = round(mem.total / (1024**3), 2)
        ram_used_percent = mem.percent

        # 3. Disk (Root / atau C:\)
        disk_path = "/"
        if platform.system() == "Windows": disk_path = "C:\\"
        
        try:
            disk = psutil.disk_usage(disk_path)
            disk_total_gb = round(disk.total / (1024**3), 2)
            disk_free_gb = round(disk.free / (1024**3), 2)
            disk_percent = disk.percent
        except:
            # Fallback kalau path C:\ gak ketemu (jarang terjadi)
            disk_percent = "N/A"
            disk_free_gb = 0
            disk_total_gb = 0

        report = f"""
[bold]OS System[/bold] : {platform.system()} {platform.release()} ({SystemTool.get_os_type()})
[bold]CPU Load[/bold]  : {cpu_usage}%
[bold]RAM Usage[/bold] : {ram_used_percent}% ({ram_total_gb} GB Total)
[bold]Disk Usage[/bold]: {disk_percent}% (Free: {disk_free_gb} GB / Total: {disk_total_gb} GB)
        """
        console.print(Panel(report.strip(), title="System Health", border_style="blue"))

    @staticmethod
    def run_update(prompt=""):
        """Menjalankan Update System Lokal (Multi-OS)"""
        os_type = SystemTool.get_os_type()
        is_install = ("install" in prompt) or ("upgrade" in prompt)
        
        cmd = ""
        msg = ""

        # --- LOGIC DEBIAN/UBUNTU ---
        if os_type == "debian_based":
            if is_install:
                cmd = "sudo apt-get update && sudo apt-get upgrade -y"
                msg = "🚀 [DEBIAN/UBUNTU] Updating & Upgrading system..."
            else:
                cmd = "sudo apt-get update"
                msg = "🔎 [DEBIAN/UBUNTU] Checking updates..."
        
        # --- LOGIC RHEL/CENTOS/FEDORA ---
        elif os_type == "rhel_based":
            # Cek pake dnf atau yum
            pkg_mgr = "dnf" if shutil.which("dnf") else "yum"
            if is_install:
                cmd = f"sudo {pkg_mgr} update -y"
                msg = f"🚀 [RHEL/CENTOS] Upgrading system via {pkg_mgr}..."
            else:
                cmd = f"sudo {pkg_mgr} check-update"
                msg = f"🔎 [RHEL/CENTOS] Checking updates via {pkg_mgr}..."

        # --- LOGIC WINDOWS ---
        elif os_type == "windows":
             if is_install:
                cmd = "winget upgrade --all"
                msg = "🚀 [WINDOWS] Upgrading via Winget..."
             else:
                cmd = "winget list --upgrade-available"
                msg = "🔎 [WINDOWS] Checking updates..."
        
        else:
            console.print(f"[red]❌ OS '{os_type}' belum didukung script update otomatis.[/red]")
            return

        console.print(f"[bold yellow]{msg}[/bold yellow]")
        try:
            # Shell=True dibutuhkan untuk chaining command (&&) dan akses path sistem
            subprocess.run(cmd, shell=True) 
        except Exception as e:
            console.print(f"[bold red]❌ Gagal Update:[/bold red] {e}")

# Fungsi wrapper biar gampang dipanggil
def run_system_check(prompt):
    if "update" in prompt or "cek update" in prompt:
        SystemTool.run_update(prompt)
    else:
        SystemTool.check_health()
