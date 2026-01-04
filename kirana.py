import sys
import argparse
import re
import time
import os
import json # [NEW] Butuh JSON buat simpan state
import psutil 
from rich.console import Console
from rich.markdown import Markdown

# Import Core
from src.core.client import KiranaClient
from src.core.help_text import get_help_panel

# Import Tools (Sama seperti sebelumnya)
from src.tools.system import run_system_check
from src.tools.netdiag import run_netdiag, run_command
from src.tools.reminder import handle_add_reminder, list_reminders, clear_reminders, _load_reminders
from src.tools.files import run_file_search 

console = Console()

# --- KONFIGURASI MEMORI PENDEK (ADAPTASI V4.5) ---
# Lokasi: ~/kirana/memory/cli_state.json
MEMORY_DIR = os.path.expanduser("~/kirana/memory")
STATE_FILE = os.path.join(MEMORY_DIR, "cli_state.json")
MAX_IDLE_SECONDS = 60  # 1 Menit Timeout
MAX_TURNS = 3          # Max 3 Percakapan sebelum reset (Saya naikkan dikit)

def _load_cli_state():
    """Membaca ingatan pendek (One-Shot Context)"""
    empty_state = {"history": [], "last_update": 0}
    
    if not os.path.exists(STATE_FILE): return empty_state
    
    try:
        with open(STATE_FILE, 'r') as f:
            state = json.load(f)
        
        # Cek Timeout (Apakah sudah lebih dari 60 detik?)
        now = time.time()
        if now - state.get("last_update", 0) > MAX_IDLE_SECONDS:
            return empty_state # Reset kalau dah lama
            
        return state
    except:
        return empty_state

def _save_cli_state(history):
    """Menyimpan ingatan pendek"""
    if not os.path.exists(MEMORY_DIR): os.makedirs(MEMORY_DIR)
    
    # Pruning (Jaga agar tidak kepanjangan)
    if len(history) > MAX_TURNS * 2: # *2 karena (User + AI)
        history = history[-(MAX_TURNS*2):]
        
    state = {
        "history": history,
        "last_update": time.time()
    }
    try:
        with open(STATE_FILE, 'w') as f:
            json.dump(state, f)
    except Exception as e:
        pass # Silent error, gak fatal

# --- HELPER LAIN (Code Cleaner, Log Sentinel) ---
# (Pastikan fungsi extract_clean_code dan smart_filter_log dari diskusi sebelumnya TETAP ADA disini)
# Saya persingkat biar fokus ke update memory
def extract_clean_code(text):
    pattern = r"```(?:\w+)?\n(.*?)```"
    match = re.search(pattern, text, re.DOTALL)
    if match: return match.group(1).strip()
    return text.replace("```python", "").replace("```bash", "").replace("```", "").strip()

# --- ROUTER UTAMA (UPDATED) ---
def router(prompt: str, client: KiranaClient, is_oneshot: bool = False):
    prompt_lower = prompt.lower().strip()

    # 1. Bypass State untuk Command "System/Tools"
    # Kita gak perlu ingat konteks kalau user cuma cek ping atau patroli
    if prompt_lower in ["help", "bantuan", "?"]: console.print(get_help_panel()); return
    if prompt_lower in ["patroli", "cek pagi"]: run_patroli(client); return
    
    # ... (Tools lain seperti cek log, cek system, file ops TETAP SAMA) ...
    # Pastikan logic routing tools (cek system, analisa file, dll) ada disini
    # Copy paste dari file sebelumnya, saya skip biar gak kepanjangan
    
    # --- HANDLING CHAT INTELLIGENCE (WITH MEMORY) ---
    # Ini logic baru untuk menangani Chat Biasa / Coding
    handle_chat_request(prompt, client, is_oneshot)


# --- HANDLER: CHAT REQUEST (UPDATED WITH STATE) ---
def handle_chat_request(prompt: str, client: KiranaClient, is_oneshot: bool = False):
    
    # 1. Tentukan Role (Persona)
    prompt_lower = prompt.lower()
    coding_triggers = ["script", "python", "code", "coding", "buatkan fungsi", "bikin kode", "html", "css", "rust"]
    target_role = "primary" if any(t in prompt_lower for t in coding_triggers) else "secondary"

    # 2. Kelola Ephemeral Context (Hanya jika One-Shot)
    full_prompt_to_server = prompt
    history = []
    
    if is_oneshot:
        state = _load_cli_state()
        history = state.get("history", [])
        
        if history:
            # Rangkai konteks untuk dikirim ke Server
            # Format: 
            # [Previous Chat]:
            # User: ...
            # AI: ...
            # [Current]: ...
            context_str = "\n".join(history)
            full_prompt_to_server = f"""
[CONTEXT DARI PERCAKAPAN SEBELUMNYA (CONTINUATION)]:
{context_str}

[USER REQUEST SAAT INI]:
{prompt}
"""
            console.print(f"[dim]⚡ Mengingat konteks {len(history)//2} percakapan terakhir...[/dim]")

    # 3. Kirim ke Server
    with console.status("[bold yellow]Sedang berpikir...[/bold yellow]", spinner="dots"):
        payload = {"message": full_prompt_to_server, "role": target_role}
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
        
        # 4. Simpan State Balik (Jika One-Shot)
        if is_oneshot:
            history.append(f"User: {prompt}")
            history.append(f"AI: {reply}")
            _save_cli_state(history)

# --- HELPER SYSTEM (SAMA SEPERTI SEBELUMNYA) ---
# ... (Pastikan fungsi run_patroli, handle_file_creation, dll tetap ada) ...
# ... (Saya skip biar hemat tempat, pakai kode sebelumnya) ...

def run_interactive_mode(client: KiranaClient):
    console.print("[bold green]** KIRANA v5.0 (CLIENT) **[/bold green]")
    console.print("(Ketik 'exit' buat udahan)\n")
    # Interactive mode gak butuh CLI State file, karena memori ada di variabel session server (jika ada)
    # atau kita bisa pakai list lokal sederhana.
    while True:
        try:
            user_input = input("Fox 🦊: ").strip()
            if not user_input: continue
            if user_input.lower() in ['exit', 'quit']: break
            # Interactive mode = False (State dikelola loop, atau server stateless)
            # Untuk simplifikasi v5, kita anggap interactive mode = one shot berulang
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
    
    if full_prompt:
        # ONE SHOT MODE -> AKTIFKAN EPHEMERAL MEMORY
        router(full_prompt, client, is_oneshot=True)
    else:
        # INTERACTIVE MODE
        run_interactive_mode(client)

if __name__ == "__main__": main()
