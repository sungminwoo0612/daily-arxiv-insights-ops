import chromadb
from chromadb.utils import embedding_functions
from typing import List, Optional
from src.schemas import ArxivPaper
from src.reranker import BaseReranker, RerankerFactory
from src.config import settings

class VectorDB:
    def __init__(
        self, 
        db_path: str = "data/vectordb", 
        collection_name: str = "arxiv_papers",
        enable_reranker: bool = True
    ):
        # Config에서 기본값 가져오기
        db_path = db_path or settings.VECTOR_DB_PATH
        collection_name = collection_name or settings.VECTOR_DB_COLLECTION_NAME

        # ChromaDB 초기화
        # 1. PersistentClient를 사용하여 디스크에 데이터 저장 (서버 재시작해도 유지됨)
        self.client = chromadb.PersistentClient(path=db_path)
        
        # 2. Embedding 설정 (기본값: all-MiniLM-L6-v2)
        # 실제 프로덕션에선 OpenAI나 Upstage 등의 고성능 모델 사용 권장
        self.embedding_func = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=settings.EMBEDDING_MODEL_NAME
        )
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            embedding_function=self.embedding_func
        )

        # 3. Reranker 초기화
        self.reranker: Optional[BaseReranker] = None
        if enable_reranker and settings.RERANKER_STRATEGY.lower() != "none":
            try:
                self.reranker = RerankerFactory.create_from_config(settings)
                print(f"✅ Reranker enabled: {settings.RERANKER_STRATEGY}")
            except Exception as e:
                print(f"⚠️ Reranker initialization failed: {e}")
                print("   Falling back to vector search only")

    def upsert_papers(self, papers: List[ArxivPaper]):
        """
        논문 요약(Summary)을 임베딩하여 저장합니다.
        이미 있는 paper_id라면 업데이트합니다 (Upsert).
        """
        if not papers:
            return

        ids = [p.paper_id for p in papers]
        documents = [p.summary for p in papers] # 벡터화할 텍스트
        
        # 메타데이터에는 검색 결과에 보여줄 제목, 링크 등을 넣습니다.
        metadatas = [
            {
                "title": p.title,
                "date": p.published_date.isoformat(),
                "url": p.pdf_url,
                "authors": ", ".join(p.authors[:3]) # 저자 3명까지만
            } 
            for p in papers
        ]

        # 데이터 삽입
        self.collection.upsert(
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )
        
        print(f"🧩 [Vector DB] Upserted {len(papers)} papers into collection '{self.collection.name}'")


    def search(self, query: str, n_results: int = 3, use_reranker: bool = True):
            """
            사용자 질문(query)과 가장 유사한 논문을 검색합니다.
            
            검색 전략:
            1. Vector search로 과잉 검색 (reranker 있으면 n_results * 3)
            2. Reranker로 정밀 필터링 → n_results
            """
            # Initial retrieval
            fetch_count = n_results * 3 if (use_reranker and self.reranker) else n_results

            results = self.collection.query(
                query_texts=[query],
                n_results=min(fetch_count, 100)  # ChromaDB 최대 제한
            )

            # ChromaDB 결과 파싱 (사용하기 편한 리스트 형태로 변환)
            initial_docs = self._parse_chromadb_results(results)

            if not initial_docs:
                return []
            
            # Reranking
            if use_reranker and self.reranker:
                reranked = self.reranker.rerank(query, initial_docs, top_k=n_results)
                return [
                    {
                        "content": r.content,
                        "metadata": r.metadata,
                        "score": r.score
                    }
                    for r in reranked
                ]
            
            # Reranker 없으면 상위 n_results만 반환
            return initial_docs[:n_results]
    
    def _parse_chromadb_results(self, results):
        """ChromaDB 결과 → Dict 변환"""
        parsed = []
        if results['documents'] and results['documents'][0]:
            for i in range(len(results['documents'][0])):
                # ChromaDB L2 distance → similarity (0~1)
                distance = results['distances'][0][i]
                similarity = 1 / (1 + distance)
                
                parsed.append({
                    "content": results['documents'][0][i],
                    "metadata": results['metadatas'][0][i],
                    "score": similarity
                })
        return parsed