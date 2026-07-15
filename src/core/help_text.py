from rich.panel import Panel
from rich.align import Align


def get_help_panel():
    """Mengembalikan Panel Rich berisi bantuan arsitektur Swarm Kirana v7.0.0 (PIXEL)"""
    
    help_content = """
[bold yellow]🦊 KIRANA v7 (PIXEL) - SWARM AI EDITION 🦊[/bold yellow]
===================================================

[bold red]🧠 SWARM AI & DYNAMIC HAND-OFF (Server-side):[/bold red]
   • [bold blue]Kirana (Blue Team - 😇):[/bold blue] Untuk tugas defensif, analisis log, mitigasi, RAG, dan obrolan umum.
   • [bold red]Yayuk (Red Team - 😈):[/bold red] Untuk tugas coding/scripting, eksploitasi, bypass firewall, dan VAPT.
   • [bold green]Dynamic Transition:[/bold green] Rute berpindah secara semantis dan dinamis menggunakan transfer tools sesuai konteks perintah Anda.
   • [bold yellow]Subtle Identity:[/bold yellow] Ditandai dengan emoji di akhir kalimat (😇 untuk Kirana, 😈 untuk Yayuk).

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

