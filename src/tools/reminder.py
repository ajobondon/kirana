import os
import json
import datetime
import re
from rich.console import Console
from rich.table import Table

console = Console()
# Simpan di folder memory lokal
REMINDER_FILE = os.path.expanduser("~/kirana/memory/reminders.json")

def _load_reminders():
    if not os.path.exists(REMINDER_FILE): return []
    try:
        with open(REMINDER_FILE, 'r') as f: return json.load(f)
    except: return []

def _save_reminders(data):
    os.makedirs(os.path.dirname(REMINDER_FILE), exist_ok=True)
    with open(REMINDER_FILE, 'w') as f: json.dump(data, f, indent=2)

def handle_add_reminder(prompt, client):
    """
    Kirim prompt ke Server untuk diparsing, lalu simpan JSON-nya di lokal.
    """
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Minta otak Server mem-parsing waktu
    system_prompt = f"""
    Current Time: {now}
    Task: Extract reminder target time and message from user input.
    Output Format: JSON ONLY with keys 'target_time' (YYYY-MM-DD HH:MM:SS) and 'message'.
    Calculate 'target_time' relative to Current Time.
    """
    
    payload = {
        "message": prompt,
        "role": "secondary", # Gemma cukup pinter buat ini
        "system_prompt": system_prompt
    }

    console.print("[cyan]⏰ Sedang mencatat jadwal...[/cyan]")
    
    try:
        response = client.post_request("/api/v1/chat/ask", payload, timeout=10)
        
        if "error" in response:
            console.print(f"[red]❌ Server Gagal Parsing: {response['error']}[/red]")
            return

        raw_reply = response.get("reply", "")
        # Bersihkan markdown json
        clean_json = raw_reply.replace("```json", "").replace("```", "").strip()
        
        data = json.loads(clean_json)
        target_time = data.get('target_time')
        msg = data.get('message')
        
        # Validasi sederhana
        if not target_time or not msg:
            raise ValueError("Incomplete data")

        # Simpan Lokal
        reminders = _load_reminders()
        reminders.append({
            "time": target_time,
            "message": msg,
            "created_at": now
        })
        _save_reminders(reminders)
        
        console.print(f"[bold green]✅ Reminder Diset![/bold green]")
        console.print(f"🕒 Waktu: {target_time}")
        console.print(f"📝 Pesan: {msg}")

    except Exception as e:
        console.print(f"[red]❌ Gagal set reminder: {e}. Coba format: 'ingetin gue makan jam 18:00'[/red]")

def list_reminders():
    reminders = _load_reminders()
    if not reminders:
        console.print("[yellow]📭 Tidak ada reminder aktif.[/yellow]")
        return

    table = Table(title="📅 Jadwal Reminder Saya")
    table.add_column("Waktu", style="cyan")
    table.add_column("Pesan", style="magenta")

    for r in reminders:
        table.add_row(r['time'], r['message'])
    
    console.print(table)

def clear_reminders():
    if os.path.exists(REMINDER_FILE):
        os.remove(REMINDER_FILE)
        console.print("[green]🗑️ Semua reminder dihapus.[/green]")
    else:
        console.print("[yellow]📭 Sudah kosong.[/yellow]")
