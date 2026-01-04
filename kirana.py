import sys
import argparse
import re
import time
# Pastikan install psutil: pip install psutil
import psutil 
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

# Import Core
from src.core.client import KiranaClient
from src.core.help_text import get_help_panel

# Import Tools
from src.tools.system import run_system_check
from src.tools.netdiag import run_netdiag, run_command
from src.tools.reminder import handle_add_reminder, list_reminders, clear_reminders, _load_reminders
# Files logic kita tanam langsung disini atau import jika file terpisah. 
# Agar rapi dan atomic, saya gabungkan logic files.py v4.5 ke sini (bagian helper).

console = Console()

# --- HELPER DARI FILES.PY V4.5 ---
def extract_clean_code(text):
    """
    [PORTED FROM V4.5]
    Membersihkan output LLM agar hanya mengambil blok kode.
    """
    pattern = r"```(?:\w+)?\n(.*?)```"
    match = re.search(pattern, text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return text.replace("```python", "").replace("```bash", "").replace("```", "").strip()

# --- ROUTER UTAMA ---
def router(prompt: str, client: KiranaClient):
    """Otak Routing Utama"""
    prompt_lower = prompt.lower().strip()

    # 1. HELP MENU
    if prompt_lower in ["help", "bantuan", "menu", "panduan", "?"]:
        console.print(get_help_panel()); return

    # 2. PATROLI (SISKAMLING)
    elif prompt_lower in ["patroli", "siskamling", "cek pagi"]:
        run_patroli(client); return

    # 3. SERVER TOOLS (REMOTE) -> Yayuk (Primary)
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

    # 4. LOCAL TOOLS
    elif any(k in prompt_lower for k in ["cek system", "status system", "update system", "cek update"]):
        run_system_check(prompt_lower); return
    elif any(k in prompt_lower for k in ["cek internet", "diagnosa", "speedtest", "cek jaringan"]):
        run_netdiag(prompt_lower); return

    # 5. FILE OPERATIONS (CODING) -> Yayuk (Primary)
    elif "cari file" in prompt_lower or "cari kata" in prompt_lower:
        # Import local search
        from src.tools.files import run_file_search
        run_file_search(prompt); return

    elif "analisa file" in prompt_lower:
        handle_file_analysis(prompt, client); return

    elif any(k in prompt_lower for k in ["buatin file", "buatkan file", "bikin file"]):
        handle_file_creation(prompt, client); return

    elif any(k in prompt_lower for k in ["perbaiki file", "benerin file", "fix file"]):
        handle_file_fix(prompt, client); return

    # 6. REMINDER
    elif any(k in prompt_lower for k in ["ingetin", "ingatkan", "remind me"]):
        handle_add_reminder(prompt, client); return
    elif any(k in prompt_lower for k in ["cek reminder", "list reminder", "lihat alarm"]):
        list_reminders(); return
    elif any(k in prompt_lower for k in ["hapus semua reminder", "hapus reminder"]):
        clear_reminders(); return

    # 7. MEMORY
    elif "ingat bahwa" in prompt_lower or "ingat ini" in prompt_lower:
        clean_text = re.sub(r"(ingat bahwa|ingat ini)\s*", "", prompt, flags=re.IGNORECASE).strip()
        handle_memory_learn(clean_text, client); return

    elif "lupakan bahwa" in prompt_lower:
        clean_text = re.sub(r"(lupakan bahwa)\s*", "", prompt, flags=re.IGNORECASE).strip()
        handle_memory_forget(clean_text, client); return

    # 8. DEFAULT CHAT (Logic Baru)
    handle_chat_request(prompt, client)


# --- HANDLERS ---

def handle_chat_request(prompt: str, client: KiranaClient):
    """
    [LOGIC BARU]
    - Default: Kirana (Secondary)
    - Jika ada bau-bau coding: Switch ke Yayuk (Primary)
    """
    prompt_lower = prompt.lower()
    
    # Deteksi intensi coding dalam chat biasa
    coding_triggers = ["script", "python", "code", "coding", "buatkan fungsi", "bikin kode", "html", "css", "rust"]
    
    if any(t in prompt_lower for t in coding_triggers):
        # Auto-switch ke Yayuk
        target_role = "primary" 
        # console.print("[dim]Detected coding request -> Switching to Yayuk[/dim]")
    else:
        # Default Kirana
        target_role = "secondary"

    with console.status("[bold yellow]Sedang berpikir...[/bold yellow]", spinner="dots"):
        payload = {"message": prompt, "role": target_role}
        response = client.post_request("/api/v1/chat/ask", payload)
    
    if "error" in response:
        console.print(f"[bold red]❌ Error:[/bold red] {response['error']}")
    else:
        reply = response.get("reply", "")
        # Tampilkan Persona yang menjawab (untuk debugging user)
        persona = response.get("persona", "AI") # Server v5 dah support return persona
        
        console.print("")
        if target_role == "primary":
            console.print(f"[bold red]😈 Yayuk:[/bold red]") # Label Yayuk
        else:
            console.print(f"[bold blue]👩‍💼 Kirana:[/bold blue]") # Label Kirana
            
        console.print(Markdown(reply))
        console.print("")


def handle_file_creation(prompt, client):
    # Logic: Kirana Client minta Yayuk (Primary) coding
    # "buatin file hello.py isinya print hello"
    
    # 1. Parse Filename & Desc
    match = re.search(r"(buatin file|buatkan file|bikin file)\s+(\S+)\s+(?:tentang|soal|for|isinya|yang)\s+(.+)", prompt, re.IGNORECASE)
    if not match:
        console.print("[red]❌ Format: 'buatin file <nama> isinya <deskripsi>'[/red]")
        return

    fname = match.group(2).strip()
    desc = match.group(3).strip()
    
    import os
    from dotenv import load_dotenv
    load_dotenv()
    WORKSPACE_DIR = os.getenv("WORKSPACE_DIR", os.path.expanduser("~/kirana/workspace"))
    full_path = os.path.join(WORKSPACE_DIR, fname)
    
    if not os.path.exists(WORKSPACE_DIR): os.makedirs(WORKSPACE_DIR)

    console.print(f"[cyan]🚀 Yayuk sedang coding '{fname}'...[/cyan]")
    
    # Kirim ke Server (Role: PRIMARY/Yayuk)
    # Gunakan System Prompt khusus coding
    coding_prompt = "You are an Expert Developer. Output ONLY the code block. No explanation."
    
    payload = {
        "message": f"Create code for file '{fname}'. Requirement: {desc}. OUTPUT CODE ONLY.",
        "role": "primary", 
        "system_prompt": coding_prompt
    }

    with console.status("[bold yellow]Coding...[/bold yellow]", spinner="dots"):
        response = client.post_request("/api/v1/chat/ask", payload)

    if "error" in response:
        console.print(f"[red]❌ Server Error: {response['error']}[/red]")
    else:
        raw_reply = response.get("reply", "")
        # Gunakan Helper v4.5 untuk bersihkan markdown
        code = extract_clean_code(raw_reply)
        
        try:
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(code)
            
            console.print(f"[bold green]✅ File berhasil dibuat![/bold green]")
            console.print(f"📂 Lokasi: [cyan]{full_path}[/cyan]")
        except Exception as e:
            console.print(f"[red]❌ Gagal menulis file: {e}[/red]")

def handle_file_analysis(prompt, client):
    # Logic: Baca file lokal -> Kirim konten ke Yayuk
    match = re.search(r"analisa file\s+(.+)", prompt, re.IGNORECASE)
    if not match: console.print("[red]❌ Path file?[/red]"); return

    path = match.group(1).strip()
    if not os.path.exists(path): console.print("[red]❌ File gak ada.[/red]"); return

    try:
        with open(path, 'r', encoding='utf-8', errors='ignore') as f: content = f.read()
    except Exception as e: console.print(f"[red]❌ Gagal baca: {e}[/red]"); return

    console.print(f"[cyan]🔍 Mengirim '{path}' ke Yayuk untuk diaudit...[/cyan]")
    
    # Kirim ke Server (Primary/Yayuk)
    payload = {
        "message": f"Analisa kode ini. Jelaskan bug, keamanan, dan saran perbaikan:\n\n{content[:15000]}", # Limit char
        "role": "primary"
    }
    
    with console.status("[bold yellow]Menganalisa...[/bold yellow]", spinner="dots"):
        response = client.post_request("/api/v1/chat/ask", payload)
        
    if "error" in response: console.print(f"[red]❌ Error: {response['error']}[/red]")
    else: 
        console.print(f"[bold red]😈 Yayuk Report:[/bold red]")
        console.print(Markdown(response.get("reply", "")))

def handle_file_fix(prompt, client):
    # Logic: Baca file -> Minta Yayuk benerin -> Timpa file
    match = re.search(r"(perbaiki|benerin|fix)\s+file\s+(.+)", prompt, re.IGNORECASE)
    if not match: console.print("[red]❌ Path file?[/red]"); return

    path = match.group(2).strip()
    if not os.path.exists(path): console.print("[red]❌ File gak ada.[/red]"); return

    with open(path, 'r') as f: content = f.read()
    
    console.print(f"[cyan]🚑 Yayuk sedang melakukan operasi bedah kode...[/cyan]")
    
    payload = {
        "message": f"Fix bugs in this code. Output ONLY the fixed code block:\n\n{content[:15000]}",
        "role": "primary",
        "system_prompt": "You are Expert Dev. Fix code. Output ONLY code."
    }

    with console.status("[bold yellow]Fixing...[/bold yellow]", spinner="dots"):
        response = client.post_request("/api/v1/chat/ask", payload)

    if "error" in response: console.print(f"[red]❌ Error: {response['error']}[/red]")
    else:
        fixed_code = extract_clean_code(response.get("reply", ""))
        
        # Backup logic v4.5
        import shutil
        bak = path + ".bak"
        shutil.copy(path, bak)
        
        with open(path, 'w') as f: f.write(fixed_code)
        
        console.print(f"[bold green]✅ File Healed![/bold green]")
        console.print(f"🛡️ Backup: {bak}")

# --- HELPER LAIN (Copy dari sebelumnya: run_patroli, dll) ---
# Paste fungsi run_patroli, handle_security_scan, dll disini...
# (Agar tidak kepanjangan, pastikan fungsi helper lain tetap ada)

# ... (Helper Functions Sisanya: run_patroli, handle_security_scan, dll) ...

# [SAYA LAMPIRKAN ULANG PATROLI SUPAYA LENGKAP]
def run_patroli(client: KiranaClient):
    console.print("\n👮 [bold blue]MEMULAI PATROLI PAGI (SISKAMLING)[/bold blue]")
    cpu = psutil.cpu_percent(interval=0.5)
    mem = psutil.virtual_memory().percent
    console.print(f"🖥️  System: CPU {cpu}%, RAM {mem}%")
    ping = run_command("ping -c 1 -W 1 8.8.8.8")
    net_status = "ONLINE" if ping else "OFFLINE"
    console.print(f"🌐 Internet: {net_status}")
    reminders = _load_reminders()
    count = len(reminders)
    console.print(f"📅 Agenda: {count} items")
    
    prompt = f"Lapor patroli: CPU {cpu}%, RAM {mem}%, Net {net_status}, Agenda {count}. Beri semangat singkat ala militer."
    # Patroli pakai YAYUK (Primary) biar semangat
    payload = {"message": prompt, "role": "primary"} 
    try:
        resp = client.post_request("/api/v1/chat/ask", payload)
        console.print(f"\n[bold red]😈 Yayuk:[/bold red] {resp.get('reply','')}\n")
    except: pass

# --- HELPER SYSTEM & MEMORY (REQUIRED) ---
def handle_security_scan(target: str, client: KiranaClient):
    console.print(f"[bold cyan]🛡️ Scan: {target}[/bold cyan]")
    with console.status("Scanning...", spinner="grenade"):
        payload = {"target": target, "scan_type": "full"}
        resp = client.post_request("/api/v1/security/scan", payload, timeout=600)
    if "error" in resp: console.print(f"[red]Error: {resp['error']}[/red]")
    else: console.print(Markdown(resp.get("result", "")))

def handle_web_scan(url: str, client: KiranaClient):
    console.print(f"[bold cyan]⚡ Web Analisa: {url}[/bold cyan]")
    with console.status("Analyzing...", spinner="runner"):
        payload = {"url": url}
        resp = client.post_request("/api/v1/web/analyze", payload, timeout=300)
    if "error" in resp: console.print(f"[red]Error: {resp['error']}[/red]")
    else: console.print(Markdown(resp.get("result", "")))

def handle_memory_learn(text: str, client: KiranaClient):
    with console.status("Saving...", spinner="dots"):
        resp = client.post_request("/api/v1/memory/learn", {"text": text})
    if "error" not in resp: console.print(f"[green]🧠 Tersimpan![/green]")

def handle_memory_forget(text: str, client: KiranaClient):
    with console.status("Deleting...", spinner="dots"):
        resp = client.post_request("/api/v1/memory/forget", {"text": text})
    if "error" not in resp: console.print(f"[green]🗑️ Dihapus![/green]")

def run_interactive_mode(client: KiranaClient):
    console.print("[bold green]** KIRANA v5.0 (CLIENT) **[/bold green]")
    console.print("(Ketik 'exit' buat udahan)\n")
    while True:
        try:
            user_input = input("Fox 🦊: ").strip()
            if not user_input: continue
            if user_input.lower() in ['exit', 'quit']: break
            router(user_input, client)
        except KeyboardInterrupt: break
        except Exception as e: console.print(f"[red]Error: {e}[/red]")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("prompt", nargs="*")
    args = parser.parse_args()
    full_prompt = " ".join(args.prompt).strip()
    try: client = KiranaClient()
    except Exception as e: console.print(f"[red]FATAL: {e}[/red]"); sys.exit(1)
    if full_prompt: router(full_prompt, client)
    else: run_interactive_mode(client)

if __name__ == "__main__": main()
