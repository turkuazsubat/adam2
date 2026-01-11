
import os
import sys
import json
import threading
import datetime
import logging
import re # Regex parser için
import customtkinter as ctk
from tkinter import scrolledtext
import tkinter as tk

# --- BACKEND MODÜLLERİ --- 
from modules.scheduler_module import TimeMaster
from modules.installer_check import check_and_install_tesseract

# --- SES MODÜLLERİ ---
try:
    from modules.tts import TextToSpeech
    from modules.stt import SpeechToText
    VOICE_AVAILABLE = False
except ImportError:
    VOICE_AVAILABLE = False
# AYARLAR

# === YENİ IMPORT'LAR (Dosyanın başına eklenecek) ===
from core.decision_engine import DecisionEngine
from memory.manager import MemoryManager  # Yeni yol
from memory.profile_manager import ProfileManager  # Yeni modül
from modules.observer import GhostObserver


DB_PATH = "db/project.db"
SCHEMA_PATH = "db_schema.sql"
MODEL_PATH = "models/qwen_agent.gguf"

# Tema Ayarları
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("green")

class ProjectXGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("ADAM v3 (Adaptive Personal Core)")
        self.root.geometry("650x800") 
        
        self.is_processing = False
        self.thinking_id = None
        self.history = [] 
        
        self.brain = None
        self.memory = None
        self.tool_manager = None
        self.ghost = None
        self.user_profile = {} 
        
        self.tts = None
        self.stt = None
        self.scheduler = TimeMaster(self.incoming_notification)

        self.setup_ui()
        self.observer = None  # Ghost Observer için
        
        # === BACKEND BAŞLATMA (DEĞİŞİYOR) ===
        self.append_message("Sistem", "Çekirdek modülleri yükleniyor...", "info")
        self.root.after(100, self.init_backend)

    def setup_ui(self):
        """SENİN İSTEDİĞİN BOYUT VE TASARIM AYARLARI"""
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(0, weight=1)
        
        # 1. Sohbet Alanı (Senin istediğin 'Segoe UI 18' boyutu)
        self.chat_display = scrolledtext.ScrolledText(
            self.root, 
            state='disabled', 
            wrap='word', 
            font=('Segoe UI', 18), # <-- İSTEDİĞİN BÜYÜK FONT
            bg="#2b2b2b", 
            fg="white", 
            borderwidth=0,
            highlightthickness=0
        )
        self.chat_display.grid(row=0, column=0, sticky="nsew", padx=15, pady=(15, 5))
        
        # Renkler
        self.chat_display.tag_config('user', foreground="#4da6ff", justify="right", rmargin=10)
        self.chat_display.tag_config('bot', foreground="#00e676", justify="left", lmargin1=10, lmargin2=10)
        self.chat_display.tag_config('system', foreground="#ff5252", justify="center")
        self.chat_display.tag_config("info", foreground="gray", justify="center")
        self.chat_display.tag_config('tool', foreground="#FFD700", justify="center")

        # 2. Alt Panel
        bottom_frame = ctk.CTkFrame(self.root, corner_radius=15, fg_color="#333333")
        bottom_frame.grid(row=1, column=0, sticky="ew", padx=15, pady=15)
        bottom_frame.grid_columnconfigure(0, weight=1)

        # 3. Giriş Kutusu (Senin istediğin 'Segoe UI 14' boyutu)
        self.entry_field = ctk.CTkTextbox(
            bottom_frame, 
            height=50, 
            font=("Segoe UI", 14), # <-- İSTEDİĞİN BOYUT
            activate_scrollbars=False, 
            fg_color="#404040", 
            text_color="white"
        )
        self.entry_field.grid(row=0, column=0, sticky="ew", padx=(10, 5), pady=10)

        # Olaylar
        self.entry_field.bind("<Return>", self.handle_enter)
        self.entry_field.bind("<KeyRelease>", self.fix_turkish_chars_live)

        # 4. Mikrofon Butonu
        self.mic_button = ctk.CTkButton(
            bottom_frame, text="🎙️", width=50, height=40, font=("Arial",16), 
            fg_color="#E65100", hover_color="#EF6C00", corner_radius=10
        )
        self.mic_button.grid(row=0, column=1, padx=5, pady=10)
        self.mic_button.bind('<ButtonPress-1>', self.on_mic_press)
        self.mic_button.bind('<ButtonRelease-1>', self.on_mic_release)

        # 5. Gönder Butonu (Senin istediğin boyutlar)
        self.send_button = ctk.CTkButton(
            bottom_frame, text="Gönder", command=self.send_message, width=80, height=40,
            font=("Segoe UI", 12, "bold"), fg_color="#2E7D32", hover_color="#1B5E20", corner_radius=10
        )
        self.send_button.grid(row=0, column=2, padx=(5, 10), pady=10)

    # --- TÜRKÇE KARAKTER DÜZELTİCİ ---
    def fix_turkish_chars_live(self, event):
        if event.keysym in ["Return", "BackSpace", "Shift_L", "Shift_R"]: return
        try:
            current_text = self.entry_field.get("1.0", "end-1c")
            if any(char in current_text for char in ['ð', 'Ð', 'þ', 'Þ', 'ý', 'Ý']):
                cursor_pos = self.entry_field.index("insert")
                fixed_text = (current_text
                              .replace('ð', 'ğ').replace('Ð', 'Ğ')
                              .replace('þ', 'ş').replace('Þ', 'Ş')
                              .replace('ý', 'ı').replace('Ý', 'İ'))
                
                self.entry_field.delete("1.0", "end")
                self.entry_field.insert("1.0", fixed_text)
                try: self.entry_field.mark_set("insert", cursor_pos)
                except: pass
        except: pass

    def handle_enter(self, event):
        if event.state & 0x0001: return None
        self.send_message()
        return "break"

    def init_backend(self):
        """
        YENİ: Qwen tabanlı Decision Engine başlatır.
        ESKİ: memory, feedback_manager, tool_manager ayrı ayrı yükleniyordu.
        """
        try:
            # 1. Hafıza Sistemini Başlat
            self.memory = MemoryManager(db_path=DB_PATH, schema_path=SCHEMA_PATH)
            self.profile = ProfileManager(self.memory)
            
            # 2. Merkezi Karar Motorunu Başlat
            self.append_message("Sistem", "🧠 Qwen Brain yükleniyor (İlk açılış 30sn sürebilir)...", "info")
            
            self.decision_engine = DecisionEngine(
                memory_manager=self.memory,
                profile_manager=self.profile,
                model_path="models/qwen_agent.gguf"  # Senin model yolun
            )
            
            self.append_message("Sistem", "✅ Bağlantı başarılı. ADAM hazır.", "info")
            self.append_message(
                "Asistan", 
                "Merhaba Yavuz! Ben ADAM 2.0. Artık daha akıllıyım ve ekranını izleyebiliyorum. Nasıl yardımcı olabilirim?", 
                "bot"
            )
            
            # 3. Ghost Observer'ı Başlat (Proaktif Mod)
            self.observer = GhostObserver(
                callback=self.on_observer_event,
                check_interval=5
            )
            self.observer.start()
            
            # 4. Ses Sistemini Yükle (Eski kod, değişmiyor)
            if VOICE_AVAILABLE:
                threading.Thread(target=self.init_voice_modules, daemon=True).start()
        
        except Exception as e:
            self.append_message("Sistem", f"KRİTİK HATA: {e}", "system")
            #log_event("CRITICAL", f"GUI Başlatma Hatası: {e}", "gui")
    
    def on_observer_event(self, event_data: Dict):
        """
        YENİ: Ghost Observer bir şey tespit edince bu çalışır
        """
        event_type = event_data.get("type")
        
        if event_type == "window_change" and event_data.get("contains_error"):
            msg = f"👁️ Bir hata mesajı fark ettim: '{event_data['window_title'][:40]}...'\nYardımcı olmamı ister misin?"
            self.root.after(0, lambda: self.append_message("ADAM (Proaktif)", msg, "system"))
        
        elif event_type == "clipboard_change" and event_data.get("is_error"):
            msg = "👁️ Panoya bir hata mesajı kopyaladın. Açıklamamı ister misin?"
            self.root.after(0, lambda: self.append_message("ADAM (Proaktif)", msg, "system"))
        
        elif event_type == "system_stress":
            msg = f"👁️ Sistem biraz yavaşlamış (RAM: %{event_data['memory_percent']}). Yardım ister misin?"
            self.root.after(0, lambda: self.append_message("ADAM (Proaktif)", msg, "system"))
    
    def _load_modules_thread(self):
        try:
            self.memory = MemoryManager(db_path=DB_PATH, schema_path=SCHEMA_PATH)
            self.user_profile = self.memory.get_profile()
            if not self.user_profile: self.user_profile = {"name": "Yavuz", "bio": "Bilinmiyor", "interests": []}
            
            #self.tool_manager = ToolManager()
            tools_schema = self.tool_manager.get_tool_schemas()

            #self.brain = Brain(model_path=MODEL_PATH, tools_schema=tools_schema)
            
            self.ghost = GhostObserver(self.brain, self.user_profile, self.incoming_notification, self.tool_manager)
            self.ghost.start()

            if VOICE_AVAILABLE:
                self.tts = TextToSpeech()
                self.stt = SpeechToText()

            self.root.after(0, lambda: self.append_message("Sistem", "Bağlantı başarılı. ADAM hazır.", "info"))
            self.root.after(0, lambda: self.append_message("Asistan", f"Merhaba {self.user_profile.get('name', 'Yavuz')}! Emrindeyim.", "bot"))

        except Exception as e:
            self.root.after(0, lambda: self.append_message("Sistem", f"BAŞLATMA HATASI: {e}", "system"))
            #log_event("CRITICAL", f"GUI Backend Hata: {e}", "gui")

    # --- BRAIN THREAD (REGEX PARSER İLE) ---
    def process_input_thread(self, user_input):
        """
        YENİ: Decision Engine'e yönlendirir
        ESKİ: generate_response, feedback, tool_manager ayrı ayrı çağrılıyordu
        """
        try:
            response = ""
            
            # Geri bildirim komutları (!onay, !yanlış)
            if user_input.startswith("!"):
                command = user_input[1:].lower().strip()
                response = self.decision_engine.handle_feedback(command)
            
            # Normal sohbet/komut
            else:
                # Observer'dan ekran durumunu al
                screen_data = None
                if self.observer:
                    screen_data = self.observer.get_current_state()
                
                # Merkezi engine'e gönder
                response = self.decision_engine.process_input(
                    user_input=user_input,
                    screen_data=screen_data
                )
        
        except Exception as e:
            response = f"Beklenmedik hata: {e}"
           
        
        # Sonucu ana thread'e gönder
        self.root.after(0, self.update_ui_with_response, user_input, response)

    def send_message(self, event=None):
        user_input = self.entry_field.get("1.0", "end-1c").strip()
        user_input = (user_input.replace('ð', 'ğ').replace('Ð', 'Ğ')
                      .replace('þ', 'ş').replace('Þ', 'Ş')
                      .replace('ý', 'ı').replace('Ý', 'İ'))

        if not user_input or self.is_processing: return "break"
        if user_input.lower() in ["çık", "exit", "quit"]:
            self.root.destroy()
            return "break"

        self.append_message("Siz", user_input, 'user')
        self.entry_field.delete("1.0", "end")
        self.is_processing = True
        self.entry_field.configure(state="disabled")
        self.thinking_id = self.append_message("Asistan", "Düşünüyor...", 'info', is_temp=True)

        threading.Thread(target=self.process_brain_thread, args=(user_input,)).start()
        return "break"

    def finish_processing(self, response):
        if self.thinking_id: self.delete_message(self.thinking_id)
        self.append_message("Asistan", response, "bot")
        self.is_processing = False
        self.entry_field.configure(state="normal")
        self.entry_field.focus_set()

    def incoming_notification(self, message):
        self.root.after(0, lambda: self.append_message("Asistan", message, "bot"))

    # --- MESAJ EKLEME (Senin istediğin Font Boyutlarıyla) ---
    def append_message(self, sender, message, tag, is_temp=False):
        self.chat_display.configure(state="normal")
        timestamp = datetime.datetime.now().strftime("%H:%M")
        
        if tag != "tool":
            self.chat_display.insert("end", f"{sender} [{timestamp}]:\n", tag)
        
        self.chat_display.insert("end", str(message) + "\n", tag)

        # Mavi Seslendir Linki (İstediğin font boyutu: 12 underline)
        if sender == "Asistan" and not is_temp and self.tts:
            lbl = tk.Label(
                self.chat_display, text="🔊 Seslendir", font=("Segoe UI", 12, "underline"), 
                fg="#40C4FF", bg="#2b2b2b", cursor="hand2"
            )
            lbl.bind("<Button-1>", lambda e, m=message: self.manual_speak(m))
            self.chat_display.window_create("end", window=lbl)
            self.chat_display.insert("end", "\n\n")
        else:
            self.chat_display.insert("end", "\n\n", tag)
            
        self.chat_display.configure(state="disabled")
        self.chat_display.see("end")
        
        if is_temp:
            return self.chat_display.index("end-3l"), self.chat_display.index("end-1c")

    def delete_message(self, indices):
        try:
            self.chat_display.configure(state="normal")
            self.chat_display.delete(indices[0], indices[1])
            self.chat_display.configure(state="disabled")
        except: pass

    # --- SES FONKSİYONLARI ---
    def on_mic_press(self, event):
        if not self.stt or self.is_processing: return
        self.mic_button.configure(fg_color="#D32F2F", text="🔴")
        self.entry_field.delete("1.0", "end")
        try: self.stt.start_recording()
        except: pass

    def on_mic_release(self, event):
        if not self.stt or self.is_processing: return
        self.mic_button.configure(fg_color="#FF9800", text="⏳")
        threading.Thread(target=self.process_voice_thread, daemon=True).start()

    def process_voice_thread(self):
        try:
            text = self.stt.stop_and_transcribe()
            self.root.after(0, lambda: self.finish_voice_process(text))
        except:
            self.root.after(0, lambda: self.finish_voice_process(None))

    def finish_voice_process(self, text):
        self.mic_button.configure(fg_color="#E65100", text="🎙️")
        if text:
            self.entry_field.insert("1.0", text)
            self.send_message()
        else:
            self.append_message("Sistem", "Ses algılanamadı.", "info")

    def manual_speak(self, text):
        if self.tts: threading.Thread(target=self.tts.speak, args=(text,), daemon=True).start()

if __name__ == "__main__":
    # Bu bölüm de aynı kalacak
    logging.basicConfig(level=logging.INFO)
    
    from modules.installer_check import check_and_install_tesseract
    check_and_install_tesseract()
    
    root = ctk.CTk()
    
    try:
        root.tk.call('encoding', 'system', 'utf-8')
    except:
        pass
    
    app = ProjectXGUI(root)
    root.mainloop()