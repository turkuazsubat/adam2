"""
Tool Registry - Tüm Araçları Merkezi Yönetim
"""
import os
import json
import logging
import subprocess
from datetime import datetime
from typing import Dict, List, Callable, Optional

logger = logging.getLogger(__name__)


class ToolRegistry:
    """Araçları kaydeder ve yönetir"""
    
    def __init__(self):
        self._tools: Dict[str, Dict] = {}
        logger.info("🔧 Tool Registry başlatılıyor...")
        
        # Araçları kaydet
        self._register_all_tools()
        
        logger.info(f"✅ {len(self._tools)} araç kaydedildi")
    
    def _register_all_tools(self):
        """Tüm araçları kaydeder"""
        
        # 1. NOT ALMA
        self._tools["take_note"] = {
            "name": "take_note",
            "description": "Kullanıcının verdiği metni not defterine kaydeder",
            "function": self._take_note,
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Kaydedilecek not"}
                },
                "required": ["text"]
            }
        }
        
        # 2. GÖREV EKLEME
        self._tools["add_todo"] = {
            "name": "add_todo",
            "description": "Yapılacaklar listesine görev ekler",
            "function": self._add_todo,
            "parameters": {
                "type": "object",
                "properties": {
                    "task": {"type": "string", "description": "Görev açıklaması"}
                },
                "required": ["task"]
            }
        }
        
        # 3. GÖREV LİSTELEME
        self._tools["list_todos"] = {
            "name": "list_todos",
            "description": "Yapılacaklar listesini gösterir",
            "function": self._list_todos,
            "parameters": {"type": "object", "properties": {}}
        }
        
        # 4. UYGULAMA BAŞLATMA
        self._tools["launch_app"] = {
            "name": "launch_app",
            "description": "Belirtilen uygulamayı başlatır (brave, spotify, notepad vb.)",
            "function": self._launch_app,
            "parameters": {
                "type": "object",
                "properties": {
                    "app_name": {"type": "string", "description": "Uygulama adı"}
                },
                "required": ["app_name"]
            }
        }
        
        # 5. PANO OKUMA
        self._tools["read_clipboard"] = {
            "name": "read_clipboard",
            "description": "Panodaki (clipboard) metni okur",
            "function": self._read_clipboard,
            "parameters": {"type": "object", "properties": {}}
        }
        
        # 6. PDF OKUMA
        self._tools["read_pdf"] = {
            "name": "read_pdf",
            "description": "Belirtilen PDF dosyasını okur",
            "function": self._read_pdf,
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {"type": "string", "description": "PDF dosya adı"}
                },
                "required": ["filename"]
            }
        }
        
        # 7. OCR (EKRAN OKUMA)
        self._tools["ocr_read"] = {
            "name": "ocr_read",
            "description": "Panodaki resmi OCR ile okur",
            "function": self._ocr_read,
            "parameters": {"type": "object", "properties": {}}
        }
    
    # === TOOL FONKSİYONLARI ===
    
    def _take_note(self, text: str) -> str:
        """Not alma"""
        try:
            NOTES_PATH = "data/notes.txt"
            os.makedirs(os.path.dirname(NOTES_PATH), exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            note_entry = f"[{timestamp}] - {text}\n"
            
            with open(NOTES_PATH, "a", encoding="utf-8") as f:
                f.write(note_entry)
            
            return "✅ Not başarıyla kaydedildi."
        except Exception as e:
            return f"❌ Not kaydedilemedi: {e}"
    
    def _add_todo(self, task: str) -> str:
        """Görev ekleme"""
        try:
            TODO_PATH = "data/todo.txt"
            os.makedirs(os.path.dirname(TODO_PATH), exist_ok=True)
            
            with open(TODO_PATH, "a", encoding="utf-8") as f:
                f.write(f"- {task}\n")
            
            return f"✅ Görev eklendi: '{task}'"
        except Exception as e:
            return f"❌ Görev eklenemedi: {e}"
    
    def _list_todos(self) -> str:
        """Görev listeleme"""
        try:
            TODO_PATH = "data/todo.txt"
            
            if not os.path.exists(TODO_PATH):
                return "Yapılacaklar listeniz boş."
            
            with open(TODO_PATH, "r", encoding="utf-8") as f:
                todos = f.readlines()
            
            if not todos:
                return "Yapılacaklar listeniz boş."
            
            response = "📋 Yapılacaklar Listeniz:\n"
            for i, todo in enumerate(todos, 1):
                response += f"{i}. {todo.strip()}\n"
            
            return response
        except Exception as e:
            return f"❌ Liste gösterilemedi: {e}"
    
    def _launch_app(self, app_name: str) -> str:
        """Uygulama başlatma"""
        try:
            CONFIG_PATH = "data/apps_config.json"
            
            if not os.path.exists(CONFIG_PATH):
                return "❌ Uygulama yapılandırma dosyası bulunamadı"
            
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                apps = json.load(f)
            
            # İsmi normalleştir
            target = app_name.lower().strip()
            target = target.replace("'ı", "").replace("'i", "")
            if target and target[-1] in ["ı", "i", "u", "ü"]:
                target = target[:-1]
            
            if target in apps:
                subprocess.Popen(apps[target])
                return f"✅ {target.title()} başlatılıyor..."
            else:
                return f"❌ '{target}' bulunamadı. Mevcut: {', '.join(apps.keys())}"
        
        except Exception as e:
            return f"❌ Uygulama başlatılamadı: {e}"
    
    def _read_clipboard(self) -> str:
        """Pano okuma"""
        try:
            import pyperclip
            
            text = pyperclip.paste()
            
            if not text or not text.strip():
                return "📋 Pano şu an boş."
            
            word_count = len(text.split())
            return f"📋 PANO İÇERİĞİ ({word_count} kelime):\n\n{text}"
        
        except Exception as e:
            return f"❌ Pano okunamadı: {e}"
    
    def _read_pdf(self, filename: str) -> str:
        """PDF okuma"""
        try:
            import PyPDF2
            
            if not filename.endswith(".pdf"):
                filename += ".pdf"
            
            pdf_path = os.path.join("data", "sample_docs", filename)
            
            if not os.path.exists(pdf_path):
                return f"❌ Dosya bulunamadı: {filename}"
            
            text_content = ""
            
            with open(pdf_path, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                num_pages = len(reader.pages)
                
                # İlk 3 sayfa
                read_limit = min(3, num_pages)
                
                for i in range(read_limit):
                    page = reader.pages[i]
                    text_content += page.extract_text() + "\n"
            
            if not text_content.strip():
                return f"❌ PDF içeriği boş: {filename}"
            
            return f"📄 PDF OKUNDU ({filename} | {read_limit}/{num_pages} sayfa):\n\n{text_content}"
        
        except Exception as e:
            return f"❌ PDF okuma hatası: {e}"
    
    def _ocr_read(self) -> str:
        """OCR ile resim okuma"""
        try:
            from modules.vision import VisionSystem
            
            vision = VisionSystem()
            result = vision.read_from_clipboard()
            
            return f"👁️ OCR SONUCU:\n\n{result}"
        
        except Exception as e:
            return f"❌ OCR hatası: {e}"
    
    # === REGISTRY YÖNETİM FONKSİYONLARI ===
    
    def execute_tool(self, name: str, arguments: Dict) -> str:
        """Aracı çalıştırır"""
        
        tool = self._tools.get(name)
        
        if not tool:
            logger.error(f"Bilinmeyen araç: {name}")
            return f"❌ '{name}' adlı araç bulunamadı."
        
        try:
            func = tool["function"]
            result = func(**arguments)
            
            logger.info(f"✅ Tool başarılı: {name}")
            return str(result)
        
        except TypeError as e:
            logger.error(f"Parametre hatası ({name}): {e}")
            return f"❌ {name} aracına yanlış parametreler gönderildi."
        
        except Exception as e:
            logger.error(f"Tool hatası ({name}): {e}")
            return f"❌ {name} çalıştırılırken hata oluştu: {e}"
    
    def get_tools_schema(self) -> List[Dict]:
        """LLM için JSON Schema döndürür"""
        
        schemas = []
        
        for tool_name, tool_data in self._tools.items():
            schemas.append({
                "name": tool_data["name"],
                "description": tool_data["description"],
                "parameters": tool_data["parameters"]
            })
        
        return schemas
    
    def list_tools(self) -> List[str]:
        """Tüm araç isimlerini döndürür"""
        return list(self._tools.keys())


# Global instance
registry = ToolRegistry()