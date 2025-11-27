from ingest_text_files import get_retriever, ingest_from_docs, ingest_from_image
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
import os, io, base64, json
from PIL import Image
import matplotlib.pyplot as plt
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="VBO DE Bootcamp RAG Assistant")

UPLOAD_DIR = "/tmp/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

print("📚 Başlangıç kontrol ediliyor...")
retriever = None

try:
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

api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    raise ValueError("❌ GOOGLE_API_KEY .env'de bulunamadı!")

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash", 
    temperature=0.7,
    google_api_key=api_key
)

store = {}
def get_session_history(session_id: str) -> BaseChatMessageHistory:
    if session_id not in store:
        store[session_id] = ChatMessageHistory()
    return store[session_id]

contextualize_q_prompt = ChatPromptTemplate.from_messages([
    ("system", "Given chat history and latest question, reformulate if needed"),
    MessagesPlaceholder("chat_history"),
    ("human", "{input}"),
])

qa_prompt_template = ChatPromptTemplate.from_messages([
    ("system", """Sen matematik ders notu asistanısın. 
    Aşağıdaki bağlamı kullanarak soruyu yanıtla.
    
    ÖNEMLİ:
    - Kapak, önsöz, fotoğraf gibi kısımları yoksay
    - Önce bağlamda cevabı ara
    - Bağlamda yoksa, kendi bilgini kullan (LLM olarak)
    - Matematiksel soruları adım adım çöz
    - Gerekirse diyagram veya grafik oluştur
    📊 GRAFİK/ŞEKİL İSTENMESİ:
    Kullanıcı grafik, diyagram, şekil, çizim isterse:
    1. Cevabı açıkla
    2. Sonra ŞU FORMATTA grafiksel gösterim ver:
    
    GRAPH: [x_değerleri], [y_değerleri]
    
    ÖRNEKLER:
    - Parabol: GRAPH: [-2,-1,0,1,2], [4,1,0,1,4]
    - Doğru: GRAPH: [0,1,2,3], [0,2,4,6]
    - Trigonometrik: GRAPH: [0,1.57,3.14,4.71,6.28], [0,1,0,-1,0]
    - Sütun grafik: GRAPH: [0,1,2,3], [10,20,15,25]
    - Herhangi veri: GRAPH: [x1,x2,x3,...], [y1,y2,y3,...]
    
    Bağlam:
    {context}
    """),
    MessagesPlaceholder("chat_history"),
    ("human", "{input}"),
])

history_aware_retriever = None
question_answer_chain = None
rag_chain = None
qa_chain = None

def initialize_chains():
    global history_aware_retriever, question_answer_chain, rag_chain, qa_chain
    if not retriever:
        print("⚠️  Retriever yok")
        return False
    try:
        history_aware_retriever = create_history_aware_retriever(
            llm, retriever, contextualize_q_prompt
        )
        question_answer_chain = create_stuff_documents_chain(llm, qa_prompt_template)
        rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)
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

if retriever:
    initialize_chains()

class Message(BaseModel):
    name: str

@app.get("/")
def root():
    return {
        "message": "VBO LLM Bootcamp RAG Assistant",
        "status": "ready" if retriever else "waiting_for_documents",
        "version": "3.0"
    }

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "retriever_ready": retriever is not None,
        "active_sessions": len(store)
    }

# Streaming mesaj endpoint
@app.post("/message")
def send_request(message: Message):
    print(f"💬 Soru alındı: {message.name}")
    
    if not retriever:
        raise HTTPException(
            status_code=503,
            detail="Henüz doküman yüklenmedi. PDF yükleyin."
        )
    
    if not qa_chain:
        raise HTTPException(
            status_code=503,
            detail="Chain başlatılmadı. PDF yükleyin."
        )
    
    try:
        # RAG chain ile yanıt al
        session_id = "default_session"  # Her kullanıcı için farklı olabilir
        
        print(f"🔍 RAG chain çalıştırılıyor...")
        result = qa_chain.invoke(
            {"input": message.name},
            config={"configurable": {"session_id": session_id}}
        )
        
        # ✅ DOĞRU: result bir dict, "answer" anahtarından yanıtı al
        answer = result.get("answer", "Yanıt bulunamadı.")
        
        print(f"✅ Yanıt oluşturuldu: {len(answer)} karakter")
        
        # Grafik kontrolü (opsiyonel - eğer LLM JSON döndürürse)
        graph_image_base64 = None
        try:
            # Eğer yanıt JSON formatında grafik verisi içeriyorsa
            data = json.loads(answer)
            if data.get("type") == "graph":
                y = data.get("data", [])
                plt.figure()
                plt.plot(y)
                buf = io.BytesIO()
                plt.savefig(buf, format="png")
                buf.seek(0)
                graph_image_base64 = base64.b64encode(buf.read()).decode("utf-8")
                plt.close()
        except:
            # JSON değilse, GRAPH: formatını kontrol et
            if "GRAPH:" in answer:
                try:
                    import re, ast
                    graph_line = re.search(r'GRAPH:\s*\[.*?\],\s*\[.*?\]', answer)
                    if graph_line:
                        coords = graph_line.group().replace("GRAPH:", "").strip()
                        x_vals, y_vals = ast.literal_eval(f"[{coords}]")
                        
                        plt.figure(figsize=(8, 6))
                        plt.plot(x_vals, y_vals, marker='o')
                        plt.grid(True)
                        plt.title("Grafik")
                        
                        buf = io.BytesIO()
                        plt.savefig(buf, format="png", bbox_inches='tight')
                        buf.seek(0)
                        graph_image_base64 = base64.b64encode(buf.read()).decode("utf-8")
                        plt.close()
                        print("📊 Grafik oluşturuldu")
                        
                        # GRAPH satırını temizle
                        answer = re.sub(r'GRAPH:\s*\[.*?\],\s*\[.*?\]', '', answer).strip()
                except Exception as graph_error:
                    print(f"⚠️ Grafik oluşturulamadı: {graph_error}")

        return {"text": answer, "graph_image": graph_image_base64}

    except Exception as e:
        print(f"❌ Sohbet hatası: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/upload-pdf")
async def upload_pdf(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Sadece PDF kabul edilir")
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)
    success = ingest_from_docs(UPLOAD_DIR)
    if not success:
        raise HTTPException(status_code=500, detail="PDF işlenemedi")
    global retriever
    retriever = get_retriever()
    initialize_chains()
    return {"status":"success","filename":file.filename,"size_bytes":len(content),
            "message":f"{file.filename} başarıyla yüklendi ve işlendi"}

@app.post("/upload-image")
async def analyze_image(file: UploadFile = File(...)):
    print(f"📸 Görsel alındı: {file.filename}")
    
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Sadece görsel yükleyin")
    
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)
    
    success = ingest_from_image(file_path)
    if not success:
        raise HTTPException(status_code=500, detail="Görsel işlenemedi")
    
    try:
        with open(file_path, "rb") as img_file:
            image_data = base64.b64encode(img_file.read()).decode("utf-8")
        
        from langchain_core.messages import HumanMessage
        
        # Görsel analizi
        analysis_message = HumanMessage(
            content=[
                {
                    "type": "text", 
                    "text": """Bu görseli detaylı analiz et. 
                    Eğer bir matematik sorusu varsa adım adım çöz.
                    Eğer bir grafik çizilmesi gerekiyorsa, son satırda şu formatta belirt:
                    GRAPH: [x_değerleri], [y_değerleri]
                    Örnek: GRAPH: [0,1,2,3,4], [0,1,4,9,16]
                    """
                },
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}
                }
            ]
        )
        
        response = llm.invoke([analysis_message])
        analysis_text = response.content
        
        print(f"✅ Analiz: {analysis_text[:200]}...")
        
        # Grafik verisi var mı kontrol et
        graph_image_base64 = None
        if "GRAPH:" in analysis_text:
            try:
                import re
                import ast
                
                # GRAPH: satırını bul
                graph_line = re.search(r'GRAPH:\s*\[.*?\],\s*\[.*?\]', analysis_text)
                if graph_line:
                    # Verileri parse et
                    coords = graph_line.group().replace("GRAPH:", "").strip()
                    x_vals, y_vals = ast.literal_eval(f"[{coords}]")
                    
                    # Grafik çiz
                    plt.figure(figsize=(8, 6))
                    plt.plot(x_vals, y_vals, marker='o')
                    plt.grid(True)
                    plt.title("Grafik")
                    
                    buf = io.BytesIO()
                    plt.savefig(buf, format="png", bbox_inches='tight')
                    buf.seek(0)
                    graph_image_base64 = base64.b64encode(buf.read()).decode("utf-8")
                    plt.close()
                    
                    print("📊 Grafik oluşturuldu")
                    
                    # GRAPH satırını temizle
                    analysis_text = re.sub(r'GRAPH:\s*\[.*?\],\s*\[.*?\]', '', analysis_text).strip()
            except Exception as graph_error:
                print(f"⚠️ Grafik oluşturulamadı: {graph_error}")
        
        return {
            "status": "success",
            "message": "Görsel başarıyla analiz edildi",
            "analysis": analysis_text,
            "graph_image": graph_image_base64,
            "filename": file.filename
        }
        
    except Exception as e:
        print(f"❌ Hata: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Analiz hatası: {str(e)}")