import streamlit as st
import requests
import os

# FastAPI URL from environment variable
FASTAPI_URL = os.getenv("FASTAPI_URL", "http://fastapi:8000")

# Page configuration
st.set_page_config(
    page_title="Dinamik Öğrenme Yolu Rehberi", 
    page_icon="📚", 
    layout="wide"
)

# Title
st.title("📚 Dinamik Öğrenme Yolu Rehberi")

# Sidebar for file upload
with st.sidebar:
    st.header("📁 Dosya Yükleme")
    
    # ✅ PDF upload olarak değiştirildi
    uploaded_file = st.file_uploader("Bir PDF dosyası seçin", type=['pdf'])
    
    if st.button("📤 Dosya Yükle", use_container_width=True) and uploaded_file is not None:
        with st.spinner("📄 PDF işleniyor..."):
            # ✅ PDF için multipart/form-data
            files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}
            try:
                # ✅ Endpoint değiştirildi
                response = requests.post(f"{FASTAPI_URL}/upload-pdf", files=files)
                
                if response.status_code == 200:
                    result = response.json()
                    st.success(f"✅ {result['message']}")
                    
                    # ✅ Daha güzel bilgi gösterimi
                    with st.expander("📊 Dosya Detayları"):
                        st.write(f"**Dosya Adı:** {result['filename']}")
                        st.write(f"**Boyut:** {result['size_bytes']:,} bytes ({result['size_bytes']/1024:.2f} KB)")
                        st.write(f"**Durum:** {result['status']}")
                else:
                    st.error(f"❌ Hata: {response.status_code}")
                    try:
                        st.json(response.json())
                    except:
                        st.text(response.text)
                        
            except requests.exceptions.ConnectionError:
                st.error("❌ FastAPI'ye bağlanılamadı. Servis çalışıyor mu?")
            except Exception as e:
                st.error(f"❌ Hata: {e}")
    
    # ✅ Bilgilendirme mesajı
    st.info("💡 PDF dosyanızı yükledikten sonra içeriği hakkında sorular sorabilirsiniz!")
    
    # ✅ Örnek sorular
    with st.expander("❓ Örnek Sorular"):
        st.markdown("""
        - PDF'teki ana konular nelerdir?
        - [Konu adı] hakkında açıklama yap
        - Bu dokümanı özetle
        - [Konsept] için örnek sorular üret
        - [Konu] için diyagram oluştur
        """)

# Chat interface
st.header("💬 Sohbet")

# ✅ Clear chat button
col1, col2 = st.columns([6, 1])
with col2:
    if st.button("🗑️ Temizle"):
        st.session_state.messages = []
        st.rerun()

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# React to user input
if prompt := st.chat_input("Sorunuzu yazın..."):
    # Display user message in chat message container
    with st.chat_message("user"):
        st.markdown(prompt)
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Get response from FastAPI
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        try:
            # Send request to FastAPI message endpoint
            payload = {"name": prompt}
            response = requests.post(
                f"{FASTAPI_URL}/message", 
                json=payload, 
                stream=True,
                timeout=60  # ✅ Timeout eklendi
            )
            
            if response.status_code == 200:
                # Stream the response
                for chunk in response.iter_content(chunk_size=1, decode_unicode=True):
                    if chunk:
                        full_response += chunk
                        message_placeholder.markdown(full_response + "▌")
                
                message_placeholder.markdown(full_response)
            else:
                full_response = f"❌ Hata: {response.status_code}"
                message_placeholder.markdown(full_response)
                
        except requests.exceptions.Timeout:
            full_response = "⏱️ İstek zaman aşımına uğradı. Lütfen tekrar deneyin."
            message_placeholder.markdown(full_response)
        except requests.exceptions.ConnectionError:
            full_response = "❌ FastAPI'ye bağlanılamadı. Servis çalışıyor mu?"
            message_placeholder.markdown(full_response)
        except Exception as e:
            full_response = f"❌ Beklenmeyen hata: {e}"
            message_placeholder.markdown(full_response)
    
    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": full_response})

# Footer
st.markdown("---")
st.markdown("*VBO AI Bootcamp - Streamlit + FastAPI + LangChain + Qdrant*")

# ✅ Sidebar'da sistem durumu
with st.sidebar:
    st.markdown("---")
    st.subheader("🔧 Sistem Durumu")
    
    try:
        health_response = requests.get(f"{FASTAPI_URL}/", timeout=5)
        if health_response.status_code == 200:
            st.success("✅ FastAPI Aktif")
        else:
            st.error("❌ FastAPI Yanıt Vermiyor")
    except:
        st.error("❌ FastAPI Bağlantısı Yok")