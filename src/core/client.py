import os
import requests
import logging
from dotenv import load_dotenv
from rich.console import Console

# Load config dari .env
load_dotenv()

console = Console()
logger = logging.getLogger("KiranaClient")

class KiranaClient:
    """
    Bridge untuk komunikasi antara Laptop (Client) dan Linux Server (Brain).
    """
    def __init__(self):
        self.base_url = os.getenv("KIRANA_SERVER_URL")
        self.api_key = os.getenv("X_API_KEY")
        
        # Validasi Config
        if not self.base_url:
            raise ValueError("❌ Konfigurasi KIRANA_SERVER_URL belum diset di .env")
        if not self.api_key:
            raise ValueError("❌ Konfigurasi X_API_KEY belum diset di .env")

        # Standard Headers
        self.headers = {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json",
            "User-Agent": "Kirana-Client/5.0 (Ubuntu)"
        }

    def check_connection(self):
        """Ping ke Server untuk memastikan server hidup dan Key valid."""
        try:
            # Tembak root endpoint
            url = f"{self.base_url}/"
            response = requests.get(url, headers=self.headers, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                return True, f"Terhubung ke {data.get('system')} ({data.get('status')})"
            elif response.status_code == 403:
                return False, "⛔ API Key Ditolak (Forbidden). Cek .env Mas."
            else:
                return False, f"⚠️ Server Error: {response.status_code}"
                
        except requests.exceptions.ConnectionError:
            return False, f"❌ Gagal konek ke {self.base_url}. Server mati atau IP salah?"
        except Exception as e:
            return False, f"❌ Error: {str(e)}"

    def post_request(self, endpoint, payload, timeout=60):
        """Wrapper untuk POST request (Chat, Scan, dll)"""
        url = f"{self.base_url}{endpoint}"
        try:
            response = requests.post(url, json=payload, headers=self.headers, timeout=timeout)
            response.raise_for_status() # Raise error kalau 4xx/5xx
            return response.json()
        except requests.exceptions.HTTPError as e:
            # Coba ambil pesan error dari server kalau ada
            try:
                err_detail = response.json().get('detail', str(e))
                return {"error": f"Server Reject: {err_detail}"}
            except:
                return {"error": str(e)}
        except Exception as e:
            return {"error": f"Connection Failed: {str(e)}"}
