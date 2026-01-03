import os
import sys
import re
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from dotenv import load_dotenv

# Load config agar bisa baca WORKSPACE_DIR
load_dotenv()

console = Console()

# Tentukan Folder Kerja (Default ke ~/kirana/workspace jika di .env kosong)
WORKSPACE_DIR = os.getenv("WORKSPACE_DIR", os.path.expanduser("~/kirana/workspace"))

# --- HELPER: Code Extractor ---
def extract_clean_code(text):
    """Membersihkan output LLM agar hanya mengambil blok kode."""
    pattern = r"```(?:\w+)?\n(.*?)```"
    match = re.search(pattern, text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return text.replace("```python", "").replace("```bash", "").replace("```", "").strip()

# --- 1. SEARCH LOCAL FILES ---
def run_file_search(prompt):
    """Mencari file berdasarkan nama atau konten di laptop"""
    mode = 'content' if "cari kata" in prompt or "cari konten" in prompt else 'name'
    trigger = "cari kata" if mode == 'content' else "cari file"
    
    try:
        raw_query = re.split(trigger, prompt, flags=re.IGNORECASE)[1].strip()
    except:
        console.print("[bold red]❌ Format salah. Contoh: 'cari file password.txt'[/bold red]")
        return

    query = raw_query
    search_path = os.getcwd() 

    if " di " in raw_query:
        parts = raw_query.split(" di ", 1)
        query = parts[0].strip()
        path_arg = parts[1].strip()
        if os.path.exists(path_arg):
            search_path = path_arg
        elif os.path.exists(os.path.expanduser(path_arg)):
             search_path = os.path.expanduser(path_arg)

    console.print(f"[bold cyan]🔎 Mencari '{query}' di: {search_path} (Mode: {mode.upper()})...[/bold cyan]")
    
    found_files = []
    SKIP_DIRS = {'.git', '__pycache__', 'node_modules', 'venv', 'env', '.idea', '.vscode', 'dist'}

    try:
        for root, dirs, files in os.walk(search_path):
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith('.')]
            
            for file in files:
                filepath = os.path.join(root, file)
                
                if mode == 'name' and query.lower() in file.lower():
                    console.print(f"📄 Found: [green]{filepath}[/green]")
                    found_files.append(filepath)
                
                elif mode == 'content':
                    if os.path.getsize(filepath) < 1024 * 1024: 
                        try:
                            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                                if query.lower() in f.read().lower():
                                    console.print(f"📝 Found in: [green]{filepath}[/green]")
                                    found_files.append(filepath)
                        except: pass

    except Exception as e:
        console.print(f"[red]❌ Error search: {e}[/red]")

    if not found_files:
        console.print("[yellow]📭 Tidak ditemukan.[/yellow]")
    else:
        console.print(f"\n[bold green]✅ Total: {len(found_files)} file ditemukan.[/bold green]")


# --- 2. ANALYZE LOCAL FILE (Hybrid) ---
def handle_file_analysis(prompt, client):
    match = re.search(r"analisa file\s+(.+)", prompt, re.IGNORECASE)
    if not match:
        console.print("[red]❌ Sebutkan path filenya. Contoh: 'analisa file script.py'[/red]")
        return

    path = match.group(1).strip()
    if not os.path.exists(path):
        console.print(f"[red]❌ File tidak ditemukan: {path}[/red]")
        return

    try:
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            if len(content) > 10000:
                content = content[:10000] + "\n...[TRUNCATED]..."
    except Exception as e:
        console.print(f"[red]❌ Gagal baca file: {e}[/red]")
        return

    console.print(f"[cyan]🚀 Mengirim konten '{os.path.basename(path)}' ke Server Kirana...[/cyan]")
    
    system_prompt = "You are a Senior Code Reviewer & Security Analyst. Analyze this file content. Explain bugs, security risks, and improvements."
    payload = {
        "message": f"Analyze this file:\n\n{content}",
        "role": "secondary",
        "system_prompt": system_prompt
    }
    
    with console.status("[bold yellow]Server sedang menganalisa file...[/bold yellow]", spinner="dots"):
        response = client.post_request("/api/v1/chat/ask", payload)

    if "error" in response:
        console.print(f"[red]❌ Server Error: {response['error']}[/red]")
    else:
        console.print(Markdown(response.get("reply", "")))


# --- 3. CREATE FILE (Hybrid) - [FIXED PATH] ---
def handle_file_creation(prompt, client):
    match = re.search(r"(buatin file|buatkan file|bikin file)\s+(\S+)\s+(?:tentang|soal|for|isinya)\s+(.+)", prompt, re.IGNORECASE)
    if not match:
        console.print("[red]❌ Format: 'buatin file <nama> tentang <deskripsi>'[/red]")
        return

    fname = match.group(2).strip()
    desc = match.group(3).strip()
    
    # [FIX] Pastikan hanya nama file (tanpa path aneh-aneh)
    fname = os.path.basename(fname)
    
    # [FIX] Tentukan Full Path ke Workspace
    full_path = os.path.join(WORKSPACE_DIR, fname)
    
    # Buat folder workspace jika belum ada
    if not os.path.exists(WORKSPACE_DIR):
        try:
            os.makedirs(WORKSPACE_DIR)
        except OSError as e:
            console.print(f"[red]❌ Gagal membuat folder workspace: {e}[/red]")
            return

    console.print(f"[cyan]🚀 Meminta Server membuatkan code untuk '{fname}'...[/cyan]")
    
    system_prompt = "You are an Expert Developer. Output ONLY the code block. No markdown wrapper needed if possible, or just standard markdown code block."
    payload = {
        "message": f"Create code for file '{fname}'. Requirement: {desc}. OUTPUT CODE ONLY.",
        "role": "primary", 
        "system_prompt": system_prompt
    }

    with console.status("[bold yellow]Server sedang coding...[/bold yellow]", spinner="dots"):
        response = client.post_request("/api/v1/chat/ask", payload)

    if "error" in response:
        console.print(f"[red]❌ Server Error: {response['error']}[/red]")
    else:
        raw_reply = response.get("reply", "")
        code = extract_clean_code(raw_reply)
        
        if not code:
            console.print("[red]❌ Gagal: AI tidak menghasilkan kode yang valid.[/red]")
            return

        try:
            # [FIX] Tulis ke full_path (Workspace)
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(code)
            
            # [FIX] Info lokasi file yang jelas
            console.print(f"[bold green]✅ File berhasil dibuat![/bold green]")
            console.print(f"📂 Lokasi: [cyan]{full_path}[/cyan]")
            console.print(Panel(code[:200] + "\n...", title=f"Preview ({fname})", border_style="green"))
            
        except Exception as e:
            console.print(f"[red]❌ Gagal menulis file: {e}[/red]")


# --- 4. FIX/HEAL FILE (Hybrid) ---
def handle_file_fix(prompt, client):
    match = re.search(r"(perbaiki|benerin|fix|refactor)\s+file\s+(.+)", prompt, re.IGNORECASE)
    if not match:
         console.print("[red]❌ Format: 'perbaiki file <nama_file>'[/red]")
         return

    path = match.group(2).strip()
    # Support relative path atau full path
    if not os.path.exists(path):
        # Coba cari di workspace juga kalau di current dir gak ada
        workspace_path = os.path.join(WORKSPACE_DIR, path)
        if os.path.exists(workspace_path):
            path = workspace_path
        else:
            console.print(f"[red]❌ File tidak ditemukan: {path}[/red]")
            return

    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        console.print(f"[red]❌ Gagal baca file: {e}[/red]")
        return

    console.print(f"[cyan]🚑 Mengirim '{os.path.basename(path)}' ke RS Server Kirana...[/cyan]")
    
    payload = {
        "message": f"Fix bugs/errors in this code. Output ONLY the fixed code:\n\n{content}",
        "role": "primary",
        "system_prompt": "You are an Expert Developer. Fix the code. Output ONLY the functional code block."
    }

    with console.status("[bold yellow]Server sedang memperbaiki kode...[/bold yellow]", spinner="dots"):
        response = client.post_request("/api/v1/chat/ask", payload)
        
    if "error" in response:
        console.print(f"[red]❌ Server Error: {response['error']}[/red]")
    else:
        fixed_code = extract_clean_code(response.get("reply", ""))
        
        # Backup
        bak_path = path + ".bak"
        try:
            import shutil
            shutil.copy(path, bak_path)
            with open(path, 'w', encoding='utf-8') as f:
                f.write(fixed_code)
            console.print(f"[bold green]✅ File healed![/bold green]")
            console.print(f"📂 Lokasi: [cyan]{path}[/cyan]")
            console.print(f"🛡️ Backup: [dim]{bak_path}[/dim]")
        except Exception as e:
            console.print(f"[red]❌ Gagal save file: {e}[/red]")
