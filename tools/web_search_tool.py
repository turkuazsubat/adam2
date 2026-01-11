import logging
import json
import urllib.parse
import urllib.request
import ssl

logger = logging.getLogger("WebSearch")

def unsafe_request(url):
    """
    CURL yerine Python'un yerel 'urllib' kütüphanesini kullanır.
    SSL sertifika hatalarını (CERTIFICATE_VERIFY_FAILED) yoksayar.
    Programı çökertmez.
    """
    try:
        # SSL Denetimini Devre Dışı Bırak (Güvenli değil ama çalışır)
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        
        # Bot gibi görünmemek için User-Agent
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        
        req = urllib.request.Request(url, headers=headers)
        
        # İsteği at
        with urllib.request.urlopen(req, context=ctx, timeout=5) as response:
            return response.read().decode('utf-8')
            
    except Exception as e:
        logger.error(f"İnternet İsteği Hatası: {e}")
        return None

def get_wikipedia_summary(title):
    try:
        encoded_title = urllib.parse.quote(title)
        url = f"https://tr.wikipedia.org/api/rest_v1/page/summary/{encoded_title}"
        
        json_response = unsafe_request(url)
        
        if json_response:
            data = json.loads(json_response)
            if data.get("type") == "disambiguation": return None
            return data.get("extract")
    except:
        pass
    return None

def search_wikipedia(query):
    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        query_enc = urllib.parse.quote(query)
        # Sadece başlık araması yap
        url = f"https://tr.wikipedia.org/w/api.php?action=opensearch&search={query_enc}&limit=1&format=json"
        with urllib.request.urlopen(url, context=ctx, timeout=3) as r:
            data = json.loads(r.read().decode('utf-8'))
            if data[1]:
                return f"Wikipedia: {data[1][0]} hakkında bilgi bulundu. (Detaylar kısıtlandı)."
    except: pass
    return "Bilgiye şu an ulaşılamıyor."