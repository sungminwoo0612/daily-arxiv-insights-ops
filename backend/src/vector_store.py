import chromadb
from chromadb.utils import embedding_functions
from typing import List
from src.schemas import ArxivPaper

class VectorDB:
    def __init__(self, db_path: str = "data/vectordb", collection_name: str = "arxiv_papers"):
        # PersistentClient를 사용하여 디스크에 데이터 저장 (서버 재시작해도 유지됨)
        self.client = chromadb.PersistentClient(path=db_path)
        
        # 임베딩 함수 설정 (기본값: all-MiniLM-L6-v2)
        # 실제 프로덕션에선 OpenAI나 Upstage 등의 고성능 모델 사용 권장
        self.embedding_func = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
        
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            embedding_function=self.embedding_func
        )

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


    def search(self, query: str, n_results: int = 3):
            """
            사용자 질문(query)과 가장 유사한 논문을 검색합니다.
            """
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results
            )
            
            # ChromaDB 결과 파싱 (사용하기 편한 리스트 형태로 변환)
            parsed_results = []
            # results['documents']는 [[doc1, doc2, ...]] 형태임 (중첩 리스트)
            if results['documents']:
                for i in range(len(results['documents'][0])):
                    doc_text = results['documents'][0][i]
                    metadata = results['metadatas'][0][i]
                    distance = results['distances'][0][i]  # 거리 (유사도 역순)
                    
                    parsed_results.append({
                        "content": doc_text,
                        "metadata": metadata,
                        "score": distance
                    })
                    
            return parsed_results