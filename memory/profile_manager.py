"""
Profile Manager - Kullanıcı Profili Yönetimi
"""
import logging

logger = logging.getLogger(__name__)


class ProfileManager:
    """
    Kullanıcı profili (isim, üslup, tercihler) yönetir.
    """
    
    def __init__(self, memory_manager):
        self.memory = memory_manager
        self.profile_txt_path = "user_profile.txt"
        
        # İlk yüklemede TXT'yi güncelle
        self._mirror_to_txt()
        
        logger.info("👤 Profil yöneticisi hazır")
    
    def set(self, key: str, value: str) -> bool:
        """Profil özelliği kaydeder"""
        try:
            self.memory.cursor.execute("""
                INSERT OR REPLACE INTO user_profile (key, value) 
                VALUES (?, ?)
            """, (key, value))
            self.memory.conn.commit()
            
            # TXT'yi güncelle
            self._mirror_to_txt()
            
            logger.info(f"Profil güncellendi: {key} = {value}")
            return True
        
        except Exception as e:
            logger.error(f"Profil kayıt hatası: {e}")
            return False
    
    def get(self, key: str) -> str:
        """Tek bir profil özelliği alır"""
        try:
            self.memory.cursor.execute(
                "SELECT value FROM user_profile WHERE key = ?",
                (key,)
            )
            row = self.memory.cursor.fetchone()
            if row:
                return row[0]
        except Exception as e:
            logger.error(f"Profil okuma hatası: {e}")
        return None
    
    def get_all(self) -> dict:
        """Tüm profili döndürür"""
        try:
            self.memory.cursor.execute("SELECT key, value FROM user_profile")
            return {row[0]: row[1] for row in self.memory.cursor.fetchall()}
        except Exception as e:
            logger.error(f"Profil getirme hatası: {e}")
            return {}
    
    def delete(self, key: str) -> bool:
        """Profil özelliği siler"""
        try:
            self.memory.cursor.execute(
                "DELETE FROM user_profile WHERE key = ?",
                (key,)
            )
            self.memory.conn.commit()
            self._mirror_to_txt()
            return True
        except:
            return False
    
    def _mirror_to_txt(self):
        """Profili TXT dosyasına yansıtır (debug için)"""
        try:
            profile = self.get_all()
            
            with open(self.profile_txt_path, "w", encoding="utf-8") as f:
                f.write("=== ADAM KULLANICI PROFİLİ ===\n\n")
                
                if not profile:
                    f.write("Henüz profil verisi yok.\n")
                else:
                    for key, value in profile.items():
                        f.write(f"{key.upper()}: {value}\n")
                        f.write("-" * 30 + "\n")
        
        except Exception as e:
            logger.warning(f"TXT mirror hatası: {e}")