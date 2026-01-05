import sys
import argparse
import re
import time
import os
import json 
import psutil
from rich.console import Console
from rich.markdown import Markdown

# Import Core
from src.core.client import KiranaClient
from src.core.help_text import get_help_panel

# Import Tools
from src.tools.system import run_system_check
from src.tools.netdiag import run_netdiag, run_command
from src.tools.reminder import handle_add_reminder, list_reminders, clear_reminders, _load_reminders
from src.tools.files import run_file_search 

console = Console()

# --- KONFIGURASI MEMORI PENDEK (EPHEMERAL CONTEXT) ---
MEMORY_DIR = os.path.expanduser("~/kirana/memory")
STATE_FILE = os.path.join(MEMORY_DIR, "cli_state.json")
MAX_IDLE_SECONDS = 60  
MAX_TURNS = 3          

def _load_cli_state():
    """Membaca ingatan pendek"""
    empty_state = {"history": [], "last_update": 0}
    if not os.path.exists(STATE_FILE): return empty_state
    try:
        with open(STATE_FILE, 'r') as f:
            state = json.load(f)
        if time.time() - state.get("last_update", 0) > MAX_IDLE_SECONDS:
            return empty_state 
        return state
    except: return empty_state

def _save_cli_state(history):
    """Menyimpan ingatan pendek"""
    if not os.path.exists(MEMORY_DIR): os.makedirs(MEMORY_DIR)
    if len(history) > MAX_TURNS * 2: history = history[-(MAX_TURNS*2):]
    state = {"history": history, "last_update": time.time()}
    try:
        with open(STATE_FILE, 'w') as f: json.dump(state, f)
    except: pass

# --- HELPER LAIN ---
def extract_clean_code(text):
    pattern = r"```(?:\w+)?\n(.*?)```"
    match = re.search(pattern, text, re.DOTALL)
    if match: return match.group(1).strip()
    return text.replace("```python", "").replace("```bash", "").replace("```", "").strip()

def smart_filter_log(filepath, max_chars=15000):
    """Helper Log Sentinel"""
    if not os.path.exists(filepath): return None, "File tidak ditemukan."
    ignore_patterns = [r"CRON\[.*\]:", r"systemd\[.*\]:", r"run-parts", r"dhclient"]
    critical_patterns = [r"Error", r"Fail", r"Critical", r"Panic", r"Denied"]
    important_lines, tail_lines = [], []
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
            tail_lines = lines[-50:]
            for line in lines[:-50]:
                if any(re.search(p, line, re.IGNORECASE) for p in ignore_patterns): continue
                if any(re.search(p, line, re.IGNORECASE) for p in critical_patterns): important_lines.append(line)
        if len(important_lines) > 200: important_lines = important_lines[-200:]
        full = "--- ERRORS ---\n" + "".join(important_lines) + "\n--- TAIL ---\n" + "".join(tail_lines)
        return full[:max_chars], None
    except Exception as e: return None, str(e)

# --- ROUTER UTAMA (UPDATED LENGKAP) ---
def router(prompt: str, client: KiranaClient, is_oneshot: bool = False):
    prompt_lower = prompt.lower().strip()

    # 1. Bypass State untuk Tools
    if prompt_lower in ["help", "bantuan", "?"]: console.print(get_help_panel()); return
    if prompt_lower in ["patroli", "cek pagi"]: run_patroli(client); return

    # 2. [UPDATE] Security Scan (Routing ke Handler Baru)
    if "cek keamanan" in prompt_lower or "analisa keamanan" in prompt_lower:
        match = re.search(r'(https?://[^\s]+)|([a-zA-Z0-9-]+\.[a-zA-Z0-9.-]+)', prompt)
        if match: handle_security_scan(match.group(0), client)
        else: console.print("[bold red]❌ Mana targetnya Fox?[/bold red]")
        return
    elif "cek web" in prompt_lower: # Webload scan (tetap sync)
        match = re.search(r'https?://[^\s]+', prompt)
        if match: handle_web_scan(match.group(0), client)
        else: console.print("[bold red]❌ Mana URL-nya Fox?[/bold red]")
        return

    # 3. Log Sentinel
    elif "cek log" in prompt_lower or "analisa log" in prompt_lower:
        handle_log_analysis(prompt, client); return

    # 4. System & Net Tools
    elif any(k in prompt_lower for k in ["cek system", "status system"]): run_system_check(prompt_lower); return
    elif any(k in prompt_lower for k in ["cek internet", "speedtest"]): run_netdiag(prompt_lower); return

    # 5. File Ops
    elif "cari file" in prompt_lower: run_file_search(prompt); return
    elif "analisa file" in prompt_lower: handle_file_analysis(prompt, client); return
    elif any(k in prompt_lower for k in ["buatin file", "bikin file"]): handle_file_creation(prompt, client); return
    elif any(k in prompt_lower for k in ["perbaiki file", "fix file"]): handle_file_fix(prompt, client); return

    # 6. Reminder & Memory
    elif any(k in prompt_lower for k in ["ingetin", "remind me"]): handle_add_reminder(prompt, client); return
    elif any(k in prompt_lower for k in ["cek reminder", "list reminder"]): list_reminders(); return
    elif any(k in prompt_lower for k in ["hapus reminder"]): clear_reminders(); return
    elif "ingat bahwa" in prompt_lower: 
        handle_memory_learn(re.sub(r"(ingat bahwa)\s*", "", prompt, flags=re.IGNORECASE).strip(), client); return
    elif "lupakan bahwa" in prompt_lower:
        handle_memory_forget(re.sub(r"(lupakan bahwa)\s*", "", prompt, flags=re.IGNORECASE).strip(), client); return

    # 7. Default Chat (With Memory)
    handle_chat_request(prompt, client, is_oneshot)

# --- NEW HANDLER: ASYNC SECURITY SCAN (POLLING) ---
def handle_security_scan(target: str, client: KiranaClient):
    console.print(f"[bold cyan]🛡️ Memulai Security Scan v5: {target}[/bold cyan]")
    console.print("[dim]⏳ Mengirim perintah ke Server (Async Mode)...[/dim]")
    
    # 1. Start Scan
    payload = {"target": target, "scan_type": "full"}
    start_resp = client.post_request("/api/v1/security/scan", payload)
    
    if "error" in start_resp:
        console.print(f"[bold red]❌ Gagal memulai scan:[/bold red] {start_resp['error']}")
        return

    # Cek apakah job_id (Async) atau result (Sync/Nmap)
    job_id = start_resp.get("job_id")
    if not job_id and "result" in start_resp:
         console.print(Markdown(start_resp["result"]))
         return

    if not job_id:
        console.print(f"[bold red]❌ Server tidak memberikan Job ID.[/bold red]")
        return

    console.print(f"✅ Job ID diterima: [yellow]{job_id}[/yellow]")
    console.print("☕ Silakan ngopi dulu Mas, Secator butuh waktu lama (bisa >10 menit)...")

    # 2. Polling Loop
    with console.status("[bold green]Sedang melakukan scanning & analisa (Polling)...[/bold green]", spinner="grenade") as status:
        while True:
            try:
                status_url = f"{client.base_url}/api/v1/security/status/{job_id}"
                resp = client.session.get(status_url, timeout=10)
                
                if resp.status_code == 200:
                    data = resp.json()
                    job_status = data.get("status")
                    
                    if job_status == "completed":
                        console.print("\n[bold green]✅ SCAN SELESAI![/bold green]")
                        console.print(Markdown(data.get("result", "")))
                        break
                    elif job_status == "failed":
                        console.print(f"\n[bold red]❌ SCAN GAGAL:[/bold red] {data.get('result')}")
                        break
                    else:
                        status.update(f"[bold yellow]Scanning berjalan... ({job_id})[/bold yellow]")
                        time.sleep(5)
                else:
                    time.sleep(5)
            except KeyboardInterrupt:
                console.print("\n[red]⛔ Polling dihentikan manual.[/red]")
                break
            except:
                time.sleep(5)

# --- HANDLER LAIN (Chat, File, Log, dll) ---
def handle_chat_request(prompt: str, client: KiranaClient, is_oneshot: bool = False):
    prompt_lower = prompt.lower()
    coding_triggers = ["script", "python", "code", "coding", "buatkan fungsi", "bikin kode", "html", "css", "rust"]
    target_role = "primary" if any(t in prompt_lower for t in coding_triggers) else "secondary"

    full_prompt_to_server = prompt
    history = []

    if is_oneshot:
        state = _load_cli_state()
        history = state.get("history", [])
        if history:
            context_str = "\n".join(history)
            full_prompt_to_server = f"[CONTEXT]:\n{context_str}\n\n[USER]: {prompt}"
            console.print(f"[dim]⚡ Mengingat konteks...[/dim]")

    with console.status("[bold yellow]Sedang berpikir...[/bold yellow]", spinner="dots"):
        payload = {"message": full_prompt_to_server, "role": target_role}
        response = client.post_request("/api/v1/chat/ask", payload)
    
    if "error" in response:
        console.print(f"[bold red]❌ Error:[/bold red] {response['error']}")
    else:
        reply = response.get("reply", "")
        console.print("")
        if target_role == "primary": console.print(f"[bold red]😈 Yayuk:[/bold red]")
        else: console.print(f"[bold blue]👩‍💼 Kirana:[/bold blue]")
        console.print(Markdown(reply))
        console.print("")
        
        if is_oneshot:
            history.append(f"User: {prompt}")
            history.append(f"AI: {reply}")
            _save_cli_state(history)

# (Sisanya Helper File Ops, Log Sentinel, Patroli samakan dengan versi sebelumnya)
# Agar code tidak terlalu panjang di sini, pastikan fungsi helper berikut ada:
# - handle_log_analysis
# - handle_file_creation
# - handle_file_analysis
# - handle_file_fix
# - run_patroli
# - handle_web_scan
# - handle_memory_learn
# - handle_memory_forget
# (Saya asumsikan Mas sudah punya helper ini dari diskusi Log Sentinel & File Ops sebelumnya)

# ... [PASTE SISA HELPER FUNCTION DISINI] ...
# Jika Mas butuh saya tuliskan ulang FULL code 100% dari atas sampai bawah (termasuk helper), bilang saja ya.

def handle_log_analysis(prompt, client):
    match = re.search(r"(cek log|analisa log|scan log)\s+(.+)", prompt, re.IGNORECASE)
    if not match: console.print("[red]❌ Format: 'cek log <path>'[/red]"); return
    path = match.group(2).strip()
    filtered, err = smart_filter_log(path)
    if err: console.print(f"[red]❌ Error: {err}[/red]"); return
    if len(filtered)<50: console.print("[green]✅ Log bersih.[/green]"); return
    payload = {"message": f"Analisa log:\n{filtered}", "role": "primary", "system_prompt": "You are Forensic Analyst."}
    with console.status("Analisa...", spinner="grenade"): resp = client.post_request("/api/v1/chat/ask", payload)
    if "error" in resp: console.print(f"[red]Error: {resp['error']}[/red]")
    else: console.print(Markdown(resp.get("reply", "")))

# --- Helper File Ops (Simplified) ---
def handle_file_creation(prompt, client):
    # (Logic sama seperti sebelumnya)
    pass # Isi dengan logic coding Yayuk

def handle_file_analysis(prompt, client):
    # (Logic sama seperti sebelumnya)
    pass

def handle_file_fix(prompt, client):
    # (Logic sama seperti sebelumnya)
    pass

def run_patroli(client):
    # (Logic sama seperti sebelumnya)
    pass

def handle_web_scan(url, client):
    # (Logic sama seperti sebelumnya)
    pass

def handle_memory_learn(text, client):
    client.post_request("/api/v1/memory/learn", {"text": text})
    console.print("[green]🧠 Tersimpan![/green]")

def handle_memory_forget(text, client):
    client.post_request("/api/v1/memory/forget", {"text": text})
    console.print("[green]🗑️ Dihapus![/green]")


def run_interactive_mode(client):
    console.print("[bold green]** KIRANA v5.0 (CLIENT) **[/bold green]")
    while True:
        try:
            user_input = input("Fox 🦊: ").strip()
            if not user_input: continue
            if user_input.lower() in ['exit', 'quit']: break
            router(user_input, client, is_oneshot=False)
        except KeyboardInterrupt: break
        except Exception as e: console.print(f"[red]Error: {e}[/red]")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("prompt", nargs="*")
    args = parser.parse_args()
    full_prompt = " ".join(args.prompt).strip()
    try: client = KiranaClient()
    except Exception as e: console.print(f"[red]FATAL: {e}[/red]"); sys.exit(1)
    if full_prompt: router(full_prompt, client, is_oneshot=True)
    else: run_interactive_mode(client)

if __name__ == "__main__": main()
