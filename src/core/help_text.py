from rich.panel import Panel
from rich.align import Align

def get_help_panel():
    """Mengembalikan Panel Rich berisi menu bantuan legacy v4.5"""
    
    help_content = """
[bold yellow]🔥 MENU PAHALA & DOSA KIRANA 🔥[/bold yellow]
===================================================

[bold cyan]💬 INTERACTIVE MODE:[/bold cyan]
   `kirana` (Masuk mode chat loop)

[bold cyan]🧠 KONSULTASI & RAG:[/bold cyan]
   `kirana apa itu XSS`
   `kirana cara install secator`
   `kirana cari berita <terserah_apa>`

[bold cyan]🌐 WEB & OSINT:[/bold cyan]
   `kirana cari info <topik>`

[bold cyan]📂 FILE OPERATIONS:[/bold cyan]
   `kirana analisa file <nama_file>`
   `kirana buatin file <file.ext> tentang <deskripsi>`
   `kirana perbaiki/benerin file <nama_skrip>`

[bold cyan]🛠️ SYSTEM TOOLS:[/bold cyan]
   `kirana cek internet`
   `kirana cek/update system`
   `kirana cari file <nama_file> di <path>`
   `kirana cek log/analisa log <nama_logfile>`

[bold cyan]🧠 MEMORY & LEARNING:[/bold cyan]
   `kirana ingat bahwa/ini <sesuatu>`
   `kirana lupakan bahwa <sesuatu>`

[bold cyan]🛡️ SISKAMLING & SECURITY:[/bold cyan]
   `kirana patroli`
   `kirana cek keamanan domain/url <target>`
   `kirana analisa web/cek web <url>`

[bold cyan]⏰ REMINDER & ASSISTANT:[/bold cyan]
   `kirana ingetin gue <pesan> <waktu>`
   `kirana cek reminder`
   `kirana hapus semua reminder`
"""
    return Panel(
        Align.left(help_content),
        title="[bold green]Kirana Help [/bold green]",
        subtitle="Kirana.AI",
        border_style="green"
    )
