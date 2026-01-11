"""
Context Builder - Dinamik Bağlam Oluşturma Motoru
LLM'e gönderilecek tam bağlamı hazırlar
"""
from typing import Dict, List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ContextBuilder:
    """
    Her sorgu için kullanıcı durumuna göre optimize edilmiş bağlam üretir.
    """
    
    def __init__(self, memory_manager, profile_manager):
        self.memory = memory_manager
        self.profile = profile_manager
        self.conversation_history = []
        self.max_history = 5
        
        logger.info("🔧 Context Builder hazır")
    
    def build_context(
        self,
        user_input: str,
        screen_data: Optional[Dict] = None
    ) -> Dict:
        """
        Tam bağlamı oluşturur.
        
        Returns:
            {
                "profile": {...},
                "conversation": [...],
                "screen_info": {...},
                "relevant_memories": [...],
                "temporal": {...}
            }
        """
        context = {
            "profile": self._get_profile_context(),
            "conversation": self._get_conversation_history(),
            "temporal": self._get_temporal_context()
        }
        
        # Ekran verisi varsa ekle
        if screen_data:
            context["screen_info"] = self._format_screen_data(screen_data)
        
        # Semantik arama (opsiyonel, şimdilik basit hafıza)
        context["relevant_memories"] = self._get_relevant_memories(user_input)
        
        return context
    
    def _get_profile_context(self) -> Dict:
        """Kullanıcı profilini çeker"""
        profile_data = self.profile.get_all()
        
        defaults = {
            "user_name": "Kullanıcı",
            "tone": "dostane",
            "expertise": "genel"
        }
        
        return {**defaults, **profile_data}
    
    def _get_conversation_history(self) -> List[Dict]:
        """Son N etkileşimi döndürür"""
        return self.conversation_history[-self.max_history:]
    
    def _format_screen_data(self, screen_data: Dict) -> Dict:
        """Ghost Observer verisini formatlar"""
        return {
            "active_window": screen_data.get("window_title", "Bilinmiyor"),
            "clipboard": screen_data.get("clipboard_preview", "")[:100],
            "last_activity": screen_data.get("timestamp")
        }
    
    def _get_relevant_memories(self, query: str, top_k: int = 2) -> List[str]:
        """
        Sorguya alakalı anıları bulur.
        Şimdilik basit SQL sorgusu, ileride semantik arama eklenebilir.
        """
        try:
            # Hafızadan en son 5 kaydı al
            self.memory.cursor.execute("""
                SELECT value FROM memory 
                WHERE status = 'valid' 
                ORDER BY created_at DESC 
                LIMIT 5
            """)
            
            results = self.memory.cursor.fetchall()
            return [row[0] for row in results]
        
        except Exception as e:
            logger.warning(f"Hafıza sorgusu başarısız: {e}")
            return []
    
    def _get_temporal_context(self) -> Dict:
        """Zaman bilgisi"""
        now = datetime.now()
        
        gun_adlari = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", 
                      "Cuma", "Cumartesi", "Pazar"]
        
        return {
            "current_time": now.strftime("%H:%M"),
            "current_date": now.strftime("%d.%m.%Y"),
            "day_of_week": gun_adlari[now.weekday()],
            "is_weekend": now.weekday() >= 5
        }
    
    def add_to_history(self, role: str, content: str):
        """Konuşma geçmişine ekler"""
        self.conversation_history.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
        
        # Limit aşılırsa eski konuşmaları sil
        if len(self.conversation_history) > self.max_history * 2:
            self.conversation_history = self.conversation_history[-self.max_history * 2:]
    
    def clear_history(self):
        """Konuşma geçmişini temizler"""
        self.conversation_history = []
        logger.info("Konuşma geçmişi temizlendi")
    
    def get_context_summary(self, context: Dict) -> str:
        """Debug için bağlam özeti"""
        profile = context.get("profile", {})
        temporal = context.get("temporal", {})
        
        return f"""
=== BAĞLAM ===
Kullanıcı: {profile.get('user_name')}
Zaman: {temporal.get('day_of_week')} {temporal.get('current_time')}
Son Konuşmalar: {len(context.get('conversation', []))}
===============
"""