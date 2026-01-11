
"""
ADAM 2.0 Sistem Testi
Tüm modüllerin çalışıp çalışmadığını kontrol eder
"""
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')

print("="*60)
print("ADAM 2.0 - SİSTEM TESTİ")
print("="*60)

# Test 1: Import kontrolü
print("\n1️⃣ Modül import kontrolü...")
try:
    from core.qwen_brain import QwenBrain
    from core.context_builder import ContextBuilder
    from core.decision_engine import DecisionEngine
    from memory.manager import MemoryManager
    from memory.profile_manager import ProfileManager
    from tools.registry import registry
    from modules.observer import GhostObserver
    print("✅ Tüm modüller başarıyla import edildi")
except Exception as e:
    print(f"❌ Import hatası: {e}")
    exit(1)

# Test 2: Model yükleme
print("\n2️⃣ Qwen modeli yükleniyor...")
try:
    brain = QwenBrain(model_path="models/qwen_agent.gguf")
    print("✅ Model başarıyla yüklendi")
except Exception as e:
    print(f"❌ Model yükleme hatası: {e}")
    print("    Kontrol edin: models/qwen_agent.gguf dosyası var mı?")
    exit(1)

# Test 3: Basit sohbet
print("\n3️⃣ Basit sohbet testi...")
try:
    response = brain.simple_chat("Merhaba, adın ne?")
    print(f"✅ Qwen cevabı: {response}")
except Exception as e:
    print(f"❌ Sohbet hatası: {e}")

# Test 4: Tool Registry
print("\n4️⃣ Tool Registry kontrolü...")
try:
    tools = registry.list_tools()
    print(f"✅ {len(tools)} araç kaydedildi:")
    for tool in tools:
        print(f"   - {tool}")
except Exception as e:
    print(f"❌ Registry hatası: {e}")

# Test 5: Hafıza sistemi
print("\n5️⃣ Hafıza sistemi kontrolü...")
try:
    memory = MemoryManager()
    profile = ProfileManager(memory)
    
    # Test kaydı
    profile.set("test_key", "test_value")
    result = profile.get("test_key")
    
    if result == "test_value":
        print("✅ Hafıza sistemi çalışıyor")
    else:
        print("❌ Hafıza okuma/yazma hatası")
    
    memory.close()
except Exception as e:
    print(f"❌ Hafıza hatası: {e}")

# Test 6: Function Calling
print("\n6️⃣ Function Calling testi...")
try:
    memory = MemoryManager()
    profile = ProfileManager(memory)
    
    engine = DecisionEngine(
        memory_manager=memory,
        profile_manager=profile,
        model_path="models/qwen_agent.gguf"
    )
    
    # Test senaryosu
    response = engine.process_input("Yarın doktora gideceğimi not al")
    print(f"✅ Engine cevabı: {response}")
    
    memory.close()
except Exception as e:
    print(f"❌ Engine hatası: {e}")

print("\n" + "="*60)
print("TEST TAMAMLANDI")
print("="*60)
print("\nEğer tüm testler ✅ ise, GUI'yi başlatabilirsin:")
print("  python gui_app.py")