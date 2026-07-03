import os
import requests
import json
from dotenv import load_dotenv

# Load ENV agar variabel terbaca
load_dotenv()

class KiranaClient:
    def __init__(self):
        self.base_url = os.getenv("KIRANA_SERVER_URL")
        self.api_key = os.getenv("X_API_KEY")
        # [NEW] Ambil Client ID dari .env
        self.client_id = os.getenv("CLIENT_ID", "unknown-device")

        # Ambil Timeout dari .env (default: 600 detik / 10 menit)
        try:
            self.timeout = int(os.getenv("KIRANA_TIMEOUT", "600"))
        except ValueError:
            self.timeout = 600

        if not self.base_url:
            raise ValueError("❌ Konfigurasi KIRANA_SERVER_URL belum diset di .env")
        if not self.api_key:
            raise ValueError("❌ Konfigurasi X_API_KEY belum diset di .env")

        # Setup Session
        self.session = requests.Session()
        
        # [NEW] Masukkan Header Wajib (Termasuk Client ID)
        self.session.headers.update({
            "X-API-Key": self.api_key,
            "X-Client-ID": self.client_id,  # <--- INI YG BIKIN ERROR HILANG
            "Content-Type": "application/json",
            "User-Agent": "Kirana-Client/6.0.0 (Ubuntu)"
        })

    def post_request(self, endpoint, payload, timeout=None):
        """Helper untuk kirim POST request"""
        if timeout is None:
            timeout = self.timeout
        url = f"{self.base_url}{endpoint}"
        try:
            response = self.session.post(url, json=payload, timeout=timeout)
            
            # Handle Error HTTP (4xx, 5xx)
            if response.status_code != 200:
                # Coba ambil pesan error dari JSON server
                try:
                    err_msg = response.json().get("detail", response.text)
                except:
                    err_msg = response.text
                return {"error": f"Server Reject: {err_msg}"}
            
            return response.json()

        except requests.exceptions.ConnectionError:
            return {"error": f"Gagal koneksi ke {self.base_url}. Server mati atau URL salah."}
        except requests.exceptions.Timeout:
            return {"error": f"Request Timeout. Server kelamaan mikir (lagi sibuk). Batas waktu saat ini: {timeout} detik."}
        except Exception as e:
            return {"error": str(e)}
