from ingest_text_files import get_retriever, ingest_from_docs  # ✅ get_retriever
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from langchain_google_genai.chat_models import ChatGoogleGenerativeAI
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from uuid import uuid4
import os

from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="VBO DE Bootcamp RAG Assistant")

# Upload dizini
UPLOAD_DIR = "/tmp/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ✅ İlk başta mevcut PDF'leri yükle (güvenli şekilde)
print("📚 Başlangıç kontrol ediliyor...")
retriever = None

try:
    # Dizinde PDF var mı kontrol et
    pdf_files = [f for f in os.listdir(UPLOAD_DIR) if f.endswith('.pdf')]
    
    if pdf_files:
        print(f"📄 {len(pdf_files)} PDF dosyası bulundu, yükleniyor...")
        success = ingest_from_docs(UPLOAD_DIR)
        if success:
            retriever = get_retriever()
            print("✅ Retriever hazır")
    else:
        print("⚠️  Başlangıçta PDF bulunamadı.")
except Exception as e:
    print(f"⚠️  Başlangıç yüklemesi atlandı: {e}")

# ✅ Model - Gemini 1.5 kullanın (2.0 henüz stable olmayabilir)
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",  # veya "gemini-1.5-pro"
    temperature=0.7
)

# Session store for chat history
store = {}

def get_session_history(session_id: str) -> BaseChatMessageHistory:
    if session_id not in store:
        store[session_id] = ChatMessageHistory()
    return store[session_id]

# Contextualize question prompt
contextualize_q_prompt = ChatPromptTemplate.from_messages([
    ("system", "Given a chat history and the latest user question which might reference context in the chat history, formulate a standalone question which can be understood without the chat history. Do NOT answer the question, just reformulate it if needed and otherwise return it as is."),
    MessagesPlaceholder("chat_history"),
    ("human", "{input}"),
])

# Answer question prompt template (global olarak tanımla)
qa_prompt_template = ChatPromptTemplate.from_messages([
    ("system", "Sen akıllı ders notu asistanısın. Sana sorulan soruları tanı ve açıkla, özetle, konsepti görselleştir, örnek sorular üret, diyagram oluştur.\n\nContext: {context}"),
    MessagesPlaceholder("chat_history"),
    ("human", "{input}"),
])

# ✅ Chain'leri başlat (eğer retriever varsa)
history_aware_retriever = None
question_answer_chain = None
rag_chain = None
qa_chain = None

def initialize_chains():
    """Chain'leri başlat veya yeniden başlat"""
    global history_aware_retriever, question_answer_chain, rag_chain, qa_chain
    
    if not retriever:
        print("⚠️  Retriever yok, chain'ler başlatılamadı")
        return False
    
    try:
        # Create history-aware retriever
        history_aware_retriever = create_history_aware_retriever(
            llm, retriever, contextualize_q_prompt
        )

        # Create question-answer chain
        question_answer_chain = create_stuff_documents_chain(llm, qa_prompt_template)

        # Create retrieval chain
        rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)

        # Add message history
        qa_chain = RunnableWithMessageHistory(
            rag_chain,
            get_session_history,
            input_messages_key="input",
            history_messages_key="chat_history",
            output_messages_key="answer",
        )
        
        print("✅ Chain'ler başlatıldı")
        return True
    except Exception as e:
        print(f"❌ Chain başlatma hatası: {e}")
        return False

# İlk chain başlatma
if retriever:
    initialize_chains()

# Pydantic model
class Message(BaseModel):
    name: str

# Root endpoint
@app.get("/")
def root():
    return {
        "message": "VBO DE Bootcamp RAG Assistant",
        "status": "ready" if retriever else "waiting_for_documents",
        "version": "1.0"
    }

# Health check endpoint
@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "retriever_ready": retriever is not None,
        "active_sessions": len(store)
    }

# Message endpoint with streaming
@app.post("/message")
def send_request(message: Message):
    # ✅ Retriever kontrolü
    if not retriever:
        raise HTTPException(
            status_code=503,
            detail="Henüz doküman yüklenmedi. Lütfen önce bir PDF yükleyin."
        )
    
    try:
        def generate_response():
            # Get relevant documents first
            docs = retriever.get_relevant_documents(message.name)
            
            if not docs:
                yield "⚠️ İlgili doküman bulunamadı. Lütfen daha spesifik bir soru sorun."
                return
            
            context = "\n\n".join([doc.page_content for doc in docs])
            
            # Create a simple prompt for streaming
            prompt = f"""Sen akıllı ders notu asistanısın. Sana sorulan soruları tanı ve açıkla, özetle, konsepti görselleştir, örnek sorular üret, diyagram oluştur.

Context: {context}

Soru: {message.name}

Cevap:"""
            
            # Stream directly from LLM
            for chunk in llm.stream(prompt):
                if chunk.content:
                    yield chunk.content
        
        return StreamingResponse(generate_response(), media_type="text/plain")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Hata: {str(e)}")

# PDF UPLOAD ENDPOINT
@app.post("/upload-pdf")
async def upload_pdf(file: UploadFile = File(...)):
    try:
        # Dosya tipini kontrol et
        if not file.filename.endswith(".pdf"):
            raise HTTPException(
                status_code=400, 
                detail="Sadece PDF dosyaları kabul edilir (.pdf)"
            )

        # Dosyayı kaydet
        file_path = os.path.join(UPLOAD_DIR, file.filename)
        
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)

        print(f"📄 {file.filename} kaydedildi, işleniyor...")
        
        # Qdrant'a yükle
        success = ingest_from_docs(UPLOAD_DIR)
        
        if not success:
            raise HTTPException(
                status_code=500, 
                detail="PDF işlenemedi"
            )

        # ✅ Global retriever'ı güncelle
        global retriever
        retriever = get_retriever()
        
        # ✅ Chain'leri yeniden başlat
        chain_success = initialize_chains()
        
        if not chain_success:
            raise HTTPException(
                status_code=500,
                detail="Chain'ler başlatılamadı"
            )

        print("✅ PDF yüklendi ve sistem güncellendi")

        return {
            "status": "success",
            "filename": file.filename,
            "size_bytes": len(content),
            "message": f"✅ {file.filename} başarıyla yüklendi ve işlendi"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500, 
            detail=f"Hata: {str(e)}"
        )


# if __name__=='__main__':
#     session_id = "user123"
    
#     print("Welcome to the interactive Travel Assistant! Type 'quit' to exit.")
    
#     while True:
#         question = input("\nYour question: ")
        
#         if question.lower() in ['quit', 'exit', 'q']:
#             print("Goodbye!")
#             break
            
#         try:
#             response = qa_chain.invoke(
#                 {"input": question},
#                 config={"configurable": {"session_id": session_id}}
#             )
#             print(f"\nAnswer: {response['answer']}")
#         except Exception as e:
#             print(f"Error: {e}")