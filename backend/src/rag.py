import os
import time
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from src.vector_store import VectorDB
from dotenv import load_dotenv
from prometheus_client import Histogram, Counter, Gauge

load_dotenv()

# Prometheus 메트릭 정의
rag_retrieval_duration = Histogram(
    'rag_retrieval_seconds', 
    'Vector search latency',
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0]  # 검색은 1초 이내 목표
)

rag_llm_duration = Histogram(
    'rag_llm_call_seconds', 
    'LLM API call latency',
    buckets=[1.0, 3.0, 5.0, 10.0, 20.0]  # OpenAI 응답 3-5초 목표
)

rag_total_duration = Histogram(
    'rag_total_seconds',
    'End-to-end RAG latency',
    buckets=[2.0, 5.0, 10.0, 15.0, 30.0]
)

rag_context_docs = Gauge(
    'rag_retrieved_docs_count',
    'Number of documents retrieved'
)

rag_context_relevance = Histogram(
    'rag_context_avg_score',
    'Average relevance score of retrieved docs',
    buckets=[0.3, 0.5, 0.7, 0.8, 0.9]
)

rag_errors = Counter(
    'rag_errors_total',
    'Total RAG errors',
    ['stage']  # stage: retrieval, llm, prompt
)

class RAGEngine:
    def __init__(self):
        self.vector_db = VectorDB()
        self.llm = ChatOpenAI(
            model="gpt-4o-mini", 
            temperature=0.1, # 약간의 유연성 / 0.0 for factual QA
            timeout=20,
            max_retries=2    
        )

    def get_answer(self, query: str):
        start_time = time.time()

        try:
            # 1. [Retrieve] - 메트릭 측정
            retrieval_start = time.time()
            related_papers = self.vector_db.search(query, n_results=3)
            rag_retrieval_duration.observe(time.time() - retrieval_start)
    
            # 검색 품질 메트릭
            rag_context_docs.set(len(related_papers))
            if related_papers:
                avg_score = sum(p['score'] for p in related_papers) / len(related_papers)
                rag_context_relevance.observe(avg_score)

            # 검색 실패 처리
            if not related_papers:
                rag_errors.labels(stage='retrieval').inc()
                return "관련된 논문을 찾을 수 없습니다.", []
            
            context_text = "\n\n".join([
                f"[논문 제목: {p['metadata']['title']}]\n{p['content']}" 
                for p in related_papers
            ])

            # 2. [Prompt]
            prompt = ChatPromptTemplate.from_template("""
당신은 AI/ML 논문 전문가입니다. 아래 최신 논문 내용을 바탕으로 질문에 답변하세요.

# 검색된 논문
{context}

# 규칙
1. 논문 내용에 근거하여 답변하되, 정확히 인용할 것
2. 불확실한 내용은 "논문에 명시되지 않음"으로 표기
3. 여러 논문의 내용을 종합하여 답변

# 질문
{question}
            """)

            # 3. [Generate] - 메트릭 측정
            chain = prompt | self.llm

            llm_start = time.time()
            response = chain.invoke({"context": context_text, "question": query})
            rag_llm_duration.observe(time.time() - llm_start)

            # E2E 메트릭
            rag_total_duration.observe(time.time() - start_time)
            
            return response.content, related_papers

        except Exception as e:
            rag_errors.labels(stage='llm').inc()
            print(f"RAG Error: {str(e)}")
            raise