"""
설정 관리 모듈
환경 변수와 애플리케이션 설정을 중앙에서 관리합니다.
"""
import os
from pathlib import Path
from typing import List

from dotenv import load_dotenv

is_docker = os.getenv("VECTOR_DB_PATH", "").startswith("/app/")

if not is_docker:
    # 로컬 개발 환경: .env 파일 로드
    backend_dir = Path(__file__).parent.parent
    env_file = backend_dir / ".env"

    if env_file.exists():
        load_dotenv(dotenv_path=env_file)
    else:
        root_env = Path(__file__).parent.parent.parent / ".env"
        if root_env.exists():
            load_dotenv(dotenv_path=root_env)


class Settings:
    """애플리케이션 설정 클래스"""

    # --- 환경 변수 설정 ---
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

    # LangChain 설정
    LANGCHAIN_TRACING_V2: bool = os.getenv("LANGCHAIN_TRACING_V2", "false").lower() == "true"
    LANGCHAIN_ENDPOINT: str = os.getenv("LANGCHAIN_ENDPOINT", "https://api.smith.langchain.com")
    LANGCHAIN_API_KEY: str = os.getenv("LANGCHAIN_API_KEY", "")
    LANGCHAIN_PROJECT: str = os.getenv("LANGCHAIN_PROJECT", "")

    # --- ArXiv 설정 ---
    ARXIV_QUERY: str = os.getenv(
        "ARXIV_QUERY",
        'cat:cs.AI AND ("Large Language Models" OR "RAG")',
    )
    ARXIV_MAX_RESULTS: int = int(os.getenv("ARXIV_MAX_RESULTS", "3"))

    # --- 데이터 저장 경로 ---
    DATA_LAKE_BASE_PATH: str = os.getenv("DATA_LAKE_BASE_PATH", "data/raw")
    VECTOR_DB_PATH: str = os.getenv("VECTOR_DB_PATH", "data/vectordb")
    VECTOR_DB_COLLECTION_NAME: str = os.getenv("VECTOR_DB_COLLECTION_NAME", "arxiv_papers")

    # --- API 설정 ---
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))
    CORS_ORIGINS: List[str] = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000",
    ).split(",")

    # --- RAG 설정 ---
    LLM_MODEL: str = os.getenv("LLM_MODEL", "gpt-4o-mini")
    LLM_TEMPERATURE: float = float(os.getenv("LLM_TEMPERATURE", "0.1"))
    LLM_TIMEOUT: int = int(os.getenv("LLM_TIMEOUT", "20"))
    LLM_MAX_RETRIES: int = int(os.getenv("LLM_MAX_RETRIES", "2"))
    RAG_N_RESULTS: int = int(os.getenv("RAG_N_RESULTS", "3"))
    LOCAL_CONFIDENCE_THRESHOLD: float = float(os.getenv("LOCAL_CONFIDENCE_THRESHOLD", "0.55"))

    # --- 임베딩 모델 설정 ---
    EMBEDDING_MODEL_NAME: str = os.getenv("EMBEDDING_MODEL_NAME", "all-MiniLM-L6-v2")

    # --- Reranker 설정 ---
    COHERE_API_KEY: str = os.getenv("COHERE_API_KEY", "")
    RERANKER_STRATEGY: str = os.getenv("RERANKER_STRATEGY", "none")
    BGE_DEVICE: str = os.getenv("BGE_DEVICE", "cpu")
    ENABLE_RERANKER: bool = os.getenv("ENABLE_RERANKER", "false").lower() == "true"

    # --- 연구 코파일럿 설정 ---
    RESEARCH_MEMORY_PATH: str = os.getenv("RESEARCH_MEMORY_PATH", "data/research")
    DIGEST_MAX_ITEMS: int = int(os.getenv("DIGEST_MAX_ITEMS", "5"))
    RESEARCH_FOCUS_AREAS: List[str] = os.getenv(
        "RESEARCH_FOCUS_AREAS",
        "retrieval augmented generation,agentic workflows,ai research automation",
    ).split(",")
    RESEARCH_EXCLUDE_TOPICS: List[str] = os.getenv("RESEARCH_EXCLUDE_TOPICS", "").split(",")
    RESEARCH_PROGRAM_PATH: str = os.getenv("RESEARCH_PROGRAM_PATH", "research_program.md")
    USE_LLM_NOTE_ENRICHMENT: bool = os.getenv("USE_LLM_NOTE_ENRICHMENT", "false").lower() == "true"
    ENABLE_WEB_FALLBACK: bool = os.getenv("ENABLE_WEB_FALLBACK", "false").lower() == "true"

    @classmethod
    def validate(cls) -> None:
        """필수 설정값 검증"""
        if not cls.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY 환경 변수가 설정되지 않았습니다.")

        valid_strategies = ["cohere", "bge", "hybrid", "cascade", "none"]
        if cls.RERANKER_STRATEGY.lower() not in valid_strategies:
            raise ValueError(
                f"RERANKER_STRATEGY는 다음 중 하나여야 합니다: {valid_strategies}. "
                f"현재 값: {cls.RERANKER_STRATEGY}"
            )

        if cls.ENABLE_RERANKER and cls.RERANKER_STRATEGY.lower() in ["cohere", "hybrid", "cascade"]:
            if not cls.COHERE_API_KEY:
                raise ValueError(
                    f"RERANKER_STRATEGY가 '{cls.RERANKER_STRATEGY}'인 경우 "
                    "COHERE_API_KEY 환경 변수가 필요합니다."
                )

    @classmethod
    def get_cors_origins(cls) -> List[str]:
        return [origin.strip() for origin in cls.CORS_ORIGINS if origin.strip()]

    @classmethod
    def get_focus_areas(cls) -> List[str]:
        return [area.strip() for area in cls.RESEARCH_FOCUS_AREAS if area.strip()]

    @classmethod
    def get_exclude_topics(cls) -> List[str]:
        return [topic.strip() for topic in cls.RESEARCH_EXCLUDE_TOPICS if topic.strip()]


settings = Settings()
settings.RESEARCH_FOCUS_AREAS = settings.get_focus_areas()
settings.RESEARCH_EXCLUDE_TOPICS = settings.get_exclude_topics()
