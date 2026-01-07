"""
LangChain 기반 Reranker 구현
- Cohere Rerank API
- BGE Cross-Encoder (HuggingFace)
- Hybrid Search (BM25 + Vector)
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Literal
import time
from dataclasses import dataclass
from prometheus_client import Histogram, Counter
import os

from langchain_core.documents import Document

# CohereRerank는 langchain_cohere 패키지에서 직접 import
try:
    from langchain_cohere import CohereRerank
except ImportError:
    try:
        from langchain_community.document_compressors import CohereRerank
    except ImportError:
        CohereRerank = None

# HuggingFaceCrossEncoder는 langchain_community에서 import
try:
    from langchain_community.cross_encoders import HuggingFaceCrossEncoder
except ImportError:
    HuggingFaceCrossEncoder = None


# ========================================
# Prometheus 메트릭
# ========================================
reranker_duration = Histogram(
    'reranker_duration_seconds',
    'Reranker execution time',
    ['reranker_type'],
    buckets=[0.05, 0.1, 0.2, 0.5, 1.0, 2.0, 5.0]
)

reranker_score_delta = Histogram(
    'reranker_score_improvement',
    'Score improvement after reranking',
    ['reranker_type'],
    buckets=[-0.2, 0, 0.05, 0.1, 0.2, 0.3, 0.5]
)

reranker_errors = Counter(
    'reranker_errors_total',
    'Reranker failures',
    ['reranker_type', 'error_type']
)

# ========================================
# 데이터 모델
# ========================================
@dataclass
class RerankResult:
    """Reranking 결과 표준 포맷"""
    content: str
    metadata: Dict
    score: float  # 0~1 정규화
    original_rank: int

# ========================================
# Abstract Base Class
# ========================================
class BaseReranker(ABC):
    """Reranker 추상 클래스"""

    @abstractmethod
    def rerank(
        self,
        query: str,
        documents: List[Dict],
        top_k: int = 3
    ) -> List[RerankResult]:
        f"""
        Args:
            query: 사용자 질문
            documents: [{"content": str, "metadata": dict, "score": float}, ...]
            top_k: 반환할 상위 K개
        
        Returns:
            RerankResult 리스트 (score 내림차순)
        """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """메트릭용 reranker 이름"""
        pass

    def _to_langchain_docs(self, documents: List[Dict]) -> List[Document]:
        """Dict → LangChain Document 변환"""
        return [
            Document(
                page_content=doc["content"],
                metadata=doc.get("metadata", {})
            )
            for doc in documents
        ]
    
    def _from_langchain_docs(
        self, 
        documents: List[Document], 
        original_docs: List[Dict]
    ) -> List[RerankResult]:
        """LangChain Document → RerankResult 변환"""
        results = []
        for rank, doc in enumerate(documents):
            # LangChain Document의 metadata에서 relevance_score 추출
            score = doc.metadata.get("relevance_score", 0.5)
            
            # original_rank 찾기 (metadata 비교)
            original_rank = 0
            for i, orig_doc in enumerate(original_docs):
                if orig_doc["content"] == doc.page_content:
                    original_rank = i
                    break
            
            results.append(RerankResult(
                content=doc.page_content,
                metadata=doc.metadata,
                score=float(score),
                original_rank=original_rank
            ))
        
        return results
    
    def _fallback_to_original(
        self, 
        documents: List[Dict], 
        top_k: int
    ) -> List[RerankResult]:
        """에러 시 원본 순서 유지"""
        return [
            RerankResult(
                content=doc["content"],
                metadata=doc.get("metadata", {}),
                score=doc.get("score", 0.5),
                original_rank=i
            )
            for i, doc in enumerate(documents[:top_k])
        ]


# ========================================
# 1. Cohere Rerank (LangChain)
# ========================================
class CohereReranker(BaseReranker):
    """
    LangChain CohereRerank 사용
    - 장점: 최고 정확도, 인프라 불필요
    - 단점: API 비용, 외부 의존성
    """
    
    def __init__(
        self, 
        api_key: str = None, 
        model: str = "rerank-english-v3.0",
        top_n: int = 3
    ):
        if CohereRerank is None:
            raise ImportError("Install: pip install langchain-cohere")
        
        self.compressor = CohereRerank(
            cohere_api_key=api_key or os.getenv("COHERE_API_KEY"),
            top_n=top_n,
            model=model  # rerank-multilingual-v3.0 for Korean
        )
        self.top_n = top_n
    
    @property
    def name(self) -> str:
        return "cohere"
    
    def rerank(
        self, 
        query: str, 
        documents: List[Dict], 
        top_k: int = 3
    ) -> List[RerankResult]:
        start_time = time.time()
        
        try:
            # Dict → LangChain Document
            lc_docs = self._to_langchain_docs(documents)
            
            # Reranking 수행
            compressed = self.compressor.compress_documents(
                documents=lc_docs,
                query=query
            )
            
            # 결과 변환
            results = self._from_langchain_docs(compressed[:top_k], documents)
            
            # 메트릭
            duration = time.time() - start_time
            reranker_duration.labels(reranker_type=self.name).observe(duration)
            
            if documents and results:
                original_top_score = documents[0].get("score", 0)
                delta = results[0].score - original_top_score
                reranker_score_delta.labels(reranker_type=self.name).observe(delta)
            
            return results
            
        except Exception as e:
            reranker_errors.labels(
                reranker_type=self.name, 
                error_type=type(e).__name__
            ).inc()
            print(f"[Cohere Rerank Error] {str(e)}")
            return self._fallback_to_original(documents, top_k)


# ========================================
# 2. BGE Reranker (LangChain)
# ========================================
class BGEReranker(BaseReranker):
    """
    HuggingFace Cross-Encoder 직접 사용
    - 장점: 무료, 높은 정확도
    - 단점: GPU 필요, 초기 로딩 시간
    """
    
    def __init__(
        self, 
        model_name: str = "BAAI/bge-reranker-v2-m3",
        top_n: int = 3
    ):
        if HuggingFaceCrossEncoder is None:
            raise ImportError(
                "Install: pip install langchain-community sentence-transformers"
            )
        
        print(f"[BGE Reranker] Loading model: {model_name}")
        
        # HuggingFace Cross-Encoder 초기화
        self.model = HuggingFaceCrossEncoder(model_name=model_name)
        self.top_n = top_n
    
    @property
    def name(self) -> str:
        return "bge_local"
    
    def rerank(
        self, 
        query: str, 
        documents: List[Dict], 
        top_k: int = 3
    ) -> List[RerankResult]:
        start_time = time.time()
        
        try:
            # 문서 텍스트 추출
            doc_texts = [doc["content"] for doc in documents]
            
            # Cross-encoder로 점수 계산 (한 번에 모든 쌍 처리)
            # score 메서드는 List[Tuple[str, str]]를 받아 List[float]를 반환
            text_pairs = [(query, doc_text) for doc_text in doc_texts]
            scores = self.model.score(text_pairs)
            
            # 점수 기준으로 정렬 (내림차순)
            scored_docs = list(zip(documents, scores, range(len(documents))))
            scored_docs.sort(key=lambda x: x[1], reverse=True)
            
            # 상위 top_k개 선택 및 정규화
            max_score = max(scores) if scores else 1.0
            min_score = min(scores) if scores else 0.0
            score_range = max_score - min_score if max_score != min_score else 1.0
            
            results = []
            for rank, (doc, score, original_rank) in enumerate(scored_docs[:top_k]):
                # 점수를 0~1 범위로 정규화
                normalized_score = (score - min_score) / score_range if score_range > 0 else 0.5
                
                results.append(RerankResult(
                    content=doc["content"],
                    metadata=doc.get("metadata", {}),
                    score=float(normalized_score),
                    original_rank=original_rank
                ))
            
            # 메트릭
            duration = time.time() - start_time
            reranker_duration.labels(reranker_type=self.name).observe(duration)
            
            if documents and results:
                delta = results[0].score - documents[0].get("score", 0)
                reranker_score_delta.labels(reranker_type=self.name).observe(delta)
            
            return results
            
        except Exception as e:
            reranker_errors.labels(
                reranker_type=self.name, 
                error_type=type(e).__name__
            ).inc()
            print(f"[BGE Rerank Error] {str(e)}")
            return self._fallback_to_original(documents, top_k)


# ========================================
# 3. Hybrid Search (BM25 + Vector)
# ========================================
class HybridReranker(BaseReranker):
    """
    BM25 + Vector Similarity Hybrid
    - LangChain에 직접 지원 없음 → 직접 구현
    - 장점: 빠름, 무료, 키워드 매칭 강화
    """
    
    def __init__(
        self, 
        bm25_weight: float = 0.3, 
        vector_weight: float = 0.7
    ):
        try:
            from rank_bm25 import BM25Okapi
        except ImportError:
            raise ImportError("Install: pip install rank-bm25")
        
        self.BM25Okapi = BM25Okapi
        self.bm25_weight = bm25_weight
        self.vector_weight = vector_weight
    
    @property
    def name(self) -> str:
        return "hybrid_bm25"
    
    def rerank(
        self, 
        query: str, 
        documents: List[Dict], 
        top_k: int = 3
    ) -> List[RerankResult]:
        start_time = time.time()
        
        try:
            # 1. BM25 점수 계산
            corpus = [doc["content"] for doc in documents]
            tokenized_corpus = [text.lower().split() for text in corpus]
            bm25 = self.BM25Okapi(tokenized_corpus)
            
            tokenized_query = query.lower().split()
            bm25_scores = bm25.get_scores(tokenized_query)
            
            # BM25 정규화 (0~1)
            if bm25_scores.max() > 0:
                bm25_scores = bm25_scores / bm25_scores.max()
            
            # 2. Vector 점수 (ChromaDB distance → similarity 변환)
            vector_scores = []
            for doc in documents:
                distance = doc.get("score", 0.5)
                # ChromaDB L2 distance를 similarity로 변환
                similarity = 1 / (1 + distance)
                vector_scores.append(similarity)
            
            # 3. Hybrid 점수 계산
            hybrid_scores = [
                self.bm25_weight * bm25 + self.vector_weight * vec
                for bm25, vec in zip(bm25_scores, vector_scores)
            ]
            
            # 4. 정렬
            ranked_indices = sorted(
                range(len(hybrid_scores)), 
                key=lambda i: hybrid_scores[i], 
                reverse=True
            )[:top_k]
            
            results = [
                RerankResult(
                    content=documents[idx]["content"],
                    metadata=documents[idx].get("metadata", {}),
                    score=hybrid_scores[idx],
                    original_rank=idx
                )
                for idx in ranked_indices
            ]
            
            # 메트릭
            duration = time.time() - start_time
            reranker_duration.labels(reranker_type=self.name).observe(duration)
            
            if results and documents:
                delta = results[0].score - vector_scores[0]
                reranker_score_delta.labels(reranker_type=self.name).observe(delta)
            
            return results
            
        except Exception as e:
            reranker_errors.labels(
                reranker_type=self.name, 
                error_type=type(e).__name__
            ).inc()
            print(f"[Hybrid Rerank Error] {str(e)}")
            return self._fallback_to_original(documents, top_k)


# ========================================
# 4. No Reranker (Pass-through)
# ========================================
class NoReranker(BaseReranker):
    """Reranking 비활성화 (원본 순서 유지)"""
    
    @property
    def name(self) -> str:
        return "none"
    
    def rerank(
        self, 
        query: str, 
        documents: List[Dict], 
        top_k: int = 3
    ) -> List[RerankResult]:
        return [
            RerankResult(
                content=doc["content"],
                metadata=doc.get("metadata", {}),
                score=doc.get("score", 0.5),
                original_rank=i
            )
            for i, doc in enumerate(documents[:top_k])
        ]


# ========================================
# Factory Pattern
# ========================================
class RerankerFactory:
    """Reranker 생성 팩토리"""
    
    @staticmethod
    def create(
        reranker_type: Literal["cohere", "bge", "hybrid", "none"],
        **kwargs
    ) -> BaseReranker:
        """
        Args:
            reranker_type: "cohere", "bge", "hybrid", "none"
            **kwargs: reranker별 설정값
        
        Returns:
            BaseReranker 인스턴스
        """
        rerankers = {
            "cohere": CohereReranker,
            "bge": BGEReranker,
            "hybrid": HybridReranker,
            "none": NoReranker
        }
        
        if reranker_type not in rerankers:
            raise ValueError(
                f"Unknown reranker: {reranker_type}. "
                f"Options: {list(rerankers.keys())}"
            )
        
        return rerankers[reranker_type](**kwargs)
    
    @staticmethod
    def create_from_config(config) -> BaseReranker:
        """
        Config 객체에서 reranker 생성
        
        Args:
            config: Settings 인스턴스 (src.config.Settings)
        """
        strategy = config.RERANKER_STRATEGY.lower()
        
        if strategy == "cohere":
            return CohereReranker(
                api_key=config.COHERE_API_KEY,
                top_n=config.RAG_N_RESULTS
            )
        
        elif strategy == "bge":
            # BGE는 GPU 사용 권장
            return BGEReranker(top_n=config.RAG_N_RESULTS)
        
        elif strategy == "hybrid":
            return HybridReranker()
        
        elif strategy == "none":
            return NoReranker()
        
        else:
            raise ValueError(
                f"Invalid RERANKER_STRATEGY: {strategy}. "
                f"Valid options: cohere, bge, hybrid, none"
            )


# ========================================
# 사용 예시
# ========================================
if __name__ == "__main__":
    # 테스트용 더미 문서
    test_docs = [
        {
            "content": "Retrieval-Augmented Generation (RAG) is a technique...",
            "metadata": {"title": "RAG Paper", "url": "http://example.com/1"},
            "score": 0.85
        },
        {
            "content": "Large Language Models are transforming AI...",
            "metadata": {"title": "LLM Paper", "url": "http://example.com/2"},
            "score": 0.75
        },
        {
            "content": "Vector databases enable efficient similarity search...",
            "metadata": {"title": "VectorDB Paper", "url": "http://example.com/3"},
            "score": 0.65
        }
    ]
    
    query = "What is RAG?"
    
    # 1. Hybrid Reranker 테스트 (API 키 불필요)
    print("\n=== Testing Hybrid Reranker ===")
    hybrid = RerankerFactory.create("hybrid")
    results = hybrid.rerank(query, test_docs, top_k=2)
    
    for i, result in enumerate(results):
        print(f"\n[{i+1}] Score: {result.score:.3f} (Original Rank: {result.original_rank})")
        print(f"Title: {result.metadata['title']}")
        print(f"Content: {result.content[:50]}...")