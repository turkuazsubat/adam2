import os
import logging
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from logger import log_event

logger = logging.getLogger("SemanticEngine")

class SemanticEngine:
    def __init__(self, model_name='paraphrase-multilingual-MiniLM-L12-v2'):
        self.model_name = model_name
        self.model = None
        # Mutlak yol kullanarak hatayı önleyelim
        self.notes_file = os.path.abspath("data/notes.txt")
        self.initialize_model()

    def initialize_model(self):
        try:
            # Model yüklenirken RAM kullanımı zirve yapar
            print(f"🧠 Hafıza motoru hazırlanıyor...")
            self.model = SentenceTransformer(self.model_name)
        except Exception as e:
            print(f"⚠️ Hafıza motoru yüklenemedi, sistem kısıtlı çalışacak: {e}")
            self.model = None
            
    def encode(self, text):
        if self.model is None: return None
        return self.model.encode(text)

    def search_notes(self, query, min_score=0.20): # <-- EŞİK DÜŞÜRÜLDÜ (%20 yeterli)
        """
        Daha hassas arama yapar.
        """
        if not os.path.exists(self.notes_file):
            return f"Hata: Not dosyası bulunamadı ({self.notes_file})"

        try:
            with open(self.notes_file, 'r', encoding='utf-8') as f:
                lines = [line.strip() for line in f.readlines() if line.strip()]

            if not lines:
                return "Not defterin boş."

            print(f"🔍 Taranan Not Sayısı: {len(lines)}") # Debug

            query_vec = self.encode(query)
            corpus_vecs = self.model.encode(lines)

            similarities = cosine_similarity(query_vec.reshape(1, -1), corpus_vecs)[0]
            top_indices = np.argsort(similarities)[::-1][:3]
            
            results = []
            found = False
            
            for idx in top_indices:
                score = similarities[idx]
                # Debug için konsola bas
                print(f"   > Aday: '{lines[idx][:30]}...' Skor: {score:.2f}")
                
                if score > min_score:
                    results.append(f"- {lines[idx]} (Eşleşme: %{int(score*100)})")
                    found = True
            
            if found:
                return f"🧠 Notlarında şunları buldum:\n" + "\n".join(results)
            else:
                return "Notlarında buna yakın bir şey bulamadım."

        except Exception as e:
            logger.error(f"Arama Hatası: {e}")
            return f"Arama hatası: {e}"