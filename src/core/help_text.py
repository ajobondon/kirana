from rich.panel import Panel
from rich.align import Align


def get_help_panel():
    """Mengembalikan Panel Rich berisi bantuan arsitektur baru Kirana v6.2.0"""
    
    help_content = """
[bold yellow]🦊 KIRANA NEXUS v6.2.0 (DYNAMIC AGENTS & WORKSPACES) 🦊[/bold yellow]
===================================================

[bold red]🎭 DUAL PERSONA & AUTO-ROUTING (Server-side):[/bold red]
   • [bold red]Yayuk (Red Team):[/bold red] Untuk tugas coding, exploit, dan VAPT.
     [dim](Berjalan di MODEL_PRIMARY dengan suhu presisi)[/dim]
   • [bold blue]Kirana (Blue Team):[/bold blue] Untuk chat umum, log forensics, dan RAG.
     [dim](Berjalan di MODEL_SECONDARY/PRIMARY dengan suhu stabil)[/dim]

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

