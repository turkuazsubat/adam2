"""
Ghost Observer - Hayalet Gözlemci
Kullanıcı sormadan ekranı ve sistemi izler
"""
import threading
import time
import logging
import pyperclip
from typing import Optional, Dict, Callable

try:
    import win32gui
    import psutil
    WIN_AVAILABLE = True
except ImportError:
    WIN_AVAILABLE = False
    logging.warning("pywin32 veya psutil yok, Observer devre dışı")

logger = logging.getLogger(__name__)


class GhostObserver:
    """Arka planda sessizce gözlem yapar"""
    
    def __init__(
        self,
        callback: Optional[Callable] = None,
        check_interval: int = 5
    ):
        self.callback = callback
        self.check_interval = check_interval
        
        # Durum
        self.last_window_title = ""
        self.last_clipboard = ""
        self.is_running = False
        self.observer_thread = None
        
        # Hata pattern'leri
        self.error_keywords = [
            "error", "exception", "failed", "hata", "başarısız",
            "traceback", "syntax", "runtime", "warning"
        ]
        
        if WIN_AVAILABLE:
            logger.info("👁️ Ghost Observer hazır")
        else:
            logger.warning("👁️ Observer pasif (pywin32 eksik)")
    
    def start(self):
        """Gözlemi başlatır"""
        
        if not WIN_AVAILABLE:
            logger.warning("Observer başlatılamıyor: pywin32 eksik")
            return
        
        if self.is_running:
            return
        
        self.is_running = True
        self.observer_thread = threading.Thread(
            target=self._observation_loop,
            daemon=True
        )
        self.observer_thread.start()
        logger.info("✅ Ghost Observer aktif")
    
    def stop(self):
        """Gözlemi durdurur"""
        self.is_running = False
        if self.observer_thread:
            self.observer_thread.join(timeout=2)
        logger.info("🛑 Observer durduruldu")
    
    def _observation_loop(self):
        """Ana gözlem döngüsü"""
        
        while self.is_running:
            try:
                # 1. Pencere kontrolü
                window_data = self._check_active_window()
                if window_data:
                    self._trigger_callback(window_data)
                
                # 2. Pano kontrolü
                clipboard_data = self._check_clipboard()
                if clipboard_data:
                    self._trigger_callback(clipboard_data)
                
                # 3. Sistem sağlığı
                system_data = self._check_system_health()
                if system_data:
                    self._trigger_callback(system_data)
                
                time.sleep(self.check_interval)
            
            except Exception as e:
                logger.error(f"Observer döngü hatası: {e}")
                time.sleep(self.check_interval)
    
    def _check_active_window(self) -> Optional[Dict]:
        """Aktif pencere kontrolü"""
        
        try:
            hwnd = win32gui.GetForegroundWindow()
            window_title = win32gui.GetWindowText(hwnd)
            
            if window_title == self.last_window_title:
                return None
            
            self.last_window_title = window_title
            
            # Hata kontrolü
            title_lower = window_title.lower()
            has_error = any(kw in title_lower for kw in self.error_keywords)
            
            if has_error:
                logger.info(f"🚨 Hata penceresi: {window_title}")
                return {
                    "type": "window_change",
                    "window_title": window_title,
                    "contains_error": True
                }
        
        except Exception as e:
            logger.error(f"Pencere kontrolü hatası: {e}")
        
        return None
    
    def _check_clipboard(self) -> Optional[Dict]:
        """Pano kontrolü"""
        
        try:
            current = pyperclip.paste()
            
            if current == self.last_clipboard or len(current) < 10:
                self.last_clipboard = current
                return None
            
            self.last_clipboard = current
            
            # Kod/hata tespiti
            lower = current.lower()
            
            is_code = any(kw in lower for kw in [
                "def ", "import ", "class ", "function", "const "
            ])
            
            is_error = any(kw in lower for kw in self.error_keywords)
            
            if is_code or is_error:
                logger.info(f"📋 İlginç pano: {len(current)} karakter")
                return {
                    "type": "clipboard_change",
                    "content_preview": current[:200],
                    "is_code": is_code,
                    "is_error": is_error
                }
        
        except Exception as e:
            logger.error(f"Pano hatası: {e}")
        
        return None
    
    def _check_system_health(self) -> Optional[Dict]:
        """Sistem yükü kontrolü"""
        
        try:
            cpu = psutil.cpu_percent(interval=1)
            mem = psutil.virtual_memory().percent
            
            if cpu > 90 or mem > 85:
                logger.warning(f"⚠️ Sistem yükü: CPU {cpu}%, RAM {mem}%")
                return {
                    "type": "system_stress",
                    "cpu_percent": cpu,
                    "memory_percent": mem
                }
        
        except Exception as e:
            logger.error(f"Sistem kontrolü hatası: {e}")
        
        return None
    
    def _trigger_callback(self, event_data: Dict):
        """Callback tetikler"""
        if self.callback:
            try:
                self.callback(event_data)
            except Exception as e:
                logger.error(f"Callback hatası: {e}")
    
    def get_current_state(self) -> Dict:
        """Anlık durum"""
        
        if not WIN_AVAILABLE:
            return {}
        
        try:
            hwnd = win32gui.GetForegroundWindow()
            window = win32gui.GetWindowText(hwnd)
            
            return {
                "window_title": window,
                "clipboard_preview": self.last_clipboard[:100],
                "timestamp": time.time()
            }
        except:
            return {}