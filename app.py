import streamlit as st
import requests, os, base64
from PIL import Image

FASTAPI_URL = os.getenv("FASTAPI_URL", "http://fastapi:8000")
st.set_page_config(page_title="Dinamik Öğrenme Yolu", page_icon="📚", layout="wide")

# Session state başlatma
if 'page' not in st.session_state:
    st.session_state.page = "home"

# Sidebar navigasyon
with st.sidebar:
    st.header("🎓 Menü")
    if st.button("🏠 Ana Sayfa", use_container_width=True):
        st.session_state.page = "home"
        st.rerun()
    if st.button("🤖 Asistan", use_container_width=True):
        st.session_state.page = "assistant"
        st.rerun()
    
    st.markdown("---")
    
    # PDF yükleme (sadece asistan sayfasında aktif)
    if st.session_state.page == "assistant":
        st.header("📁 PDF Yükleme")
        uploaded_file = st.file_uploader("PDF seçin", type=['pdf'])
        if st.button("📤 Dosya Yükle") and uploaded_file:
            files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}
            response = requests.post(f"{FASTAPI_URL}/upload-pdf", files=files)
            if response.status_code==200:
                result=response.json()
                st.success(result["message"])
                with st.expander("📊 Dosya Detayları"):
                    st.write(f"**Dosya:** {result['filename']}")
                    st.write(f"**Boyut:** {result['size_bytes']/1024:.2f} KB")
            else:
                st.error(response.text)

# ============================================
# ANA SAYFA - Tanıtım
# ============================================
if st.session_state.page == "home":
    # Hero Section
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.title("🎓 Dinamik Öğrenme Yolu Rehberi")
        st.markdown("### Yapay Zeka Destekli Kişiselleştirilmiş Öğrenme Asistanınız")
        
        st.markdown("""
        **Dinamik Öğrenme Yolu Rehberi** ile öğrenme deneyiminizi kişiselleştirin!
        
        ✨ **Özellikler:**
        - 📚 **Akıllı PDF Analizi**: Ders notlarınızı yükleyin, yapay zeka anlasın ve sorularınızı yanıtlasın
        - 🖼️ **Görsel Tanıma**: Ders slaytı, diyagram, grafik ve formülleri fotoğrafla, detaylı açıklama al
        - ✍️ **El Yazısı OCR**: El yazısı notlarınızı tarayın, metne dönüştürün ve analiz ettirin
        - 📊 **Grafik Analizi**: Görsellerden veri noktalarını çıkarır, yorumlar ve yeni grafikler oluşturur
        - 🧮 **Matematik Çözücü**: Matematik problemlerini fotoğraftan algılar, adım adım çözüm önerir
        - 💬 **Akıllı Sohbet**: Yüklediğiniz içerikler hakkında soru sorun, bağlamsal yanıtlar alın
        - 🧠 **Konuşma Hafızası**: Sohbet geçmişiniz korunur, takip soruları sorabilirsiniz
        """)
        
        st.markdown("---")
        
        # CTA Butonu
        if st.button("🚀 Hemen Başla", use_container_width=True, type="primary"):
            st.session_state.page = "assistant"
            st.rerun()
    
    with col2:
        # Görsel ekle
        image_path = "assest/hero.png"  # Sizin klasör adınız
        
        if os.path.exists(image_path):
            try:
                img = Image.open(image_path)
                st.image(img, use_container_width=True, caption="Yapay Zeka ile Öğrenme")
            except Exception as e:
                st.info("🖼️ Görsel yüklenemedi")
        else:
            # Görsel yoksa placeholder
            st.markdown("### 🎨 Proje Görseli")
            st.info("""
            🤖 **Yapay Zeka ile Öğrenme**
            
            Görsel eklemek için:
            1. `assest` klasöründe `hero.png` dosyası olmalı
            2. Path: `/home/train/week_05_08/llm_final_project/llm_endtoend_proje/assest/hero.png`
            """)
    
    # Özellikler Bölümü
    st.markdown("---")
    st.markdown("## 🎯 Nasıl Çalışır?")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("### 📚 PDF İşleme & Embedding")
        st.markdown("""
        **PyMuPDF + Google Embeddings**
        - PDF'ler PyMuPDF ile yüklenir
        - Metinler 1500 karakterlik parçalara bölünür
        - Google text-embedding-004 ile vektörleştirilir
        - Qdrant vektör veritabanına kaydedilir
        """)
    
    with col2:
        st.markdown("### 🔍 RAG Chain & Retrieval")
        st.markdown("""
        **LangChain + Gemini 2.5 Flash**
        - Sorular history-aware retriever ile işlenir
        - Qdrant'tan ilgili dokümanlar MMR ile getirilir (k=3)
        - Context + Sohbet geçmişi ile yanıt üretilir
        - Session bazlı sohbet hafızası
        """)
    
    with col3:
        st.markdown("### 🖼️ OCR & Görsel Analiz")
        st.markdown("""
        **Tesseract + Gemini Vision**
        - Pytesseract ile OCR işlenir
        - Gemini 2.5 Flash görsel analiz yapar
        - Matematik problemleri adım adım çözülür
        - Grafik verileri otomatik çizilir (Matplotlib)
        """)
    
    st.markdown("---")
    
    # Mimari Bölümü
    st.markdown("## 🏗️ Sistem Mimarisi")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🐳 Docker Containerları")
        st.code("""
        ┌─────────────────────┐
        │   Streamlit UI      │ :8501
        │   (Frontend)        │
        └──────────┬──────────┘
                   │
        ┌──────────▼──────────┐
        │   FastAPI Backend   │ :8000
        │   (RAG + LangChain) │
        └──────────┬──────────┘
                   │
        ┌──────────▼──────────┐
        │   Qdrant Vector DB  │ :6333
        │   (Embeddings)      │
        └─────────────────────┘
        """, language="text")
    
    with col2:
        st.markdown("### 🔧 Teknoloji Stack")
        st.markdown("""
        **Backend:**
        - FastAPI (REST API)
        - LangChain (RAG Framework)
        - Gemini 2.5 Flash (LLM)
        - Google text-embedding-004
        
        **Vector DB:**
        - Qdrant (Vektör Arama)
        - MMR Retrieval
        
        **Processing:**
        - PyMuPDF (PDF Parser)
        - Pytesseract (OCR)
        - Matplotlib (Grafik)
        """)
    
    # Ek bilgi bölümü
    st.markdown("---")
    st.markdown("## 🔬 RAG Pipeline Detayları")
    
    with st.expander("📖 PDF İşleme Süreci"):
        st.markdown("""
        1. **Yükleme**: PDF dosyası `/tmp/uploads` dizinine kaydedilir
        2. **Parsing**: PyMuPDF ile metin çıkarılır
        3. **Chunking**: RecursiveCharacterTextSplitter (1500 char, overlap 200)
        4. **Embedding**: Google text-embedding-004 ile vektörleştirilir
        5. **Storage**: Qdrant koleksiyonuna (`vbo-de-bootcamp`) kaydedilir
        """)
    
    with st.expander("🔍 Soru-Cevap Süreci"):
        st.markdown("""
        1. **Question Reformulation**: History-aware retriever ile soru yeniden düzenlenir
        2. **Vector Search**: Qdrant'ta MMR algoritması ile arama (k=3, fetch_k=10)
        3. **Context Building**: İlgili dokümanlar birleştirilir
        4. **LLM Generation**: Gemini 2.5 Flash ile yanıt üretilir
        5. **Session Memory**: Sohbet geçmişi korunur
        """)
    
    with st.expander("🖼️ Görsel Analiz Süreci"):
        st.markdown("""
        1. **OCR**: Pytesseract ile metin çıkarılır ve Qdrant'a eklenir
        2. **Vision Analysis**: Gemini 2.5 Flash Vision API ile detaylı analiz
        3. **Math Solving**: Matematik problemleri adım adım çözülür
        4. **Graph Detection**: "GRAPH:" formatında veri varsa Matplotlib ile çizilir
        5. **Response**: Analiz + Görsel (varsa) döndürülür
        """)
    
    st.markdown("---")
    st.markdown("## 📊 Özellikler")
    st.info("""
    ✅ **Multi-modal Analiz**: PDF, görsel ve metin desteği
    
    ✅ **Akıllı Retrieval**: MMR algoritması ile en alakalı içerik
    
    ✅ **Session Memory**: Konuşma geçmişi korunur
    
    ✅ **Graph Generation**: Otomatik grafik oluşturma
    
    ✅ **Scalable**: Docker-compose ile kolay deploy
    """)
    
    st.markdown("---")
    st.markdown("*VBO AI&LLM Bootcamp - Streamlit + FastAPI + LangChain + Qdrant*")

# ============================================
# ASİSTAN SAYFASI (Mevcut Kodunuz)
# ============================================
elif st.session_state.page == "assistant":
    st.title("📚 Dinamik Öğrenme Yolu Rehberi")
    
    # Ana sayfa - Görsel yükleme ve analiz
    st.header("📸 Görsel Analiz")
    st.markdown("Anlamadığınız bir konu veya sorunun fotoğrafını yükleyin, yapay zeka analiz etsin.")

    col1, col2 = st.columns([2, 1])

    with col1:
        uploaded_image = st.file_uploader(
            "Görseli seçin", 
            type=["jpg", "png", "jpeg"],
            help="Ders notu, soru, formül veya grafik içeren görselleri yükleyebilirsiniz"
        )

    with col2:
        if uploaded_image:
            st.image(uploaded_image, caption="Yüklenen Görsel", use_container_width=True)

    # Görsel analiz butonu
    if uploaded_image:
        if st.button("🔍 Görseli Analiz Et", type="primary", use_container_width=True):
            files = {"file": (uploaded_image.name, uploaded_image.getvalue(), uploaded_image.type)}
            
            with st.spinner("Görsel analiz ediliyor..."):
                try:
                    response = requests.post(f"{FASTAPI_URL}/upload-image", files=files, timeout=60)
                    
                    if response.status_code == 200:
                        data = response.json()
                        st.success(data.get("message", "Görsel başarıyla işlendi!"))
                        
                        # Analiz sonucunu göster
                        if "analysis" in data:
                            st.markdown("### 📖 Analiz Sonucu")
                            st.info(data["analysis"])
                        
                        # Grafik varsa göster
                        if data.get("graph_image"):
                            st.markdown("### 📊 Grafik")
                            st.image(base64.b64decode(data["graph_image"]), use_container_width=True)
                    else:
                        st.error(f"Hata: {response.status_code} - {response.text}")
                        
                except Exception as e:
                    st.error(f"İstek hatası: {str(e)}")

    st.markdown("---")

    # Chat interface
    st.header("💬 Sohbet")
    st.markdown("Yüklediğiniz PDF'ler hakkında soru sorun veya konu anlatımı isteyin.")

    if "messages" not in st.session_state:
        st.session_state.messages=[]

    for m in st.session_state.messages:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])

    if prompt := st.chat_input("Sorunuzu yazın..."):
        with st.chat_message("user"):
            st.markdown(prompt)
        st.session_state.messages.append({"role":"user","content":prompt})
        
        with st.chat_message("assistant"):
            msg_placeholder = st.empty()
            full_response = ""
            try:
                payload = {"name": prompt}
                response = requests.post(f"{FASTAPI_URL}/message", json=payload, timeout=60)
                
                if response.status_code == 200:
                    result = response.json()
                    full_response = result.get("text", "")
                    msg_placeholder.markdown(full_response)
                    
                    # Eğer grafik varsa göster
                    if result.get("graph_image"):
                        st.image(base64.b64decode(result["graph_image"]), use_container_width=True)
                else:
                    msg_placeholder.markdown(f"❌ Hata: {response.status_code}")
            except Exception as e:
                msg_placeholder.markdown(f"❌ Hata: {e}")
        
        st.session_state.messages.append({"role": "assistant", "content": full_response})

    st.markdown("---")
    st.markdown("*VBO AI&LLM Bootcamp - Streamlit + FastAPI + LangChain + Qdrant*")