from rich.panel import Panel
from rich.align import Align


def get_help_panel():
    """Mengembalikan Panel Rich berisi bantuan arsitektur Swarm Kirana v8.0.0 (MATRIX)"""
    
    help_content = """
[bold yellow]🦊 KIRANA v8.0.0 (MATRIX) - 5 SWARM AGENTS EDITION 🦊[/bold yellow]
============================================================

[bold red]🧠 5-AGENT STANDBY SWARM ROSTER (Server-side):[/bold red]
   • [bold blue]Kirana (Blue Team - 😇):[/bold blue] Blue Team Lead, CISO Advisor, & Default Analyst (`kimi-k2.6:cloud`).
   • [bold red]Yayuk (Red Team - 😈):[/bold red] Red Team SecOps Specialist & Exploit Expert (`kimi-k2.7-code:cloud`).
   • [bold yellow]Gembul (Code Architect - 😸):[/bold yellow] Software Engineering & Code Architecture (`qwen3.5:397b-cloud`).
   • [bold cyan]Mei (SecOps Auditor - 😺):[/bold cyan] Cyber Defense Audit & Compliance (`glm-5.2:cloud`).
   • [bold green]Udin (Casual Chat - 😽):[/bold green] Daily Conversational Assistant (`gemma4:31b-cloud`).
   • [bold magenta]Flex-Position Keyword Trigger:[/bold magenta] Sebut nama agent di mana saja dalam prompt untuk mengarahkan rute.
   • [bold yellow]Subtle Identity:[/bold yellow] Ditandai dengan emoji resmi masing-masing agent di akhir jawaban.

[bold green]🔌 DYNAMIC SKILLS (OpenClaw Compatible):[/bold green]
   • Skill tersimpan dinamis di server: `workspaces/{client_id}/skills/`
   • Tambah skill instan dengan menyalin folder skill (misal: `tavily`, `weather`).
   • Minta Kirana/Yayuk membuat skill baru secara langsung melalui chat:
     `kirana buatin skill geolocation untuk cek lokasi IP`

[bold cyan]🧠 WORKSPACE & MEMORY ISOLATION:[/bold cyan]
   • Konfigurasi (`BOOTSTRAP.md`, `SOUL.md`), RAG DB, dan sesi obrolan
     terisolasi secara otomatis berdasarkan `CLIENT_ID` di remote server.
   • Simpan ingatan RAG lokal: `kirana ingat bahwa [informasi]`
   • Hapus ingatan RAG lokal:  `kirana lupakan bahwa [informasi]`

[bold magenta]💻 LOCAL UTILITIES (Client-side / Laptop):[/bold magenta]
   • `kirana cek system`    (Status CPU/RAM laptop)
   • `kirana cek internet`  (Speedtest koneksi lokal)
   • `kirana cari file [nama] di [path]` (Cari berkas lokal)
   • `kirana update client` (Perbarui kode client dari GitHub)


[bold yellow]⏰ LOCAL REMINDERS (Client-side):[/bold yellow]
   • `kirana ingetin gue [pesan] [waktu]` (misal: in 10 mins)
   • `kirana cek reminder` (Lihat pengingat aktif)
   • `kirana hapus semua reminder` (Bersihkan pengingat)
"""
    return Panel(
        Align.left(help_content),
        title="[bold green] Kirana Help [/bold green]",
        subtitle="Kirana AI Ecosystem",
        border_style="green"
    )

