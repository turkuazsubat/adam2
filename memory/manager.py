"""
Memory Manager - SQLite Tabanlı Hafıza Sistemi
"""
import sqlite3
import os
import logging
import re

logger = logging.getLogger(__name__)


class MemoryManager:
    """Veritabanı bağlantısını ve hafıza işlemlerini yönetir"""
    
    def __init__(self, db_path="db/project.db", schema_path="db_schema.sql"):
        self.db_path = db_path
        self.schema_path = schema_path
        self.conn = None
        self.cursor = None
        self.last_interaction_id = None
        
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.connect()
        self.initialize_db()
        
        logger.info(f"💾 Hafıza sistemi hazır: {db_path}")
    
    def connect(self):
        """Veritabanı bağlantısını kurar"""
        try:
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.conn.row_factory = sqlite3.Row
            self.cursor = self.conn.cursor()
        except sqlite3.Error as e:
            logger.critical(f"Veritabanı hatası: {e}")
            raise
    
    def initialize_db(self):
        """Tabloları oluşturur"""
        if os.path.exists(self.schema_path):
            try:
                with open(self.schema_path, 'r', encoding='utf-8') as f:
                    self.cursor.executescript(f.read())
                self.conn.commit()
            except sqlite3.Error as e:
                logger.error(f"Şema hatası: {e}")
        
        # Profil tablosu (garanti için)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_profile (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)
        self.conn.commit()
    
    def normalize_query(self, query: str) -> str:
        """Sorguyu temizler"""
        if not query:
            return ""
        cleaned = re.sub(r'[^\w\s]', ' ', query)
        return ' '.join(cleaned.lower().split()).strip()
    
    def save_interaction(self, user_input, assistant_response):
        """Etkileşimi kaydeder"""
        try:
            self.cursor.execute("""
                INSERT INTO interactions (user_input, response_text) 
                VALUES (?, ?)
            """, (user_input, assistant_response))
            self.conn.commit()
            self.last_interaction_id = self.cursor.lastrowid
            return self.last_interaction_id
        except sqlite3.Error as e:
            logger.error(f"Etkileşim kayıt hatası: {e}")
            return None
    
    def get_last_interaction(self) -> dict:
        """Son etkileşimi döndürür"""
        try:
            self.cursor.execute("""
                SELECT user_input, response_text 
                FROM interactions 
                ORDER BY timestamp DESC 
                LIMIT 1
            """)
            row = self.cursor.fetchone()
            if row:
                return {
                    "user_input": row[0],
                    "response": row[1]
                }
        except Exception as e:
            logger.error(f"Son etkileşim alınamadı: {e}")
        return None
    
    def promote_to_memory(self, user_query, bot_response):
        """Kalıcı hafızaya kayıt"""
        normalized_key = self.normalize_query(user_query)
        try:
            self.cursor.execute("""
                INSERT OR REPLACE INTO memory (key, value, status)
                VALUES (?, ?, 'valid')
            """, (normalized_key, bot_response))
            self.conn.commit()
            logger.info(f"LTM kaydedildi: {normalized_key}")
            return True
        except Exception as e:
            logger.error(f"LTM kayıt hatası: {e}")
            return False
    
    def read_from_memory(self, query: str) -> str:
        """Hafızadan okur"""
        normalized_key = self.normalize_query(query)
        try:
            self.cursor.execute("""
                SELECT value FROM memory
                WHERE key = ? AND status = 'valid'
                ORDER BY created_at DESC LIMIT 1
            """, (normalized_key,))
            row = self.cursor.fetchone()
            if row:
                return row[0]
        except sqlite3.Error as e:
            logger.error(f"Okuma hatası: {e}")
        return None
    
    def invalidate_last(self):
        """Son hafıza kaydını geçersiz kılar"""
        try:
            self.cursor.execute("""
                UPDATE memory 
                SET status = 'invalid' 
                WHERE rowid = (SELECT MAX(rowid) FROM memory)
            """)
            self.conn.commit()
            return True
        except:
            return False
    
    def add_task(self, task):
        """Görev ekler"""
        try:
            self.cursor.execute(
                "INSERT INTO todo_list (task, status) VALUES (?, 'pending')",
                (task,)
            )
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Görev ekleme hatası: {e}")
            return False
    
    def get_tasks(self):
        """Görevleri listeler"""
        try:
            self.cursor.execute(
                "SELECT id, task FROM todo_list WHERE status = 'pending'"
            )
            return self.cursor.fetchall()
        except Exception as e:
            logger.error(f"Görev listeleme hatası: {e}")
            return []
    
    def close(self):
        """Bağlantıyı kapatır"""
        if self.conn:
            self.conn.close()
            logger.info("Veritabanı bağlantısı kapatıldı")