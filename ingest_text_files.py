__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

import os  # ✅ DÜZELTME: os'u ayrı import et
from uuid import uuid4
from dotenv import load_dotenv
from langchain_google_genai.embeddings import GoogleGenerativeAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_qdrant import QdrantVectorStore
from langchain_community.document_loaders import DirectoryLoader
from langchain_community.document_loaders import PyMuPDFLoader

load_dotenv()

embeddings = GoogleGenerativeAIEmbeddings(
    model="text-embedding-004",
    task_type="RETRIEVAL_DOCUMENT"
)

url = "http://qdrant:6333"
#url = "http://localhost:6333"
COLLECTION_NAME = "vbo-de-bootcamp"

# Returns QdrantVectorStore object + ingesting documents
def ingest_from_docs(upload_dir: str = "/tmp/uploads"):
    try:
        # Dizini oluştur
        os.makedirs(upload_dir, exist_ok=True)
        
        # PDF dosyalarını yükle
        loader = DirectoryLoader(
            upload_dir,
            glob="**/*.pdf",  # Sadece PDF dosyalarını al
            loader_cls=PyMuPDFLoader,  # PyMuPDF kullanarak PDF'leri oku
            show_progress=True
        )
        
        print(f"📁 {upload_dir} dizininden PDF'ler okunuyor...")
        raw_documents = loader.load()
        
        if not raw_documents:
            print(f"⚠️  {upload_dir} dizininde PDF bulunamadı")
            return False

        print(f"✓ {len(raw_documents)} PDF sayfası okundu")

        # ✅ DÜZELTME: İndentasyon düzeltildi - try bloğu içinde
        # Split raw pdf content into chunks
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1500,
            chunk_overlap=200,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )

        docs = text_splitter.split_documents(raw_documents)
        print(f"✓ {len(docs)} parçaya bölündü")

        # Qdrant'a kaydet
        print("💾 Qdrant'a kaydediliyor...")
        QdrantVectorStore.from_documents(
            docs,
            embeddings,
            url=url,
            prefer_grpc=True,
            collection_name=COLLECTION_NAME,
        )

        print(f"✅ Toplam {len(docs)} parça başarıyla kaydedildi!")
        return True  # ✅ DÜZELTME: True döndür
        
    except Exception as e:  # ✅ DÜZELTME: Exception handling eklendi
        print(f"❌ Hata oluştu: {e}")
        import traceback
        traceback.print_exc()  # Detaylı hata mesajı
        return False

# ✅ DÜZELTME: Fonksiyon ismi düzeltildi
def get_retriever():
    try:
        vector_store = QdrantVectorStore.from_existing_collection(
            collection_name=COLLECTION_NAME,
            embedding=embeddings,
            url=url,
            prefer_grpc=True
        )

        bootcamp_retriever = vector_store.as_retriever(
            search_type="mmr", 
            search_kwargs={"k": 3, "fetch_k": 10}
        )
        
        print("✓ Retriever hazır")
        return bootcamp_retriever
        
    except Exception as e:  # ✅ DÜZELTME: Exception handling eklendi
        print(f"❌ Retriever oluşturulurken hata: {e}")
        import traceback
        traceback.print_exc()
        raise
    