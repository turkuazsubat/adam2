"""
ADAM Merkezi Beyin - GGUF Qwen2.5 Model
Yerel, hızlı ve hafıza dostu LLM motoru
"""
import json
import logging
from typing import Dict, List, Optional
from llama_cpp import Llama

logger = logging.getLogger(__name__)


class QwenBrain:
    """
    GGUF formatında Qwen modelini kullanan yerel LLM.
    Function calling ve bağlamsal karar verme yeteneği.
    """
    
    def __init__(
        self,
        model_path: str = "models/qwen_agent.gguf",
        n_ctx: int = 4096,
        n_threads: int = 4,
        n_gpu_layers: int = 0
    ):
        """
        Args:
            model_path: GGUF model dosyasının yolu
            n_ctx: Context window boyutu (4096 = ~3000 kelime)
            n_threads: CPU thread sayısı (4-8 optimal)
            n_gpu_layers: GPU'ya yüklenecek katman sayısı (0 = sadece CPU)
        """
        self.model_path = model_path
        
        logger.info(f"🧠 Qwen Brain başlatılıyor: {model_path}")
        
        try:
            self.llm = Llama(
                model_path=model_path,
                n_ctx=n_ctx,
                n_threads=n_threads,
                n_gpu_layers=n_gpu_layers,
                verbose=False  # Gereksiz log'ları kapat
            )
            logger.info("✅ Qwen Brain hazır (GGUF modu)")
        
        except Exception as e:
            logger.critical(f"Model yükleme hatası: {e}")
            raise
    
    def generate_with_context(
        self,
        user_input: str,
        context: Dict,
        available_tools: List[Dict],
        max_tokens: int = 512,
        temperature: float = 0.7
    ) -> Dict:
        """
        Bağlamsal üretim yapar ve tool çağırma kararı verir.
        
        Returns:
            {
                "intent": "command" | "query" | "chat",
                "tool_call": {
                    "name": "take_note",
                    "arguments": {"text": "..."}
                } | None,
                "response": "Kullanıcıya cevap"
            }
        """
        
        # Sistem prompt'unu oluştur
        system_prompt = self._build_system_prompt(context, available_tools)
        
        # Tam prompt'u hazırla
        full_prompt = f"""{system_prompt}

Kullanıcı: {user_input}

Asistan (JSON formatında cevap ver):"""
        
        logger.info(f"💭 Düşünüyor... (max {max_tokens} token)")
        
        try:
            # Model üretimi
            output = self.llm(
                full_prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=0.9,
                stop=["Kullanıcı:", "\n\n\n"],  # Durma koşulları
                echo=False
            )
            
            # Çıktıyı al
            generated_text = output['choices'][0]['text'].strip()
            
            # JSON ayrıştır
            result = self._parse_response(generated_text)
            
            logger.info(f"✅ Karar: {result.get('intent')}")
            return result
        
        except Exception as e:
            logger.error(f"Üretim hatası: {e}")
            return {
                "intent": "chat",
                "tool_call": None,
                "response": "Üzgünüm, bir düşünce hatası yaşadım. Tekrar söyler misin?"
            }
    
    def _build_system_prompt(self, context: Dict, tools: List[Dict]) -> str:
        """Dinamik sistem prompt'u oluşturur"""
        
        profile = context.get("profile", {})
        user_name = profile.get("user_name", "Kullanıcı")
        tone = profile.get("tone", "dostane")
        
        # Zaman bilgisi
        temporal = context.get("temporal", {})
        time_str = f"{temporal.get('day_of_week', 'Bugün')} {temporal.get('current_time', '')}"
        
        # Konuşma geçmişi
        conversation = context.get("conversation", [])
        history_str = ""
        if conversation:
            for msg in conversation[-3:]:  # Son 3 konuşma
                role = "Kullanıcı" if msg["role"] == "user" else "Asistan"
                history_str += f"{role}: {msg['content']}\n"
        
        # Tool listesi
        tools_json = json.dumps(tools, indent=2, ensure_ascii=False)
        
        prompt = f"""Sen ADAM (Adaptive Personal Core), yerel çalışan yapay zeka asistanısın.

KULLANICI BİLGİLERİ:
- İsim: {user_name}
- Üslup Tercihi: {tone}
- Zaman: {time_str}

SON KONUŞMALAR:
{history_str if history_str else "İlk etkileşim"}

GÖREV:
Kullanıcının isteğini anla ve uygun aksiyonu belirle.

KULLANILABİLİR ARAÇLAR:
{tools_json}

CEVAP FORMATI (SADECE JSON):
{{
  "intent": "command" veya "query" veya "chat",
  "tool_call": {{"name": "araç_adı", "arguments": {{"param": "değer"}}}} veya null,
  "response": "Kullanıcıya söylenecek kısa mesaj"
}}

KURALLAR:
1. Araç kullanılacaksa "tool_call" doldur, kullanılmayacaksa null yap
2. Her zaman geçerli JSON formatında cevap ver
3. Üslup '{tone}' olmalı
4. Kısa ve net cevaplar ver"""
        
        return prompt
    
    def _parse_response(self, raw_output: str) -> Dict:
        """Model çıktısını JSON'a çevirir"""
        
        try:
            # Markdown temizleme
            cleaned = raw_output.strip()
            if "```json" in cleaned:
                cleaned = cleaned.split("```json")[1].split("```")[0]
            elif "```" in cleaned:
                cleaned = cleaned.split("```")[1].split("```")[0]
            
            # JSON parse
            result = json.loads(cleaned.strip())
            
            # Validasyon
            if "intent" not in result:
                result["intent"] = "chat"
            if "response" not in result:
                result["response"] = cleaned[:200]
            
            return result
        
        except json.JSONDecodeError:
            logger.warning(f"JSON parse başarısız, ham çıktı: {raw_output[:100]}")
            
            # Fallback: Ham metni döndür
            return {
                "intent": "chat",
                "tool_call": None,
                "response": raw_output[:500]
            }
    
    def simple_chat(self, message: str, max_tokens: int = 256) -> str:
        """
        Basit sohbet modu (tool kullanmadan).
        Hızlı cevaplar için.
        """
        prompt = f"""Sen ADAM adlı dostane bir asistansın.

Kullanıcı: {message}
Asistan:"""
        
        try:
            output = self.llm(
                prompt,
                max_tokens=max_tokens,
                temperature=0.7,
                stop=["Kullanıcı:"]
            )
            return output['choices'][0]['text'].strip()
        except Exception as e:
            logger.error(f"Basit sohbet hatası: {e}")
            return "Üzgünüm, bir sorun oluştu."


# === TEST BLOĞU ===
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    brain = QwenBrain()
    
    # Test 1: Basit sohbet
    print("=== TEST 1: Basit Sohbet ===")
    response = brain.simple_chat("Merhaba ADAM, nasılsın?")
    print(f"Cevap: {response}\n")
    
    # Test 2: Tool çağırma
    print("=== TEST 2: Tool Çağırma ===")
    context = {
        "profile": {"user_name": "Yavuz", "tone": "teknik"},
        "temporal": {"day_of_week": "Pazartesi", "current_time": "14:30"}
    }
    
    tools = [
        {
            "name": "take_note",
            "description": "Not alır",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {"type": "string"}
                }
            }
        }
    ]
    
    result = brain.generate_with_context(
        user_input="Yarın doktora gideceğimi not al",
        context=context,
        available_tools=tools
    )
    
    print(json.dumps(result, indent=2, ensure_ascii=False))