from llama_cpp import Llama
import json
import datetime

class Brain:
    def __init__(self, model_path, tools_schema):
        print("🧠 ADAM Beyni Yükleniyor... (Qwen-2.5-3B)")
        
        # Model Yükleme (RAM Dostu Ayarlar)
        self.llm = Llama(
            model_path=model_path,
            n_ctx=512,           # Context'i iyice düşürdük (RAM'i kurtarır)
            n_batch=128,         # Paket boyutunu küçülttük
            n_threads=4,         # İşlemciyi yormasın
            n_gpu_layers=0,      # Her şeyi CPU'ya çek (En güvenlisi bu)
            verbose=False
        )
        
        self.tools_schema = tools_schema
        print("✅ Beyin Aktif.")

    def _create_system_prompt(self, user_profile):
        """
        Modelin kişiliğini ve yeteneklerini tanımlayan prompt.
        JSON formatını zorlamak için kurallar sıkılaştırıldı.
        """
        current_time = datetime.datetime.now().strftime("%d %B %Y, %H:%M")
        
        prompt = f"""<|im_start|>system
Sen ADAM (Adaptive Personal Core). Python tabanlı, yerel çalışan gelişmiş bir yapay zeka asistanısın.
Tarih: {current_time}

KULLANICI BİLGİSİ:
İsim: {user_profile.get('name', 'Kullanıcı')}
Biyografi: {user_profile.get('bio', 'Bilinmiyor')}
İlgi Alanları: {user_profile.get('interests', [])}

GÖREVLERİN:
1. Kullanıcıyla samimi, zeki ve doğrudan bir dille konuş. Asla Wikipedia gibi sıkıcı olma.
2. Kullanıcının isteği bir eylem gerektiriyorsa (not almak, arama yapmak vb.), aşağıdaki ARAÇLARI (TOOLS) kullan.

MEVCUT ARAÇLAR (TOOLS):
{self.tools_schema}

KRİTİK KURALLAR (Tool Kullanımı):
- Eğer bir araç kullanman gerekiyorsa, cevabın SADECE şu formatta olmalı:
  <TOOL_CALL>{{"name": "tool_adi", "args": "parametre"}}</TOOL_CALL>
  
- Tool çağrısından sonra veya önce ASLA ekstra açıklama yazma. Sadece XML/JSON ver.
- Parametre yoksa "args": null yap.
- Eğer sadece sohbet ediyorsan <TOOL_CALL> kullanma, normal cevap ver.
<|im_end|>
"""
        return prompt

    def think(self, user_input, user_profile, history=[]):
        """
        HAFIZA SINIRLAMALI DÜŞÜNME (Çökmeyi Önler)
        """
        system_prompt = self._create_system_prompt(user_profile)
        
        messages = [{"role": "system", "content": system_prompt}]
        
        # --- KRİTİK DEĞİŞİKLİK: SADECE SON 2 MESAJI AL ---
        # 5'ten 2'ye düşürdük ki 512 sınırını geçmesin
        for msg in history[-2:]: 
            role = "user" if msg['role'] == "user" else "assistant"
            # Mesaj çok uzunsa kırp (Hafıza güvenliği için)
            content = msg['content'][:200] 
            messages.append({"role": role, "content": content})

        # Yeni mesaj (Bunu da güvenlik için biraz kısıtlayalım)
        messages.append({"role": "user", "content": user_input[:300]})

        # Cevap Üret
        try:
            response = self.llm.create_chat_completion(
                messages=messages,
                temperature=0.6,
                max_tokens=256, # Cevabı da kısa tut ki sınır aşılmasın
                stop=["<|im_end|>", "User:", "Siz:"]
            )
            return response['choices'][0]['message']['content']
        except Exception as e:
            # Eğer yine sınır hatası verirse, geçmişi tamamen silip sadece soruyu sor
            print(f"Hafıza doldu, temizleniyor... Hata: {e}")
            response = self.llm.create_chat_completion(
                messages=[{"role": "system", "content": system_prompt},
                          {"role": "user", "content": user_input}],
                max_tokens=256
            )
            return response['choices'][0]['message']['content']
    def process_tool_result(self, tool_result, history):
        """
        Tool çalıştıktan sonra gelen sonucu (örn: "Not kaydedildi") alır
        ve kullanıcıya son bir nazik cevap üretir.
        """
        prompt = f"""<|im_start|>system
Sen ADAM. Az önce bir aracı başarıyla çalıştırdın.
Aracın Teknik Çıktısı: {tool_result}

GÖREV:
Bu teknik çıktıyı kullanıcıya doğal bir dille bildir.
Örn: "Not kaydedildi" -> "Tamamdır, notunu aldım."
Örn: "Wikipedia: Polonya..." -> "Araştırdım ve şunu buldum: Polonya..."

Kısa ve net ol.
<|im_end|>
"""
        response = self.llm.create_chat_completion(
            messages=[{"role": "system", "content": prompt}],
            temperature=0.7,
            max_tokens=200
        )
        return response['choices'][0]['message']['content']