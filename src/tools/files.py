import os
import sys
import re
import time
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from dotenv import load_dotenv

# Load config agar bisa baca WORKSPACE_DIR
load_dotenv()

console = Console()

# Tentukan Folder Kerja (Default ke ~/kirana/workspace jika di .env kosong)
WORKSPACE_DIR = os.getenv("WORKSPACE_DIR", os.path.expanduser("~/kirana/workspace"))

# --- HELPER: Code Extractor (EXISTING - TIDAK DIUBAH) ---
def extract_clean_code(text):
    """Membersihkan output LLM agar hanya mengambil blok kode."""
    pattern = r"```(?:\w+)?\n(.*?)```"
    match = re.search(pattern, text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return text.replace("```python", "").replace("```bash", "").replace("```", "").strip()


# --- 1. SEARCH LOCAL FILES (EXISTING - TIDAK DIUBAH) ---
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


# --- 2. CREATE FILE (EXISTING - TIDAK DIUBAH) ---
def handle_file_creation(prompt, client):
    match = re.search(r"(buatin file|buatkan file|bikin file|create file)\s+(\S+)\s+(?:tentang|soal|for|isinya)\s+(.+)", prompt, re.IGNORECASE)
    
    if not match:
        console.print("[red]❌ Format: 'buatin file <nama> tentang <deskripsi>'[/red]")
        return

    fname = match.group(2).strip()
    desc = match.group(3).strip()
    
    # Pastikan hanya nama file
    fname = os.path.basename(fname)
    
    # Tentukan Full Path ke Workspace
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
            # Tulis ke full_path (Workspace)
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(code)
            
            # Info lokasi file yang jelas
            console.print(f"[bold green]✅ File berhasil dibuat![/bold green]")
            console.print(f"📂 Lokasi: [cyan]{full_path}[/cyan]")
            console.print(Panel(code[:200] + "\n...", title=f"Preview ({fname})", border_style="green"))
            
        except Exception as e:
            console.print(f"[red]❌ Gagal menulis file: {e}[/red]")


# --- 3. ANALYZE LOCAL FILE (UPDATED: ASYNC POLLING) ---
def handle_file_analysis(prompt, client):
    # Regex baru: Menangkap Filename (path) DAN Instruksi Opsional
    match = re.search(r"analisa file\s+(\S+)(?:\s+(.+))?", prompt, re.IGNORECASE)
    if not match:
        console.print("[red]❌ Sebutkan path filenya. Contoh: 'analisa file script.py'[/red]")
        return

    path = match.group(1).strip()
    
    # [UPDATE] Default instruction yang lebih kuat & berbahasa Indonesia
    default_instr = "Analisa kode ini secara lengkap. Jelaskan fungsi, bug, dan keamanannya dalam Bahasa Indonesia."
    instruction = match.group(2).strip() if match.group(2) else default_instr

    if not os.path.exists(path):
        console.print(f"[red]❌ File tidak ditemukan: {path}[/red]")
        return

    try:
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            # [NOTE]: Truncate logic saya hapus agar server yang handle lewat prompt slice
    except Exception as e:
        console.print(f"[red]❌ Gagal baca file: {e}[/red]")
        return

    #console.print(f"[cyan]🚀 Mengirim konten '{os.path.basename(path)}' ke Server Kirana (Async Mode)...[/cyan]")
    
    # [UPDATE] Hit endpoint ASYNC baru
    payload = {
        "filename": os.path.basename(path),
        "content": content,
        "instruction": instruction
    }
    
    start_resp = client.post_request("/api/v1/files/analyze", payload)

    if "error" in start_resp:
        console.print(f"[red]❌ Gagal memulai analisa: {start_resp['error']}[/red]")
        return

    job_id = start_resp.get("job_id")
    #console.print(f"✅ Job ID: [yellow]{job_id}[/yellow]. Menunggu Kirana mikir...")

    # [UPDATE] Polling Loop (Anti-Timeout)
    with console.status("[bold blue]👩‍💼 Kirana sedang menganalisa file...[/bold blue]", spinner="dots") as status:
        while True:
            try:
                # Cek status
                status_url = f"{client.base_url}/api/v1/files/status/{job_id}"
                resp = client.session.get(status_url, timeout=10)
                
                if resp.status_code == 200:
                    data = resp.json()
                    job_status = data.get("status")
                    
                    if job_status == "completed":
                        console.print("\n[bold blue]👩‍💼 Laporan Analisa Kirana:[/bold blue]")
                        console.print(Markdown(data.get("result", "")))
                        break
                    elif job_status == "failed":
                        console.print(f"\n[red]❌ Analisa Gagal: {data.get('result')}[/red]")
                        break
                    else:
                        time.sleep(3) # Tunggu 3 detik
                else:
                    time.sleep(3)
            except KeyboardInterrupt:
                console.print("\n[red]⛔ Dibatalkan user.[/red]")
                break
            except:
                time.sleep(3)


# --- 4. FIX/HEAL FILE (UPDATED: ASYNC POLLING) ---
def handle_file_fix(prompt, client):
    match = re.search(r"(perbaiki|benerin|fix|refactor)\s+file\s+(\S+)(?:\s+(.+))?", prompt, re.IGNORECASE)
    if not match:
         console.print("[red]❌ Format: 'perbaiki file <nama_file>'[/red]")
         return

    path = match.group(2).strip()
    instruction = match.group(3).strip() if match.group(3) else ""

    # Support relative path atau full path
    if not os.path.exists(path):
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

    #console.print(f"[cyan]🚑 Mengirim '{os.path.basename(path)}' ke RS Server Kirana (Async Mode)...[/cyan]")
    
    # [UPDATE] Hit endpoint ASYNC baru
    payload = {
        "filename": os.path.basename(path),
        "content": content,
        "instruction": instruction
    }

    start_resp = client.post_request("/api/v1/files/fix", payload)
    
    if "error" in start_resp:
        console.print(f"[red]❌ Gagal memulai perbaikan: {start_resp['error']}[/red]")
        return

    job_id = start_resp.get("job_id")
    #console.print(f"✅ Job ID: [yellow]{job_id}[/yellow]. Yayuk mulai coding...")

    # [UPDATE] Polling Loop (Anti-Timeout)
    with console.status("[bold red]😈 Yayuk sedang mengetik kode...[/bold red]", spinner="bouncingBall") as status:
        while True:
            try:
                status_url = f"{client.base_url}/api/v1/files/status/{job_id}"
                resp = client.session.get(status_url, timeout=10)
                
                if resp.status_code == 200:
                    data = resp.json()
                    job_status = data.get("status")
                    
                    if job_status == "completed":
                        raw_result = data.get("result", "")
                        fixed_code = extract_clean_code(raw_result)
                        
                        if not fixed_code:
                            console.print("[red]❌ Yayuk tidak mengembalikan kode valid.[/red]")
                            break
                        
                        # Simpan ke Workspace (SAFE MODE) - Tidak menimpa file asli langsung
                        fname = os.path.basename(path)
                        if not os.path.exists(WORKSPACE_DIR): os.makedirs(WORKSPACE_DIR)
                        save_path = os.path.join(WORKSPACE_DIR, f"fixed_{fname}")
                        
                        try:
                            with open(save_path, 'w', encoding='utf-8') as f:
                                f.write(fixed_code)
                                
                            console.print("\n[bold green]✅ OPERASI BERHASIL![/bold green]")
                            console.print(f"📂 File hasil perbaikan disimpan di: [cyan]{save_path}[/cyan]")
                            console.print("[dim](Silakan review sebelum ditimpa ke file asli)[/dim]")
                        except Exception as e:
                             console.print(f"[red]❌ Gagal menyimpan file: {e}[/red]")
                        break
                        
                    elif job_status == "failed":
                        console.print(f"\n[red]❌ Perbaikan Gagal: {data.get('result')}[/red]")
                        break
                    else:
                        time.sleep(3)
                else:
                    time.sleep(3)
            except KeyboardInterrupt:
                console.print("\n[red]⛔ Dibatalkan user.[/red]")
                break
            except:
                time.sleep(3)
