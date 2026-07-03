# Kirana Project - Agent Rules & Knowledge Base (v6.1.0)

Dokumen ini berisi panduan, aturan arsitektur, dan ringkasan riwayat integrasi agar agen AI (seperti Antigravity/Kirana) yang bekerja di workspace ini di masa mendatang memahami status proyek dan menjaga konsistensi kode.

---

## 📌 Identitas Proyek & Standar Versi
1. **Nama Persona AI:** **Kirana** (Blue Team) & **Yayuk** (Red Team).
2. **Standar Versi:** Menggunakan **Semantic Versioning (SemVer)** dengan format `Major.Minor.Patch` (saat ini **`v6.1.0`**).
   * **Major:** Perubahan arsitektur besar.
   * **Minor:** Fitur/fungsi baru (misal: integrasi platform baru).
   * **Patch:** Perbaikan bug/keamanan.
3. **Penyelarasan Versi:** Selalu pastikan penomoran versi di `kirana-server` (app/main.py, app/core/config.py, README.md, dan systemd services) sinkron dengan `kirana` (client/kirana.py, install.py, src/core/client.py).

---

## 💬 WhatsApp Integration (kirana-wa)
1. **Teknologi:** Node.js + `@whiskeysockets/baileys` (Headless/Soket murni tanpa Puppeteer untuk menghemat RAM server).
2. **Lokasi Deployment:** `/home/erwan/kirana-server/kirana-wa/` di server remote `ihome`.
3. **Service Systemd:** Berjalan di latar belakang server remote sebagai **`kirana-wa.service`** (dikelola via `systemctl restart kirana-wa`).
4. **Otentikasi:** Menggunakan metode **Pairing Code** via nomor telepon utama (`62817170582`). Kredensial sesi disimpan di `/home/erwan/kirana-server/data/wa-session`.
5. **Keamanan & Whitelist:**
   * Nomor WhatsApp pengirim yang diizinkan wajib didaftarkan di variabel `ALLOWED_WHATSAPP_NUMBERS` pada `.env`.
   * **LID (Linked Identity Database) Support:** WhatsApp menggunakan format ID baru bertipe `@lid` untuk privasi (misal: `15543503437837`). ID privat LID ini wajib didaftarkan di whitelist `.env` agar bot bersedia merespon.
6. **Local Help Menu:** Memotong input lokal (`help`, `/help`, `bantuan`, `menu`) untuk langsung dibalas oleh Node.js client guna menghemat token LLM.

---

## 📁 Workspace Isolation & Session Management
1. **Skenario B (Workspace per Nomor):** 
   * Jembatan WhatsApp mengirimkan nomor HP / LID pengirim secara dinamis sebagai header `X-Client-ID` ke server utama.
   * Setiap nomor mendapatkan folder ruang kerja terisolasi di `/home/erwan/kirana-server/workspaces/<nomor_atau_LID>/`.
   * Nomor-nomor tersebut wajib didaftarkan dalam `ALLOWED_CLIENT_IDS` pada `.env` server utama FastAPI agar tidak terblokir (403 Forbidden).
2. **Reset Sesi:** 
   * Pengguna dapat mengirim pesan **`reset sesi`**, **`hapus sesi`**, atau **`/reset`** via WhatsApp.
   * Logika jembatan akan menghapus file `sessions/default.json` milik nomor bersangkutan di server secara instan.
3. **Batas Histori:** Sisi backend python (`app/core/agent_engine.py` $\rightarrow$ `history_to_messages`) memotong riwayat obrolan dan hanya membawa maksimal **10 pesan terakhir** ke LLM untuk optimasi token.

---

## 🔌 Model Context Protocol (MCP) Integration
1. **Module:** Dikelola oleh `/home/erwan/kirana-server/app/core/mcp_manager.py` (stdio client, converting schemas to dynamic Pydantic models for LangChain StructuredTools).
2. **Konfigurasi:** Konfigurasi server MCP tersimpan di `/home/erwan/kirana-server/data/mcp_config.json` (diambil dari setelan openclaw bawaan: `servertenant`, `orangtua`, `cloudflare-mcp`, `panot`).
3. **Schema Caching:** Menggunakan *in-memory schema caching* agar server MCP tidak di-boot ulang hanya untuk membaca list tool.
4. **Perkakas Manajemen:** AI memiliki tool `manage_mcp_servers` untuk menambah, menghapus, atau melihat daftar server MCP secara langsung via obrolan chat.
