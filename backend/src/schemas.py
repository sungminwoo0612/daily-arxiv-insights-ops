from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class ArxivPaper(BaseModel):
    """
    논문 메타데이터를 저장하기 위한 Pydantic 모델
    """
    paper_id: str = Field(..., description="ArXiv ID (e.g. 2310.xxxx)")
    title: str = Field(..., description="논문 제목")
    authors: List[str] = Field(..., description="저자 목록")
    summary: str = Field(..., description="논문 초록 (Abstract)")
    published_date: datetime = Field(..., description="출판 날짜")
    categories: List[str] = Field(..., description="ArXiv 카테고리 (e.g. cs.AI, cs.LG)")
    pdf_url: str = Field(..., description="PDF 다운로드 링크")

    # 데이터 수집 시점 추적 (Data Lineage)
    collected_at: datetime = Field(default_factory=datetime.now, description="수집된 시간")

    class Config:
        json_schema_extra = {
            "example": {
                "paper_id": "2310.00001",
                "title": "LLM for MLOps",
                "authors": ["Sungmin Woo", "AI Researcher"],
                "summary": "This paper discusses...",
                "published_date": "2023-10-01T12:00:00",
                "categories": ["cs.LG", "cs.AI"],
                "pdf_url": "http://arxiv.org/pdf/..."
            }
        }