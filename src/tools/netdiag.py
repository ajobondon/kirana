import subprocess
import sys
import re
import shutil
import time
from rich.console import Console

console = Console()

def run_command(command, timeout=None):
    try:
        result = subprocess.run(
            command, shell=True, check=True, 
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, 
            text=True, timeout=timeout
        )
        return result.stdout.strip()
    except:
        return None

def print_step(message):
    console.print(f"\n🔄 [bold]{message}...[/bold]")
    time.sleep(0.5)

def run_netdiag(prompt=""):
    """Main function untuk diagnosa jaringan"""
    console.print("[bold green]--- 🕵️ MULAI DIAGNOSA JARINGAN LOKAL ---[/bold green]")

    # 1. Cek Interface
    print_step("Mengecek Interface Jaringan")
    route_info = run_command("ip route show default")
    
    if not route_info:
        console.print("[bold red]❌ FATAL: Tidak ada koneksi jaringan.[/bold red]")
        return

    # Extract Interface
    match = re.search(r"dev\s+(\S+)", route_info)
    iface = match.group(1) if match else "unknown"
    console.print(f"✅ Terhubung via Interface: [cyan]{iface}[/cyan]")

    # 2. Cek Gateway
    print_step("Mengecek Koneksi ke Router (Gateway)")
    gateway_match = re.search(r"default via (\S+)", route_info)
    if gateway_match:
        gateway_ip = gateway_match.group(1)
        ping_res = run_command(f"ping -c 3 -W 2 {gateway_ip}")
        if ping_res:
             # Ambil avg time
             rtt = re.search(r"rtt min/avg/max/mdev = [\d\.]+/([\d\.]+)/", ping_res)
             avg = rtt.group(1) if rtt else "?"
             console.print(f"✅ Ping Gateway ({gateway_ip}): [green]{avg} ms[/green]")
        else:
             console.print(f"[bold red]❌ GAGAL Ping Gateway ({gateway_ip})[/bold red]")
    else:
        console.print("[yellow]⚠️ Gateway tidak ditemukan.[/yellow]")

    # 3. Cek Internet (Google)
    print_step("Mengecek Koneksi Internet (8.8.8.8)")
    ping_res = run_command("ping -c 3 -W 2 8.8.8.8")
    if ping_res:
         rtt = re.search(r"rtt min/avg/max/mdev = [\d\.]+/([\d\.]+)/", ping_res)
         avg = rtt.group(1) if rtt else "?"
         console.print(f"✅ Ping Internet: [green]{avg} ms[/green]")
    else:
         console.print("[bold red]❌ GAGAL Ping Internet. Cek ISP![/bold red]")

    # 4. Speedtest (Opsional, kalau user minta atau eksplisit 'speedtest')
    if "speedtest" in prompt or shutil.which("speedtest-cli"):
        print_step("Menjalankan Speedtest (via speedtest-cli)")
        if shutil.which("speedtest-cli") or shutil.which("speedtest"):
            # Streaming output langsung ke terminal
            subprocess.run("speedtest-cli --simple", shell=True)
        else:
            console.print("[yellow]⚠️ 'speedtest-cli' belum terinstall. Skip speedtest.[/yellow]")
            console.print("[dim]Tips: pip install speedtest-cli[/dim]")

    console.print("\n[bold green]--- ✅ DIAGNOSA SELESAI ---[/bold green]\n")
