import time
import pyperclip
import threading
from modules.brain import Brain

class GhostObserver:
    def __init__(self, brain_instance, user_profile, callback_function, tool_manager=None):
        """
        Ghost Modülü: Arka planda panoyu izler ve sadece hata kodu görürse uyarır.
        """
        self.brain = brain_instance
        self.profile = user_profile
        self.callback = callback_function # GUI'ye mesaj gönderen fonksiyon
        self.tool_manager = tool_manager  # Gerekirse tool kullanması için (Opsiyonel)
        self.last_clipboard = ""
        self.running = False

    def start(self):
        self.running = True
        thread = threading.Thread(target=self._watch_clipboard, daemon=True)
        thread.start()

    def stop(self):
        self.running = False

    def _watch_clipboard(self):
        print("👻 Ghost: Gözlem başladı (Final Mod)...")
        # İlk açılışta panodaki eski veriyi okuyup "yeni" sanmaması için:
        try:
            self.last_clipboard = pyperclip.paste()
        except:
            self.last_clipboard = ""

        while self.running:
            try:
                current_clipboard = pyperclip.paste()
                
                # Değişiklik kontrolü (En az 5 karakter ve eskisiyle aynı değilse)
                if current_clipboard != self.last_clipboard and len(current_clipboard) > 5:
                    print(f"\n👻 Ghost: Değişiklik yakalandı!")
                    self.last_clipboard = current_clipboard
                    
                    # --- FİNAL PROMPT ---
                    # Modele "Düşünme, direkt konuş" diyoruz.
                    # Negatif kelimeyi 'SKIP' yaptık.
                    prompt = f"""
                    GÖREV: Panodaki metni analiz et.
                    
                    METİN:
                    "{current_clipboard[:1000]}"
                    
                    KURALLAR:
                    1. Eğer bu bir YAZILIM HATASI (Traceback, Error, Exception) veya KOD PARÇASI ise: Kullanıcıya hitaben, hatanın sebebini veya çözümünü tek cümleyle, samimi bir dille söyle.
                    2. Eğer sıradan bir metinse (haber, mesaj, link vb.): Sadece 'SKIP' yaz.
                    """
                    
                    # Brain içindeki LLM nesnesine direkt erişim
                    response = self.brain.llm.create_chat_completion(
                        messages=[
                            {"role": "system", "content": "Sen arka planda çalışan zeki bir gözlemcisin. Sadece hataları yakalarsın."},
                            {"role": "user", "content": prompt}
                        ],
                        max_tokens=100, # Kısa tut
                        temperature=0.3 # Yaratıcı olma, net ol
                    )
                    
                    suggestion = response['choices'][0]['message']['content'].strip()
                    
                    # Hata ayıklama için terminale basıyoruz
                    print(f"👻 Model Çıktısı: [{suggestion}]") 

                    # Eğer SKIP değilse GUI'ye gönder
                    if "SKIP" not in suggestion and len(suggestion) > 5:
                        self.callback(f"👻 [GHOST]: {suggestion}")
                    else:
                        print("👻 Ghost: Önemsiz (SKIP).")
                
            except Exception as e:
                print(f"👻 Ghost HATA: {e}")
            
            # CPU'yu yormamak için 2 saniye bekle
            time.sleep(2)