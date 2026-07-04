import sys
import argparse
import re
import time
import os
import json 
import psutil
import subprocess
import shutil
from rich.console import Console
from rich.markdown import Markdown

# Import Core
from src.core.client import KiranaClient
from src.core.help_text import get_help_panel

# Import Tools
from src.tools.system import run_system_check, handle_system_update
from src.tools.netdiag import run_netdiag, run_command
from src.tools.reminder import handle_add_reminder, list_reminders, clear_reminders, _load_reminders

# [FIX] IMPORT SEMUA FUNGSI FILE DARI SINI
from src.tools.files import (
    run_file_search, 
    handle_file_analysis, 
    handle_file_creation, 
    handle_file_fix
)

__version__ = "6.2.0"

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

# --- HELPER PATROLI (Jika belum ada di module lain, definisikan disini) ---
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

# --- HANDLER MEMORY (Helper Lokal) ---
def handle_memory_learn(text, client):
    client.post_request("/api/v1/memory/learn", {"text": text})
    console.print("[green]🧠 Tersimpan![/green]")

def handle_memory_forget(text, client):
    client.post_request("/api/v1/memory/forget", {"text": text})
    console.print("[green]🗑️ Dihapus![/green]")

def handle_client_update():
    console.print("[bold cyan]🔄 Melakukan pembaruan Kirana Client...[/bold cyan]")
    install_dir = os.path.expanduser("~/kirana")
    git_dir = os.path.join(install_dir, ".git")
    
    try:
        if os.path.exists(git_dir):
            # Run git pull
            res = subprocess.run(["git", "pull"], cwd=install_dir, capture_output=True, text=True)
            if res.returncode == 0:
                console.print("[green]✅ Kirana Client berhasil diperbarui via git pull![/green]")
                console.print(res.stdout)
            else:
                console.print(f"[bold red]❌ Gagal melakukan git pull:[/bold red] {res.stderr}")
        else:
            console.print("[yellow]⚠️  Folder ~/kirana tidak memiliki repositori Git (Instalasi Lokal).[/yellow]")
            console.print("[dim]Mengunduh kode terbaru dari GitHub...[/dim]")
            
            temp_dir = os.path.expanduser("~/kirana_temp")
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
            
            subprocess.run(["git", "clone", "https://github.com/ajobondon/kirana.git", temp_dir], check=True)
            
            # Copy all files except env/venv/git
            for item in os.listdir(temp_dir):
                if item in ['env', 'venv', '.git']:
                    continue
                s = os.path.join(temp_dir, item)
                d = os.path.join(install_dir, item)
                if os.path.isdir(s):
                    shutil.copytree(s, d, dirs_exist_ok=True)
                else:
                    shutil.copy2(s, d)
                    
            shutil.rmtree(temp_dir)
            console.print("[green]✅ Berkas Kirana Client berhasil diperbarui dari GitHub![/green]")
        
        # Re-install dependencies
        console.print("[dim]Memperbarui dependensi (pip)...[/dim]")
        pip_bin = os.path.join(install_dir, "env", "bin", "pip")
        subprocess.run([pip_bin, "install", "-r", "requirements.txt"], cwd=install_dir, check=True)
        console.print("[green]✅ Dependensi diperbarui.[/green]")
        
        # Reload bash/zsh shell for the user
        console.print("[bold yellow]🔔 PEMBARUAN SELESAI![/bold yellow]")
        console.print("Silakan jalankan kembali shell atau reload konfigurasi:")
        zshrc = os.path.expanduser("~/.zshrc")
        if os.path.exists(zshrc):
            console.print("[cyan]source ~/.zshrc[/cyan]")
        else:
            console.print("[cyan]source ~/.bashrc[/cyan]")
        
    except Exception as e:
        console.print(f"[bold red]❌ Gagal memperbarui Kirana Client:[/bold red] {e}")

# --- ROUTER UTAMA ---
def router(prompt: str, client: KiranaClient, is_oneshot: bool = False):
    prompt_lower = prompt.lower().strip()

    # 1. Bypass State untuk Tools Lokal
    if prompt_lower in ["help", "bantuan", "?"]: console.print(get_help_panel()); return
    if prompt_lower in ["patroli", "cek pagi"]: run_patroli(client); return
    if any(k in prompt_lower for k in ["update client", "upgrade client", "update kirana", "upgrade kirana"]):
        handle_client_update()
        return

    # 2. System & Net Tools (Client-side Local Tools)
    elif any(k in prompt_lower for k in ["upgrade system", "cek update", "update system"]):
        handle_system_update(prompt_lower)
        return

    elif any(k in prompt_lower for k in ["cek system", "status system", "info system"]):
        run_system_check(prompt_lower)
        return

    elif any(k in prompt_lower for k in ["cek internet", "speedtest"]): 
        run_netdiag(prompt_lower)
        return 

    elif "cari file" in prompt_lower: run_file_search(prompt); return

    # 3. Local Reminder
    elif any(k in prompt_lower for k in ["ingetin", "remind me"]): handle_add_reminder(prompt, client); return
    elif any(k in prompt_lower for k in ["cek reminder", "list reminder"]): list_reminders(); return
    elif any(k in prompt_lower for k in ["hapus reminder"]): clear_reminders(); return

    # 4. Aksi lainnya (VAPT, RAG, Memory, Pembuatan File, Chat) dikirim ke Server Agent Loop
    handle_chat_request(prompt, client, is_oneshot)

# --- HANDLER CHAT UTAMA ---
def handle_chat_request(prompt: str, client: KiranaClient, is_oneshot: bool = False):
    full_prompt_to_server = prompt
    history = []

    if is_oneshot:
        state = _load_cli_state()
        history = state.get("history", [])
        if history:
            context_str = "\n".join(history)
            full_prompt_to_server = f"[CONTEXT]:\n{context_str}\n\n[USER]: {prompt}"
            console.print(f"[dim]⚡ Mengingat konteks...[/dim]")

    # Klasifikasi apakah butuh proses asinkron (proses yang lama)
    coding_triggers = ["script", "code", "bypass", "exploit", "secator", "nmap", "vapt", "coding", "buatkan", "bikin", "python", "html", "css", "rust", "c++", "bash"]
    log_triggers = ["error", "log", "syslog", "journalctl", "cek log", "analisa log"]
    msg_lower = prompt.lower()
    is_long_process = any(t in msg_lower for t in coding_triggers) or any(t in msg_lower for t in log_triggers)

    response = {}
    if is_long_process:
        # Gunakan Async Polling untuk mencegah Cloudflare 524 Timeout
        with console.status("[bold yellow]Sedang memproses (asinkron)...[/bold yellow]", spinner="dots"):
            payload = {"message": full_prompt_to_server}
            start_resp = client.post_request("/api/v1/chat/ask_async", payload)
            
            if "error" in start_resp:
                response = start_resp
            else:
                job_id = start_resp.get("job_id")
                while True:
                    try:
                        status_url = f"/api/v1/chat/status/{job_id}"
                        resp = client.session.get(f"{client.base_url}{status_url}", timeout=10)
                        if resp.status_code == 200:
                            data = resp.json()
                            job_status = data.get("status")
                            if job_status == "completed":
                                response = data
                                break
                            elif job_status == "failed":
                                response = {"error": f"Proses gagal: {data.get('error')}"}
                                break
                        time.sleep(2)
                    except KeyboardInterrupt:
                        console.print("\n[red]⛔ Dibatalkan user.[/red]")
                        return
                    except Exception as e:
                        time.sleep(2)
    else:
        # Gunakan koneksi sinkron biasa untuk obrolan ringan (cepat)
        with console.status("[bold yellow]Sedang berpikir...[/bold yellow]", spinner="dots"):
            payload = {"message": full_prompt_to_server}
            response = client.post_request("/api/v1/chat/ask", payload)
    
    if "error" in response:
        console.print(f"[bold red]❌ Error:[/bold red] {response['error']}")
    else:
        reply = response.get("reply", "")
        persona = response.get("persona", "").lower()
        console.print("")
        if "yayuk" in persona:
            console.print(f"[bold red]😈 Yayuk:[/bold red]")
        else:
            console.print(f"[bold blue]👩‍💼 Kirana:[/bold blue]")
        console.print(Markdown(reply))
        console.print("")
        
        if is_oneshot:
            history.append(f"User: {prompt}")
            history.append(f"AI: {reply}")
            _save_cli_state(history)

def run_interactive_mode(client: KiranaClient):
    console.print(f"[bold green]** KIRANA v{__version__} (CLIENT) **[/bold green]")
    console.print(f"[dim]Build: Nexus Release[/dim]")
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
    parser.add_argument("--version", action="store_true", help="Cek versi Kirana")
    args = parser.parse_args()
    # Cek flag version
    if args.version:
        console.print(f"Kirana Client v{__version__}")
        sys.exit(0)
    full_prompt = " ".join(args.prompt).strip()
    try: client = KiranaClient()
    except Exception as e: console.print(f"[red]FATAL: {e}[/red]"); sys.exit(1)
    if full_prompt: router(full_prompt, client, is_oneshot=True)
    else: run_interactive_mode(client)

if __name__ == "__main__": main()
