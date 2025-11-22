# 📚 Dinamik Öğrenme Yolu Rehberi (Dynamic Learning Path Guide)

!(/home/train/week_05_08/llm_final_project/llm_endtoend_proje/assest/hero.png)

Bu proje, yapay zeka destekli, kişiselleştirilmiş ve **çok modlu (multimodal)** bir öğrenme asistanıdır. Öğrencilerin kendi ders materyallerini yüklemelerine, bu materyaller hakkında soru sormalarına ve görselleri (diyagramlar, formüller, grafikler) analiz etmelerine olanak tanır.

Proje, LLM (Büyük Dil Modeli) teknolojilerini **LangChain**, **RAG (Retrieval-Augmented Generation)** ve **Vision** yetenekleriyle birleştiren uçtan uca bir çözümdür.

---

## ✨ Temel Özellikler

| Özellik | Açıklama | Anahtar Teknolojiler |
| :--- | :--- | :--- |
| **Akıllı PDF Analizi** | Kullanıcının yüklediği ders notlarını (PDF) işler, vektörleştirir ve içeriğe dayalı (halüsinasyonsuz) yanıtlar üretir. | LangChain, Qdrant, Google Embeddings |
| **Çok Modlu Analiz** | Ders slaytları, grafikler, formüller veya el yazısı notların fotoğraflarını yükleyerek detaylı açıklama ve adım adım çözüm alma. | Gemini 2.5 Flash **Vision API**, Pytesseract (OCR) |
| **Otomatik Grafik Oluşturma** | Görsel analiz veya metin tabanlı verilerden otomatik olarak grafikler (**Matplotlib**) çizerek veriyi görselleştirir. | Matplotlib, FastAPI |
| **Akıllı Retrieval** | Qdrant üzerinde **MMR (Maximum Marginal Relevance)** algoritması ile en alakalı ve çeşitli dokümanların getirilmesi. | Qdrant, LangChain |
| **Sohbet Hafızası** | Konuşma geçmişi korunur ve takip soruları sorulabilir (**History-Aware Retriever**). | LangChain Session Memory |

---

## 🏗️ Sistem Mimarisi

Proje, birbirine bağlı üç ana Docker Container'ından oluşan mikroservis mimarisi üzerine kurulmuştur.

### 🐳 Teknoloji Stack

| Bileşen | Görev | Temel Teknoloji |
| :--- | :--- | :--- |
| **Frontend (UI)** | Kullanıcı arayüzü, etkileşim, görsel ve PDF yükleme. | **Streamlit** |
| **Backend (API)** | LLM ile iletişim, RAG zincirinin yönetimi, görsel işleme, OCR ve grafik çizimi. | **FastAPI**, **LangChain** |
| **LLM/Embeddings** | Cevap üretimi ve vektörleştirme. | **Gemini 2.5 Flash**, **Google text-embedding-004** |
| **Vector DB** | Vektörleştirilmiş ders notlarının depolanması ve hızlı aranması. | **Qdrant** |

### 🌐 Mimarinin Akışı

Aşağıdaki diyagram, uygulamadaki veri akışını ve servisler arasındaki iletişimi göstermektedir.

```mermaid
graph TD
    A[Streamlit UI :8501] --> B{FastAPI Backend :8000};
    B --> C(Qdrant Vector DB :6333);
    B --> D[Gemini 2.5 Flash / Vision API];
    C --> B;
    D --> B;



##############
🔬 Pipeline Detayları
1. 📖 PDF İşleme Süreci (RAG)
Parsing: PDF'ler PyMuPDF ile metin olarak çıkarılır.

Chunking: Metinler, RecursiveCharacterTextSplitter kullanılarak 1500 karakterlik parçalara (200 overlap) bölünür.

Embedding: Parçalar, yüksek kaliteli Google text-embedding-004 ile vektörleştirilir.

Storage: Vektörler, Qdrant veritabanına kaydedilir.

2. 💬 Soru-Cevap Süreci (Retrieval)
Question Reformulation: Yeni gelen soru, History-aware retriever ile geçmiş konuşma bağlamına göre yeniden düzenlenir.

Vector Search (MMR): Qdrant'ta MMR (Maximum Marginal Relevance) algoritması (k=3, fetch_k=10) kullanılarak en alakalı dokümanlar getirilir. Bu, hem alaka düzeyini hem de doküman çeşitliliğini maksimize eder.

LLM Generation: Getirilen Context, yeniden düzenlenen soru ve Sohbet Geçmişi ile birlikte Gemini 2.5 Flash modeline gönderilerek nihai yanıt üretilir.

3. 🖼️ Görsel Analiz Süreci
OCR ve Vision: Yüklenen görsel, hem Pytesseract (metin çıkarımı) hem de Gemini 2.5 Flash Vision API ile detaylı analiz için işlenir.

Math Solving: Görseldeki matematik problemleri adım adım çözülür.

Graph Generation: Analiz metninde veri tespit edilirse, Matplotlib ile otomatik olarak grafik çizilir ve yanıtla birlikte döndürülür.

⚙️ Kurulum ve Çalıştırma
Projenin çalıştırılması için Docker ve Docker Compose gereklidir.

1. 🔑 Ön Koşullar
docker-compose.yml dosyasının bulunduğu dizinde Gemini API Key tanımlanmalıdır.

Bash

export GEMINI_API_KEY="SİZİN_ANAHTARINIZ"
2. 🚀 Başlatma
Aşağıdaki komut, tüm servisleri (Streamlit, FastAPI ve Qdrant) ayağa kaldırır:

Bash

# Proje dizininde
docker-compose up --build
3. 🖥️ Erişim
Uygulamaya tarayıcınızdan erişin:

http://localhost:8501
4. 📝 Kullanım
Uygulama açıldığında Sidebar üzerinden PDF yükleyerek RAG veritabanını oluşturun.

"🤖 Asistan" sayfasına gidin.

Görsel Analiz bölümünden ders notlarınızın veya formüllerin fotoğrafını yükleyin.

Sohbet bölümünden yüklediğiniz içerik hakkında sorular sorun.

🎓 Proje Detayları
Teknik Odak Noktaları: Uçtan uca RAG pipeline kurulumu, LangChain ile Agent mimarisi, Docker/FastAPI ile üretim ortamı simülasyonu, Multimodalite (Vision) entegrasyonu.

Geliştirici: [Adınızı Soyadınızı Buraya Yazın]

Tarih: [Proje Tamamlanma Tarihini Buraya Yazın]

VBO AI & LLM Bootcamp Bitirme Projesi
