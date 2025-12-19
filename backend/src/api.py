from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from prometheus_fastapi_instrumentator import Instrumentator
from src.rag import RAGEngine

app = FastAPI(
    title="Arxiv Paper RAG Service",
    description="최신 논문 기반 질의응답 API",
    version="1.0.0"
)

# --- CORS 설정 추가 ---
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,            # 특정 도메인만 허용
    allow_credentials=True,
    allow_methods=["*"],              # GET, POST, OPTIONS 등 모든 메서드 허용
    allow_headers=["*"],              # 모든 헤더 허용
)

# 서버 시작 시 Prometheus 메트릭 측정 시작
Instrumentator().instrument(app).expose(app)

# RAG 엔진 초기화 (서버 시작 시 한 번만 로드)
rag_engine = RAGEngine()

# --- Request/Response 모델 정의 (Pydantic) ---
class QueryRequest(BaseModel):
    query: str

class SourceMetadata(BaseModel):
    title: str
    url: str
    date: str

class QueryResponse(BaseModel):
    answer: str
    sources: list[SourceMetadata]

# --- Endpoints ---
@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.post("/chat", response_model=QueryResponse)
def chat_endpoint(request: QueryRequest):
    """
    사용자의 질문을 받아 RAG 기반으로 답변하고, 참고한 논문 출처를 반환합니다.
    """
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
        
    try:
        answer, context_docs = rag_engine.get_answer(request.query)
        
        # 출처 정보 정리
        sources = [
            SourceMetadata(
                title=doc['metadata']['title'],
                url=doc['metadata']['url'],
                date=doc['metadata']['date']
            ) for doc in context_docs
        ]
        
        return QueryResponse(answer=answer, sources=sources)
    
    except Exception as e:
        # 실제 운영에선 여기서 에러 로그를 남겨야 함 (Sentry 등)
        print(f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    # 로컬 개발용 실행 커맨드
    uvicorn.run(app, host="0.0.0.0", port=8000)