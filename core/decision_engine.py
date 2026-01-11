"""
Decision Engine - ADAM'ın Merkezi Karar Motoru
Kullanıcı → Bağlam → LLM → Tool → Cevap akışını yönetir
"""
import logging
from typing import Dict, Optional
from core.qwen_brain import QwenBrain
from core.context_builder import ContextBuilder
from tools.registry import registry
from memory.manager import MemoryManager
from memory.profile_manager import ProfileManager

logger = logging.getLogger(__name__)


class DecisionEngine:
    """
    ADAM'ın merkezi sinir sistemi.
    Tüm karar verme süreçlerini yönetir.
    """
    
    def __init__(
        self,
        memory_manager: MemoryManager,
        profile_manager: ProfileManager,
        model_path: str = "models/qwen_agent.gguf"
    ):
        self.memory = memory_manager
        self.profile = profile_manager
        
        # Alt modülleri başlat
        self.context_builder = ContextBuilder(memory_manager, profile_manager)
        self.qwen = QwenBrain(model_path=model_path)
        
        logger.info("🚀 Decision Engine başlatıldı")
    
    def process_input(
        self,
        user_input: str,
        screen_data: Optional[Dict] = None
    ) -> str:
        """
        Ana işlem fonksiyonu.
        
        Returns:
            Kullanıcıya gösterilecek cevap
        """
        
        logger.info(f"📥 Input: {user_input[:50]}...")
        
        # 1. Bağlam oluştur
        context = self.context_builder.build_context(user_input, screen_data)
        
        # 2. Mevcut araçları al
        available_tools = registry.get_tools_schema()
        
        # 3. LLM'e sor
        decision = self.qwen.generate_with_context(
            user_input=user_input,
            context=context,
            available_tools=available_tools
        )
        
        logger.info(f"Karar: {decision.get('intent')} | Tool: {decision.get('tool_call')}")
        
        # 4. Kararı uygula
        final_response = self._execute_decision(decision, user_input, context)
        
        # 5. Hafızaya kaydet
        self._save_to_memory(user_input, final_response, decision)
        
        # 6. Konuşma geçmişine ekle
        self.context_builder.add_to_history("user", user_input)
        self.context_builder.add_to_history("assistant", final_response)
        
        return final_response
    
    def _execute_decision(
        self,
        decision: Dict,
        user_input: str,
        context: Dict
    ) -> str:
        """LLM kararını uygular"""
        
        tool_call = decision.get("tool_call")
        base_response = decision.get("response", "")
        
        # Tool yok, direkt cevap
        if tool_call is None:
            return base_response
        
        # Tool var, çalıştır
        tool_name = tool_call.get("name")
        tool_args = tool_call.get("arguments", {})
        
        if not tool_name:
            return base_response
        
        # Tool'u çalıştır
        tool_result = registry.execute_tool(tool_name, tool_args)
        
        # İçerik araçları için LLM analizi
        content_tools = ["read_clipboard", "read_pdf", "ocr_read"]
        
        if tool_name in content_tools and len(tool_result) > 100:
            logger.info("📄 İçerik LLM'e analiz ettiriliyor...")
            
            analysis_prompt = f"""Araç '{tool_name}' bu veriyi döndürdü:

{tool_result[:1000]}

Kullanıcı '{user_input}' demişti. Bu veriyi ona açıkla."""
            
            analyzed = self.qwen.simple_chat(analysis_prompt, max_tokens=300)
            return analyzed
        
        # Normal tool sonucu
        if base_response:
            return f"{base_response}\n\n{tool_result}"
        else:
            return tool_result
    
    def _save_to_memory(
        self,
        user_input: str,
        response: str,
        decision: Dict
    ):
        """Etkileşimi hafızaya kaydeder"""
        
        try:
            # İnteraksiyonu kaydet
            self.memory.save_interaction(user_input, response)
            
            # Soru-cevap türündeyse LTM'e kaydet
            intent = decision.get("intent")
            if intent == "query" and len(response) > 50:
                self.memory.promote_to_memory(user_input, response)
        
        except Exception as e:
            logger.error(f"Hafıza kayıt hatası: {e}")
    
    def handle_feedback(self, feedback_type: str) -> str:
        """Geri bildirim komutları (!onay, !yanlış)"""
        
        last_interaction = self.memory.get_last_interaction()
        
        if not last_interaction:
            return "Geri bildirim verilecek bir etkileşim bulunamadı."
        
        if feedback_type == "onay":
            self.memory.promote_to_memory(
                last_interaction["user_input"],
                last_interaction["response"]
            )
            return "✅ Son cevap hafızama kaydedildi."
        
        elif feedback_type == "yanlış":
            self.memory.invalidate_last()
            return "❌ Son cevap geçersiz olarak işaretlendi."
        
        else:
            return "Bilinmeyen geri bildirim türü."
    
    def clear_context(self):
        """Konuşma bağlamını sıfırlar"""
        self.context_builder.clear_history()