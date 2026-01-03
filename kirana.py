import sys
import argparse
import re
import time
# Pastikan install psutil di venv client: pip install psutil
import psutil 
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

# Import Core
from src.core.client import KiranaClient
from src.core.help_text import get_help_panel

# Import Tools
from src.tools.system import run_system_check
from src.tools.netdiag import run_netdiag, run_command # Helper ping
from src.tools.files import run_file_search, handle_file_analysis, handle_file_creation, handle_file_fix
from src.tools.reminder import handle_add_reminder, list_reminders, clear_reminders, _load_reminders

console = Console()

def router(prompt: str, client: KiranaClient):
    """Otak Routing Utama"""
    prompt_lower = prompt.lower().strip()

    # --- 1. HELP MENU ---
    if prompt_lower in ["help", "bantuan", "menu", "panduan", "?"]:
        console.print(get_help_panel()); return

    # --- 2. PATROLI (SISKAMLING) [NEW] ---
    elif prompt_lower in ["patroli", "siskamling", "cek pagi", "morning briefing"]:
        run_patroli(client); return

    # --- 3. SERVER TOOLS (REMOTE) ---
    elif "cek keamanan" in prompt_lower or "analisa keamanan" in prompt_lower:
        match = re.search(r'(https?://[^\s]+)|([a-zA-Z0-9-]+\.[a-zA-Z0-9.-]+)', prompt)
        if match: handle_security_scan(match.group(0), client)
        else: console.print("[bold red]❌ Mana targetnya Fox?[/bold red]")
        return

    elif "cek web" in prompt_lower or "analisa web" in prompt_lower:
        match = re.search(r'https?://[^\s]+', prompt)
        if match: handle_web_scan(match.group(0), client)
        else: console.print("[bold red]❌ Mana URL-nya Fox?[/bold red]")
        return

    # --- 4. LOCAL TOOLS ---
    elif any(k in prompt_lower for k in ["cek system", "status system", "update system", "cek update"]):
        run_system_check(prompt_lower); return
    elif any(k in prompt_lower for k in ["cek internet", "diagnosa", "speedtest", "cek jaringan"]):
        run_netdiag(prompt_lower); return

    elif "cari file" in prompt_lower or "cari kata" in prompt_lower:
        run_file_search(prompt); return
    elif "analisa file" in prompt_lower:
        handle_file_analysis(prompt, client); return
    elif any(k in prompt_lower for k in ["buatin file", "buatkan file", "bikin file"]):
        handle_file_creation(prompt, client); return
    elif any(k in prompt_lower for k in ["perbaiki file", "benerin file", "fix file"]):
        handle_file_fix(prompt, client); return

    elif any(k in prompt_lower for k in ["ingetin", "ingatkan", "remind me"]):
        handle_add_reminder(prompt, client); return
    elif any(k in prompt_lower for k in ["cek reminder", "list reminder", "lihat alarm"]):
        list_reminders(); return
    elif any(k in prompt_lower for k in ["hapus semua reminder", "hapus reminder"]):
        clear_reminders(); return

    # --- MEMORY ---
    elif "ingat bahwa" in prompt_lower or "ingat ini" in prompt_lower:
        clean_text = re.sub(r"(ingat bahwa|ingat ini)\s*", "", prompt, flags=re.IGNORECASE).strip()
        handle_memory_learn(clean_text, client); return

    elif "lupakan bahwa" in prompt_lower:
        clean_text = re.sub(r"(lupakan bahwa)\s*", "", prompt, flags=re.IGNORECASE).strip()
        handle_memory_forget(clean_text, client); return

    # --- DEFAULT: CHAT ---
    handle_chat_request(prompt, client)


# --- FEATURE: PATROLI SISKAMLING [NEW] ---
def run_patroli(client: KiranaClient):
    console.print("\n👮 [bold blue]MEMULAI PATROLI PAGI (SISKAMLING)[/bold blue]")
    console.print("[dim]Memeriksa kesehatan laptop, jaringan, dan jadwal...[/dim]\n")

    # 1. Cek System (Silent Mode)
    cpu = psutil.cpu_percent(interval=0.5)
    mem = psutil.virtual_memory().percent
    disk = psutil.disk_usage("/").percent
    
    sys_status = "[green]SEHAT[/green]"
    if cpu > 80 or mem > 85 or disk > 90: sys_status = "[red]KRITIS[/red]"
    elif cpu > 60 or mem > 70 or disk > 80: sys_status = "[yellow]WASPADA[/yellow]"
    
    console.print(f"🖥️  System Status: {sys_status} (CPU: {cpu}%, RAM: {mem}%, Disk: {disk}%)")

    # 2. Cek Internet
    ping = run_command("ping -c 1 -W 1 8.8.8.8")
    net_status = "[green]ONLINE[/green]" if ping else "[red]OFFLINE[/red]"
    console.print(f"🌐 Internet Status: {net_status}")

    # 3. Cek Reminder
    reminders = _load_reminders()
    count = len(reminders)
    rem_status = f"[cyan]Ada {count} agenda.[/cyan]" if count > 0 else "[dim]Tidak ada agenda.[/dim]"
    console.print(f"📅 Reminder: {rem_status}")
    if count > 0:
        for r in reminders[:3]: # Show top 3
            console.print(f"   - {r['time']}: {r['message']}")

    # 4. Lapor ke Server (Brain) untuk insight
    console.print("\n[dim]Meminta insight dari Markas Pusat...[/dim]")
    
    # Context untuk AI
    patrol_data = f"""
    [System Check]
    CPU: {cpu}% | RAM: {mem}% | Disk: {disk}% ({sys_status})
    Internet: {net_status}
    Reminder Count: {count}
    Top Reminders: {[r['message'] for r in reminders[:3]]}
    """
    
    prompt = f"Saya baru saja melakukan patroli laptop dengan hasil berikut: {patrol_data}. Berikan komentar singkat/semangat dalam 1 kalimat saja (Bahasa Indonesia) seolah kamu asisten pribadi yang perhatian."
    
    try:
        # Panggil API Chat biasa
        payload = {"message": prompt, "role": "primary"}
        response = client.post_request("/api/v1/chat/ask", payload)
        
        if "reply" in response:
            console.print("")
            console.print(Markdown(response['reply']))
            console.print("")
    except:
        console.print("[yellow]Gagal menghubungi markas, tapi patroli lokal selesai.[/yellow]")

# --- HELPER FUNCTIONS ---

def handle_security_scan(target: str, client: KiranaClient):
    console.print(f"[bold cyan]🛡️ Memerintahkan Server untuk Scan: {target}[/bold cyan]")
    with console.status(f"[bold yellow]Sedang menjalankan Secator & Analisa AI (Bisa 1-5 menit)...[/bold yellow]", spinner="grenade"):
        payload = {"target": target, "scan_type": "full"}
        response = client.post_request("/api/v1/security/scan", payload, timeout=600)
    if "error" in response: console.print(f"[bold red]❌ Gagal Scan:[/bold red] {response['error']}")
    else:
        console.print(f"\n[bold green]✅ {response.get('tool','Secator')} Finished:[/bold green]")
        console.print(Markdown(response.get("result", ""))); console.print("")

def handle_web_scan(url: str, client: KiranaClient):
    console.print(f"[bold cyan]⚡ Memerintahkan Server untuk Analisa Web: {url}[/bold cyan]")
    with console.status(f"[bold yellow]Membuka Headless Browser di Server...[/bold yellow]", spinner="runner"):
        payload = {"url": url}
        response = client.post_request("/api/v1/web/analyze", payload, timeout=300)
    if "error" in response: console.print(f"[bold red]❌ Gagal Analisa Web:[/bold red] {response['error']}")
    else:
        console.print(f"\n[bold green]✅ Webload Analysis Finished:[/bold green]")
        console.print(Markdown(response.get("result", ""))); console.print("")

def handle_chat_request(prompt: str, client: KiranaClient):
    # CLEAN VERSION (Tanpa Header)
    with console.status("[bold yellow]Sedang berpikir...[/bold yellow]", spinner="dots"):
        payload = {"message": prompt, "role": "primary"}
        response = client.post_request("/api/v1/chat/ask", payload)
    
    if "error" in response:
        console.print(f"[bold red]❌ Error:[/bold red] {response['error']}")
    else:
        reply = response.get("reply", "")
        console.print("")
        console.print(Markdown(reply))
        console.print("")

def handle_memory_learn(text: str, client: KiranaClient):
    if not text: console.print("[red]❌ Apa yang harus diingat?[/red]"); return
    with console.status("[bold yellow]Sedang menanam ingatan ke Server...[/bold yellow]", spinner="dots"):
        payload = {"text": text}
        response = client.post_request("/api/v1/memory/learn", payload)
    if "error" in response: console.print(f"[bold red]❌ Gagal:[/bold red] {response['error']}")
    else:
        console.print(f"[bold green]🧠 Ingatan Tersimpan di Server![/bold green]")
        console.print(f"📝 {response['message']}")

def handle_memory_forget(text: str, client: KiranaClient):
    if not text: console.print("[red]❌ Apa yang harus dilupakan?[/red]"); return
    with console.status("[bold yellow]Sedang menghapus ingatan di Server...[/bold yellow]", spinner="dots"):
        payload = {"text": text}
        response = client.post_request("/api/v1/memory/forget", payload)
    if "error" in response: console.print(f"[bold red]❌ Gagal:[/bold red] {response['error']}")
    else:
        console.print(f"[bold green]🗑️ Ingatan Dihapus![/bold green]")
        console.print(f"📝 {response['message']}")

def run_interactive_mode(client: KiranaClient):
    console.print("[bold green]** KIRANA v5.0 (CLIENT) **[/bold green]")
    console.print("(Ketik 'exit' buat udahan, 'clear' buat bersihin layar)\n")
    while True:
        try:
            user_input = input("Fox 🦊: ").strip()
            if not user_input: continue
            if user_input.lower() in ['exit', 'quit', 'bye']: console.print("\n[italic]Bye Fox! 👋[/italic]\n"); break
            if user_input.lower() == 'clear': console.clear(); continue
            router(user_input, client)
        except KeyboardInterrupt: console.print("\n[italic]Aborted.[/italic]"); break
        except Exception as e: console.print(f"[bold red]❌ Client Error:[/bold red] {e}")

def main():
    parser = argparse.ArgumentParser(description="Kirana Client CLI")
    parser.add_argument("prompt", nargs="*", help="Prompt/Perintah untuk Kirana")
    args = parser.parse_args()
    full_prompt = " ".join(args.prompt).strip()
    try: client = KiranaClient()
    except Exception as e: console.print(f"[bold red]FATAL:[/bold red] Gagal init config. {e}"); sys.exit(1)
    if full_prompt: router(full_prompt, client)
    else: run_interactive_mode(client)

if __name__ == "__main__": main()
