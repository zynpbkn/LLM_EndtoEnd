__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

import os
from uuid import uuid4
from dotenv import load_dotenv
from langchain_google_genai.embeddings import GoogleGenerativeAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_qdrant import QdrantVectorStore
from langchain_community.document_loaders import DirectoryLoader, PyMuPDFLoader
from PIL import Image
import pytesseract

load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    raise ValueError("❌ GOOGLE_API_KEY .env'de bulunamadı!")

embeddings = GoogleGenerativeAIEmbeddings(
    model="text-embedding-004", 
    task_type="RETRIEVAL_DOCUMENT",
    google_api_key=api_key
)
url = "http://qdrant:6333"
COLLECTION_NAME = "vbo-de-bootcamp"

def ingest_from_docs(upload_dir: str = "/tmp/uploads"):
    try:
        os.makedirs(upload_dir, exist_ok=True)
        loader = DirectoryLoader(upload_dir, glob="**/*.pdf", loader_cls=PyMuPDFLoader, show_progress=True)
        raw_documents = loader.load()
        if not raw_documents:
            print(f"⚠️  {upload_dir} dizininde PDF bulunamadı")
            return False
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1500, chunk_overlap=200)
        docs = text_splitter.split_documents(raw_documents)
        QdrantVectorStore.from_documents(docs, embeddings, url=url, collection_name=COLLECTION_NAME)
        return True
    except Exception as e:
        print(f"❌ Hata: {e}")
        return False

def ingest_from_image(file_path: str):
    try:
        img = Image.open(file_path)
        text = pytesseract.image_to_string(img)
        from langchain.docstore.document import Document
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1500, chunk_overlap=200)
        docs = text_splitter.split_text(text)
        docs = [Document(page_content=d) for d in docs]
        QdrantVectorStore.from_documents(docs, embeddings, url=url, collection_name=COLLECTION_NAME)
        return True
    except Exception as e:
        print(f"❌ Görsel işlenirken hata: {e}")
        return False

def get_retriever():
    try:
        vector_store = QdrantVectorStore.from_existing_collection(
            collection_name=COLLECTION_NAME,
            embedding=embeddings,
            url=url,
            prefer_grpc=True
        )
        bootcamp_retriever = vector_store.as_retriever(search_type="mmr", search_kwargs={"k":3,"fetch_k":10})
        return bootcamp_retriever
    except Exception as e:
        print(f"❌ Retriever oluşturulurken hata: {e}")
        raise
