# -*- coding: utf-8 -*-
"""
Osmanlı Eyalet Yönetim Simülasyonu
Destek ve Geri Bildirim API Modülü (GitHub & SMTP Entegrasyonu)
"""

import os
import json
import base64
import requests
import threading
import smtplib
import sys
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def _deobfuscat(obfuscated_text: str) -> str:
    """secured_keys.json içindeki şifreli metni çalışma zamanında çözer."""
    if not obfuscated_text:
        return ""
    try:
        # Önce ters çevirme işlemini geri al
        reversed_b64 = obfuscated_text[::-1]
        
        # Base64 decode işlemi
        xored_bytes = base64.b64decode(reversed_b64.encode('utf-8'))
        
        # XOR şifresini çöz (Anahtar = 42)
        key = 42
        original_bytes = bytearray()
        for b in xored_bytes:
            original_bytes.append(b ^ key)
            
        return original_bytes.decode('utf-8')
    except Exception as e:
        print(f"[Destek API] Şifre çözme hatası: {e}")
        return ""

class SupportAPI:
    """Oyun içinden hata, öneri ve destek biletleri gönderen sınıf."""
    
    def __init__(self):
        self.github_token = ""
        self.email_address = ""
        self.email_pass = ""
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 465
        
        # GitHub Repo URL (Örn: M-Enes-Senovali/Osmanl-Eyalet-sim-lasyonu)
        self.github_repo = "M-Enes-Senovali/Osmanl-Eyalet-sim-lasyonu"
        
        self.is_ready = False
        self._load_keys()

    def _load_keys(self):
        """secured_keys.json dosyasından obfuscate edilmiş anahtarları yükler."""
        if getattr(sys, 'frozen', False):
            # PyInstaller ile derlenmişse (.exe içinden)
            base_dir = sys._MEIPASS
        else:
            # Normal .py betiği olarak çalışıyorsa (ana dizinde arıyoruz)
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            
        key_file = os.path.join(base_dir, "secured_keys.json")
        
        if os.path.exists(key_file):
            try:
                with open(key_file, "r", encoding="utf-8") as f:
                    secrets = json.load(f)
                    
                self.github_token = _deobfuscat(secrets.get("github_token_encrypted", ""))
                self.email_address = _deobfuscat(secrets.get("email_address_encrypted", ""))
                self.email_pass = _deobfuscat(secrets.get("email_pass_encrypted", ""))
                
                # Custom SMTP Server support
                server_val = _deobfuscat(secrets.get("smtp_server_encrypted", ""))
                port_val = _deobfuscat(secrets.get("smtp_port_encrypted", ""))
                if server_val: self.smtp_server = server_val
                if port_val and port_val.isdigit(): self.smtp_port = int(port_val)
                
                if self.github_token or (self.email_address and self.email_pass):
                    self.is_ready = True
                    print("[Destek API] Anahtarlar başarıyla yüklendi ve sistem aktif.")
            except Exception as e:
                print(f"[Destek API] Anahtar dosyası okuma hatası: {e}")
        else:
            print("[Destek API] UYARI: secured_keys.json bulunamadı! Bildirim sistemi çalışmayacak.")

    def submit_ticket_async(self, destination: str, category: str, subject: str, message: str, game_state_info: str = "", player_email: str = "", callback=None):
        """
        Bileti arkaplan (Thread) üzerinde gönderir ki oyun donmasın.
        destination: "github" veya "email"
        """
        if not self.is_ready:
            if callback:
                callback(False, "Hata: Destek sistemi API anahtarları kurulu değil.")
            return

        def _send_task():
            success = False
            error_msgs = []
            
            if destination == "github":
                if self.github_token:
                    gh_success, gh_err = self._send_to_github(category, subject, message, game_state_info)
                    if gh_success:
                        success = True
                    else:
                        error_msgs.append(f"GitHub Hatası: {gh_err}")
                else:
                    error_msgs.append("GitHub token eksik.")
                    
            elif destination == "email":
                if self.email_address and self.email_pass:
                    em_success, em_err = self._send_to_email(category, subject, message, game_state_info, player_email)
                    if em_success:
                        success = True
                    else:
                        error_msgs.append(f"E-Posta Hatası: {em_err}")
                else:
                    error_msgs.append("E-Posta kimlik bilgileri eksik.")
                    
            if callback:
                if success:
                    callback(True, "Biletiniz başarıyla iletildi. Katkınız için teşekkürler!")
                else:
                    callback(False, " | ".join(error_msgs))

        # Thread başlat
        thread = threading.Thread(target=_send_task)
        thread.daemon = True
        thread.start()

    def _send_to_github(self, category: str, subject: str, message: str, game_state_info: str):
        """GitHub API'sini kullanarak depoda yeni bir Issue açar."""
        if not self.github_token:
            return False, "GitHub token yok"
            
        url = f"https://api.github.com/repos/{self.github_repo}/issues"
        
        # Etiketler (Labels)
        labels = ["user-report"]
        if "hata" in category.lower() or "bug" in category.lower():
            labels.append("bug")
        elif "öneri" in category.lower() or "tavsiye" in category.lower():
            labels.append("enhancement")
            
        title = f"[{category.upper()}] {subject}"
        
        body = f"### Kullanıcı Mesajı\n{message}\n\n"
        if game_state_info:
            body += f"### Oyun İçi Durum Özeti (Debug)\n```\n{game_state_info}\n```\n\n"
        body += "\n*Bu sorun/öneri oyun içindeki yerleşik destek API aracı ile otomatik olarak gönderilmiştir.*"

        headers = {
            "Authorization": f"token {self.github_token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        data = {
            "title": title,
            "body": body,
            "labels": labels
        }
        
        try:
            response = requests.post(url, headers=headers, json=data, timeout=10)
            if response.status_code == 201:
                return True, ""
            else:
                return False, f"Status {response.status_code}: {response.text}"
        except Exception as e:
            return False, str(e)

    def _send_to_email(self, category: str, subject: str, message: str, game_state_info: str, player_email: str):
        """SMTP protokolü ile doğrudan Gmail üzerinden bildirim atar."""
        if not self.email_address or not self.email_pass:
            return False, "E-Posta ayarları eksik"
            
        try:
            msg = MIMEMultipart()
            msg['From'] = self.email_address
            msg['To'] = self.email_address  # Kendisine atacak
            msg['Subject'] = f"Osmanlı Oyunu - [{category.upper()}] {subject}"
            
            if player_email:
                msg.add_header('reply-to', player_email)
            
            body = f"KATEGORİ: {category}\n\n"
            if player_email:
                body += f"GÖNDEREN OYUNCU E-POSTASI: {player_email}\n\n"
                
            body += f"MESAJ:\n{message}\n\n"
            if game_state_info:
                body += f"OYUN İÇİ DURUM (DEBUG):\n{game_state_info}\n"
                
            msg.attach(MIMEText(body, 'plain'))
            
            import ssl
            context = ssl.create_default_context()
            
            # SMTP sunucusuna bağlan (Örn: mail.altinbilgi.com.tr)
            with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port, context=context) as server:
                server.login(self.email_address, self.email_pass)
                server.send_message(msg)
                
            return True, ""
        except Exception as e:
            return False, str(e)

# Singleton Pattern (Kolay erişim için)
_support_api_instance = None

def get_support_api() -> SupportAPI:
    global _support_api_instance
    if _support_api_instance is None:
        _support_api_instance = SupportAPI()
    return _support_api_instance
