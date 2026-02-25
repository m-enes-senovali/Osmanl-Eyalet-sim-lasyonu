# -*- coding: utf-8 -*-
"""
Osmanlı Eyalet Yönetim Simülasyonu - Güncelleme Sistemi
GitHub Releases API ile otomatik güncelleme
"""

import os
import sys
import json
import tempfile
import zipfile
import shutil
import subprocess
import threading
import queue
from typing import Optional, Tuple, Dict, List
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

from config import VERSION, GITHUB_REPO
from audio.audio_manager import get_audio_manager

# Güncelleme sırasında korunacak dosya/klasörler
# Bunlar asla silinmez veya üzerine yazılmaz
PROTECTED_PATHS = {
    'saves',           # Kayıt dosyaları
    'save',            # Alternatif kayıt klasörü
    'settings.json',   # Kullanıcı ayarları
    'config_user.json',# Kullanıcı config
    '__pycache__',     # Python cache
    '.git',            # Git metadata
}


class UpdateChecker:
    """GitHub Releases API ile güncelleme kontrolü"""
    
    API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
    
    def __init__(self):
        self.audio = get_audio_manager()
        self.latest_version: Optional[str] = None
        self.latest_release_url: Optional[str] = None
        self.changelog: Optional[str] = None
        self.download_url: Optional[str] = None
        self.is_checking = False
        self.is_downloading = False
        self.download_progress = 0
        self.error_message: Optional[str] = None
        self.startup_result: Optional[Dict] = None
        
        # Thread-safe callback kuyruğu
        # Background thread buraya yazar, main thread işler
        self._callback_queue: queue.Queue = queue.Queue()
    
    def process_callbacks(self):
        """
        Main thread'den çağrılmalı (game loop'ta).
        Background thread'lerden gelen callback'leri güvenli şekilde işler.
        """
        while not self._callback_queue.empty():
            try:
                callback, args = self._callback_queue.get_nowait()
                callback(*args)
            except queue.Empty:
                break
            except Exception as e:
                print(f"Callback hatası: {e}")
    
    @property
    def current_version(self) -> str:
        """Mevcut sürüm"""
        return VERSION
    
    def _parse_version(self, version_str: str) -> Tuple[int, ...]:
        """Sürüm stringini karşılaştırılabilir tuple'a çevir"""
        # v1.0.0 => (1, 0, 0)
        clean = version_str.lstrip('vV')
        try:
            return tuple(int(x) for x in clean.split('.'))
        except ValueError:
            return (0, 0, 0)
    
    def is_newer_version(self, remote: str, local: str) -> bool:
        """Uzak sürüm yerel sürümden yeni mi?"""
        return self._parse_version(remote) > self._parse_version(local)
    
    def check_for_updates(self) -> Dict:
        """
        GitHub'dan güncelleme kontrolü yap.
        
        Returns:
            {
                'available': bool,
                'current': str,
                'latest': str,
                'changelog': str,
                'error': str or None
            }
        """
        self.is_checking = True
        self.error_message = None
        
        try:
            # GitHub API'ye istek
            request = Request(
                self.API_URL,
                headers={
                    'User-Agent': 'OsmanliEyaletSimulasyonu',
                    'Accept': 'application/vnd.github.v3+json'
                }
            )
            
            with urlopen(request, timeout=10) as response:
                data = json.loads(response.read().decode('utf-8'))
            
            # Release bilgilerini al
            self.latest_version = data.get('tag_name', '0.0.0')
            self.changelog = data.get('body', 'Değişiklik notu yok.')
            self.latest_release_url = data.get('html_url', '')
            
            # İndirme linkini bul (.exe veya .zip)
            assets = data.get('assets', [])
            for asset in assets:
                name = asset.get('name', '').lower()
                if name.endswith('.exe') or name.endswith('.zip'):
                    self.download_url = asset.get('browser_download_url')
                    break
            
            # Eğer asset yoksa zip ball kullan
            if not self.download_url:
                self.download_url = data.get('zipball_url')
            
            is_update_available = self.is_newer_version(
                self.latest_version, 
                self.current_version
            )
            
            self.is_checking = False
            
            return {
                'available': is_update_available,
                'current': self.current_version,
                'latest': self.latest_version,
                'changelog': self.changelog,
                'error': None
            }
            
        except HTTPError as e:
            if e.code == 404:
                self.error_message = "Henüz bir güncelleme yayınlanmamış"
            else:
                self.error_message = f"GitHub hatası: {e.code}"
        except URLError as e:
            self.error_message = f"Bağlantı hatası: {e.reason}"
        except json.JSONDecodeError:
            self.error_message = "Geçersiz yanıt"
        except Exception as e:
            self.error_message = f"Hata: {str(e)}"
        
        self.is_checking = False
        return {
            'available': False,
            'current': self.current_version,
            'latest': None,
            'changelog': None,
            'error': self.error_message
        }
    
    def check_async(self, callback):
        """Arka planda güncelleme kontrolü (thread-safe)"""
        def _check():
            result = self.check_for_updates()
            # Callback'i main thread'e gönder
            self._callback_queue.put((callback, (result,)))
        
        thread = threading.Thread(target=_check, daemon=True)
        thread.start()
    
    def check_on_startup(self):
        """
        Oyun başlangıcında arka planda güncelleme kontrolü.
        Sonuç startup_result'a yazılır, main loop process_callbacks ile işler.
        """
        def _on_startup_result(result):
            self.startup_result = result
            if result.get('available'):
                self.announce_status(result)
        
        self.check_async(_on_startup_result)
    
    def download_update(self, callback=None) -> bool:
        """
        Güncellemeyi indir.
        
        Args:
            callback: İlerleme durumu için callback(progress, status)
        
        Returns:
            Başarılı mı?
        """
        if not self.download_url:
            self.error_message = "İndirme linki bulunamadı"
            return False
        
        self.is_downloading = True
        self.download_progress = 0
        
        try:
            # Geçici dizin oluştur
            temp_dir = tempfile.mkdtemp(prefix="osmanli_update_")
            
            # Dosya adını belirle
            filename = self.download_url.split('/')[-1]
            if '?' in filename:
                filename = filename.split('?')[0]
            if not filename:
                filename = "update.zip"
            
            temp_file = os.path.join(temp_dir, filename)
            
            if callback:
                callback(0, "İndiriliyor...")
            
            # İndir
            request = Request(
                self.download_url,
                headers={'User-Agent': 'OsmanliEyaletSimulasyonu'}
            )
            
            with urlopen(request, timeout=60) as response:
                total_size = int(response.headers.get('Content-Length', 0))
                downloaded = 0
                chunk_size = 8192
                
                with open(temp_file, 'wb') as f:
                    while True:
                        chunk = response.read(chunk_size)
                        if not chunk:
                            break
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        if total_size > 0:
                            self.download_progress = int((downloaded / total_size) * 100)
                            if callback:
                                callback(self.download_progress, f"İndiriliyor... %{self.download_progress}")
            
            if callback:
                callback(100, "İndirme tamamlandı!")
            
            # Güncellemeyi uygula
            success = self._apply_update(temp_file, temp_dir, callback)
            
            self.is_downloading = False
            return success
            
        except Exception as e:
            self.error_message = f"İndirme hatası: {str(e)}"
            self.is_downloading = False
            if callback:
                callback(-1, self.error_message)
            return False
    
    def _apply_update(self, file_path: str, temp_dir: str, callback=None) -> bool:
        """
        İndirilen güncellemeyi uygula.
        
        Exe dosyası ise:
            - Mevcut exe'yi yedekle
            - Yeni exe'yi kopyala
            - Oyunu yeniden başlat
        
        Zip dosyası ise:
            - Zip'i aç
            - Dosyaları güncelle
        """
        try:
            if callback:
                callback(100, "Güncelleme uygulanıyor...")
            
            # Exe güncelleme dosyası mı?
            if file_path.endswith('.exe'):
                # Mevcut exe yolu
                current_exe = sys.executable
                backup_exe = current_exe + '.backup'
                
                # Yedekle
                if os.path.exists(backup_exe):
                    os.remove(backup_exe)
                
                # Batch script oluştur (exe'yi kapatıp güncellemek için)
                batch_script = os.path.join(temp_dir, 'update.bat')
                with open(batch_script, 'w', encoding='utf-8') as f:
                    f.write(f'''@echo off
echo Güncelleme uygulanıyor...
timeout /t 2 /nobreak > nul
move /y "{current_exe}" "{backup_exe}"
move /y "{file_path}" "{current_exe}"
start "" "{current_exe}"
del "%~f0"
''')
                
                # Batch'i çalıştır ve çık
                subprocess.Popen(['cmd', '/c', batch_script], 
                               creationflags=subprocess.CREATE_NO_WINDOW)
                
                if callback:
                    callback(100, "Oyun yeniden başlatılıyor...")
                
                # Çık
                sys.exit(0)
                
            elif file_path.endswith('.zip'):
                # Zip'i aç
                extract_dir = os.path.join(temp_dir, 'extracted')
                
                with zipfile.ZipFile(file_path, 'r') as zf:
                    zf.extractall(extract_dir)
                
                # Dosyaları kopyala
                app_dir = os.path.dirname(os.path.abspath(__file__))
                
                # Zip içindeki ilk klasörü bul (GitHub zipball formatı)
                items = os.listdir(extract_dir)
                if len(items) == 1 and os.path.isdir(os.path.join(extract_dir, items[0])):
                    source_dir = os.path.join(extract_dir, items[0])
                else:
                    source_dir = extract_dir
                
                # Dosyaları kopyala — korunan yolları ATLAYARAK
                for item in os.listdir(source_dir):
                    # Kayıt dosyaları ve ayarları koru!
                    if item in PROTECTED_PATHS:
                        continue
                    
                    src = os.path.join(source_dir, item)
                    dst = os.path.join(app_dir, item)
                    
                    if os.path.isdir(src):
                        if os.path.exists(dst):
                            shutil.rmtree(dst)
                        shutil.copytree(src, dst)
                    else:
                        shutil.copy2(src, dst)
                
                if callback:
                    callback(100, "Güncelleme tamamlandı! Oyunu yeniden başlatın.")
                
                return True
            
            return True
            
        except Exception as e:
            self.error_message = f"Uygulama hatası: {str(e)}"
            if callback:
                callback(-1, self.error_message)
            return False
    
    def download_async(self, callback):
        """Arka planda güncelleme indir (thread-safe)"""
        def _safe_callback(*args):
            self._callback_queue.put((callback, args))
        
        def _download():
            self.download_update(_safe_callback)
        
        thread = threading.Thread(target=_download, daemon=True)
        thread.start()
    
    def announce_status(self, result: Dict):
        """Güncelleme durumunu sesli duyur"""
        if result.get('error'):
            self.audio.speak(f"Güncelleme kontrolü başarısız: {result['error']}")
        elif result.get('available'):
            self.audio.speak(
                f"Yeni sürüm mevcut: {result['latest']}. "
                f"Mevcut sürümünüz: {result['current']}"
            )
        else:
            self.audio.speak(f"Oyun güncel. Sürüm: {result['current']}")


# Global instance
_updater: Optional[UpdateChecker] = None


def get_updater() -> UpdateChecker:
    """Global updater instance"""
    global _updater
    if _updater is None:
        _updater = UpdateChecker()
    return _updater
