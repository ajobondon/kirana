import sys
import argparse
import re
import time
import os
import psutil 
from collections import Counter
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
from src.tools.files import run_file_search # Helper search path

console = Console()

# --- HELPER: LOG SENTINEL (SMART FILTERING) ---
def smart_filter_log(filepath, max_chars=15000):
    """
    [PORTED FROM LOGSENTINEL.PY V4.5]
    Membaca log file besar, membuang noise, dan mengambil error + tail.
    """
    if not os.path.exists(filepath): return None, "File tidak ditemukan."

    # Pattern Sampah (Noise) yang aman diabaikan
    ignore_patterns = [
        r"CRON\[.*\]:", r"systemd\[.*\]:", r"run-parts",
        r"dhclient", r"ntpd", r"syslogd", r"klogd",
        r"session opened for user", r"session closed for user"
    ]
    
    # Pattern Penting (Signal)
    critical_patterns = [r"Error", r"Fail", r"Critical", r"Panic", r"Denied", r"Refused", r"Segfault"]
    
    important_lines = []
    tail_lines = []
    
    try:
        # Baca file line by line (Memory Safe)
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            # Ambil semua baris dulu (untuk log < 100MB masih aman di RAM modern)
            # Kalau log > 1GB sebaiknya pakai deque, tapi ini simplified version.
            lines = f.readlines()
            
            # Ambil 50 baris terakhir (Context terkini)
            tail_lines = lines[-50:]
            
            # Scan baris sisanya untuk cari error
            for line in lines[:-50]:
                # Skip jika noise
                if any(re.search(p, line, re.IGNORECASE) for p in ignore_patterns):
                    continue
                # Keep jika critical
                if any(re.search(p, line, re.IGNORECASE) for p in critical_patterns):
                    important_lines.append(line)

        # Gabungkan
        # Batasi important lines biar gak kegedean
        if len(important_lines) > 200: 
            important_lines = important_lines[-200:] # Ambil 200 error terakhir aja
            
        full_content = "--- DETECTED ERRORS/WARNINGS ---\n" + "".join(important_lines)
        full_content += "\n--- LATEST LOGS (TAIL) ---\n" + "".join(tail_lines)
        
        # Potong jika masih kepanjangan buat LLM
        return full_content[:max_chars], None

    except Exception as e:
        return None, str(e)

# --- HELPER: CODE CLEANER ---
def extract_clean_code(text):
    pattern = r"```(?:\w+)?\n(.*?)```"
    match = re.search(pattern, text, re.DOTALL)
    if match: return match.group(1).strip()
    return text.replace("```python", "").replace("```bash", "").replace("```", "").strip()

# --- ROUTER UTAMA ---
def router(prompt: str, client: KiranaClient):
    prompt_lower = prompt.lower().strip()

    if prompt_lower in ["help", "bantuan", "menu", "panduan", "?"]:
        console.print(get_help_panel()); return

    elif prompt_lower in ["patroli", "siskamling", "cek pagi"]:
        run_patroli(client); return

    # --- LOG SENTINEL (NEW) ---
    elif "cek log" in prompt_lower or "analisa log" in prompt_lower or "scan log" in prompt_lower:
        handle_log_analysis(prompt, client); return

    # --- SERVER TOOLS ---
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

    # --- LOCAL TOOLS ---
    elif any(k in prompt_lower for k in ["cek system", "status system", "update system", "cek update"]):
        run_system_check(prompt_lower); return
    elif any(k in prompt_lower for k in ["cek internet", "diagnosa", "speedtest", "cek jaringan"]):
        run_netdiag(prompt_lower); return

    # --- FILE OPS ---
    elif "cari file" in prompt_lower or "cari kata" in prompt_lower:
        run_file_search(prompt); return
    elif "analisa file" in prompt_lower:
        handle_file_analysis(prompt, client); return
    elif any(k in prompt_lower for k in ["buatin file", "buatkan file", "bikin file"]):
        handle_file_creation(prompt, client); return
    elif any(k in prompt_lower for k in ["perbaiki file", "benerin file", "fix file"]):
        handle_file_fix(prompt, client); return

    # --- REMINDER & MEMORY ---
    elif any(k in prompt_lower for k in ["ingetin", "ingatkan", "remind me"]):
        handle_add_reminder(prompt, client); return
    elif any(k in prompt_lower for k in ["cek reminder", "list reminder", "lihat alarm"]):
        list_reminders(); return
    elif any(k in prompt_lower for k in ["hapus semua reminder", "hapus reminder"]):
        clear_reminders(); return

    elif "ingat bahwa" in prompt_lower or "ingat ini" in prompt_lower:
        clean_text = re.sub(r"(ingat bahwa|ingat ini)\s*", "", prompt, flags=re.IGNORECASE).strip()
        handle_memory_learn(clean_text, client); return

    elif "lupakan bahwa" in prompt_lower:
        clean_text = re.sub(r"(lupakan bahwa)\s*", "", prompt, flags=re.IGNORECASE).strip()
        handle_memory_forget(clean_text, client); return

    handle_chat_request(prompt, client)


# --- HANDLER: LOG SENTINEL ---
def handle_log_analysis(prompt, client):
    # Logic: "cek log /var/log/syslog"
    # 1. Cari path log
    match = re.search(r"(cek log|analisa log|scan log)\s+(.+)", prompt, re.IGNORECASE)
    if not match:
        console.print("[red]❌ Format: 'cek log <path_file>'[/red]")
        return

    path = match.group(2).strip()
    
    # 2. Filtering Lokal (Heavy Lifting di Client)
    console.print(f"[cyan]🔍 Log Sentinel: Membaca & Memfilter '{path}'...[/cyan]")
    
    filtered_content, error = smart_filter_log(path)
    if error:
        console.print(f"[red]❌ Gagal baca log: {error}[/red]")
        return

    if len(filtered_content) < 50:
        console.print("[green]✅ Log terlihat bersih (Tidak ada error kritikal/signifikan).[/green]")
        return

    console.print(f"[dim]📦 Mengirim ringkasan log ({len(filtered_content)} chars) ke Markas Pusat...[/dim]")

    # 3. Kirim ke Server (Yayuk/Primary) dengan System Prompt Forensik
    system_prompt_forensic = """
    IDENTITY: You are a Digital Forensic Analyst.
    TASK: Analyze these log snippets. Identify critical errors, suspicious activities, or system failures.
    OUTPUT: Executive Summary, Key Issues (Bulleted), and Recommended Fixes.
    """
    
    payload = {
        "message": f"Analisa log server ini:\n\n{filtered_content}",
        "role": "primary", # Yayuk (Technical)
        "system_prompt": system_prompt_forensic
    }
    
    with console.status("[bold yellow]Menganalisa Anomali...[/bold yellow]", spinner="grenade"):
        response = client.post_request("/api/v1/chat/ask", payload)

    if "error" in response:
        console.print(f"[red]❌ Server Error: {response['error']}[/red]")
    else:
        console.print("")
        console.print(f"[bold red]🛡️ LOG SENTINEL REPORT:[/bold red]")
        console.print(Markdown(response.get("reply", "")))
        console.print("")


# --- HANDLERS LAINNYA (TETAP SAMA) ---
# ... (Pastikan fungsi handle_chat_request, handle_file_creation, dll tetap ada seperti sebelumnya) ...
# ... (Saya ringkas bagian ini karena sama persis dengan kode sebelumnya) ...

def handle_chat_request(prompt: str, client: KiranaClient):
    prompt_lower = prompt.lower()
    coding_triggers = ["script", "python", "code", "coding", "buatkan fungsi", "bikin kode", "html", "css", "rust"]
    target_role = "primary" if any(t in prompt_lower for t in coding_triggers) else "secondary"

    with console.status("[bold yellow]Sedang berpikir...[/bold yellow]", spinner="dots"):
        payload = {"message": prompt, "role": target_role}
        response = client.post_request("/api/v1/chat/ask", payload)
    
    if "error" in response:
        console.print(f"[bold red]❌ Error:[/bold red] {response['error']}")
    else:
        reply = response.get("reply", "")
        persona = response.get("persona", "AI")
        console.print("")
        if target_role == "primary": console.print(f"[bold red]😈 Yayuk:[/bold red]")
        else: console.print(f"[bold blue]👩‍💼 Kirana:[/bold blue]")
        console.print(Markdown(reply))
        console.print("")

def handle_file_creation(prompt, client):
    match = re.search(r"(buatin file|buatkan file|bikin file)\s+(\S+)\s+(?:tentang|soal|for|isinya|yang)\s+(.+)", prompt, re.IGNORECASE)
    if not match: console.print("[red]❌ Format: 'buatin file <nama> isinya <deskripsi>'[/red]"); return
    fname, desc = match.group(2).strip(), match.group(3).strip()
    
    import os
    from dotenv import load_dotenv
    load_dotenv()
    WORKSPACE_DIR = os.getenv("WORKSPACE_DIR", os.path.expanduser("~/kirana/workspace"))
    if not os.path.exists(WORKSPACE_DIR): os.makedirs(WORKSPACE_DIR)
    full_path = os.path.join(WORKSPACE_DIR, fname)
    
    console.print(f"[cyan]🚀 Yayuk sedang coding '{fname}'...[/cyan]")
    payload = {"message": f"Create code for file '{fname}'. Requirement: {desc}. OUTPUT CODE ONLY.", "role": "primary", "system_prompt": "You are Expert Dev. Fix code. Output ONLY code."}
    with console.status("[bold yellow]Coding...[/bold yellow]", spinner="dots"): response = client.post_request("/api/v1/chat/ask", payload)
    if "error" in response: console.print(f"[red]❌ Error: {response['error']}[/red]")
    else:
        code = extract_clean_code(response.get("reply", ""))
        try:
            with open(full_path, 'w') as f: f.write(code)
            console.print(f"[bold green]✅ File berhasil dibuat: {full_path}[/bold green]")
        except Exception as e: console.print(f"[red]❌ Gagal tulis: {e}[/red]")

def handle_file_analysis(prompt, client):
    match = re.search(r"analisa file\s+(.+)", prompt, re.IGNORECASE)
    if not match: console.print("[red]❌ Path file?[/red]"); return
    path = match.group(1).strip()
    if not os.path.exists(path): console.print("[red]❌ File gak ada.[/red]"); return
    try:
        with open(path, 'r', encoding='utf-8', errors='ignore') as f: content = f.read()
    except Exception as e: console.print(f"[red]❌ Gagal baca: {e}[/red]"); return
    console.print(f"[cyan]🔍 Mengirim '{path}' ke Yayuk...[/cyan]")
    payload = {"message": f"Analisa kode ini:\n\n{content[:15000]}", "role": "primary"}
    with console.status("Menganalisa...", spinner="dots"): response = client.post_request("/api/v1/chat/ask", payload)
    if "error" in response: console.print(f"[red]Error: {response['error']}[/red]")
    else: console.print(Markdown(response.get("reply", "")))

def handle_file_fix(prompt, client):
    match = re.search(r"(perbaiki|benerin|fix)\s+file\s+(.+)", prompt, re.IGNORECASE)
    if not match: console.print("[red]❌ Path file?[/red]"); return
    path = match.group(2).strip()
    if not os.path.exists(path): console.print("[red]❌ File gak ada.[/red]"); return
    with open(path, 'r') as f: content = f.read()
    console.print(f"[cyan]🚑 Yayuk sedang healing code...[/cyan]")
    payload = {"message": f"Fix bugs. Output ONLY fixed code:\n\n{content[:15000]}", "role": "primary", "system_prompt": "You are Expert Dev. Output ONLY code."}
    with console.status("Fixing...", spinner="dots"): response = client.post_request("/api/v1/chat/ask", payload)
    if "error" in response: console.print(f"[red]Error: {response['error']}[/red]")
    else:
        code = extract_clean_code(response.get("reply", ""))
        import shutil; shutil.copy(path, path+".bak")
        with open(path, 'w') as f: f.write(code)
        console.print(f"[bold green]✅ File Healed! Backup: {path}.bak[/bold green]")

# --- HELPER LAINNYA ---
def run_patroli(client):
    console.print("\n👮 [bold blue]SISKAMLING PAGI[/bold blue]")
    cpu = psutil.cpu_percent(interval=0.5)
    mem = psutil.virtual_memory().percent
    console.print(f"🖥️  System: CPU {cpu}%, RAM {mem}%")
    prompt = f"Lapor: CPU {cpu}%, RAM {mem}%. Beri semangat."
    payload = {"message": prompt, "role": "primary"}
    try:
        resp = client.post_request("/api/v1/chat/ask", payload)
        console.print(f"\n[bold red]😈 Yayuk:[/bold red] {resp.get('reply','')}\n")
    except: pass

def handle_security_scan(target, client):
    console.print(f"[bold cyan]🛡️ Scan: {target}[/bold cyan]")
    with console.status("Scanning...", spinner="grenade"):
        resp = client.post_request("/api/v1/security/scan", {"target": target, "scan_type": "full"}, timeout=600)
    if "error" in resp: console.print(f"[red]Error: {resp['error']}[/red]")
    else: console.print(Markdown(resp.get("result", "")))

def handle_web_scan(url, client):
    console.print(f"[bold cyan]⚡ Web Analisa: {url}[/bold cyan]")
    with console.status("Analyzing...", spinner="runner"):
        resp = client.post_request("/api/v1/web/analyze", {"url": url}, timeout=300)
    if "error" in resp: console.print(f"[red]Error: {resp['error']}[/red]")
    else: console.print(Markdown(resp.get("result", "")))

def handle_memory_learn(text, client):
    with console.status("Saving...", spinner="dots"): resp = client.post_request("/api/v1/memory/learn", {"text": text})
    if "error" not in resp: console.print(f"[green]🧠 Tersimpan![/green]")

def handle_memory_forget(text, client):
    with console.status("Deleting...", spinner="dots"): resp = client.post_request("/api/v1/memory/forget", {"text": text})
    if "error" not in resp: console.print(f"[green]🗑️ Dihapus![/green]")

def run_interactive_mode(client):
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
