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


class ResearchProfile(BaseModel):
    """개인 연구 방향과 우선순위를 정의하는 프로필"""

    focus_areas: List[str] = Field(default_factory=list, description="핵심 관심 주제")
    exclude_topics: List[str] = Field(default_factory=list, description="우선순위에서 제외할 주제")
    preferred_queries: List[str] = Field(default_factory=list, description="수집에 사용할 검색 쿼리")
    research_program: str = Field(default="", description="연구 목적과 판단 기준을 적은 텍스트")


class PaperNote(BaseModel):
    """논문을 개인 연구 메모 형태로 구조화한 노트"""

    paper_id: str
    title: str
    source_url: str
    published_date: datetime
    authors: List[str] = Field(default_factory=list)
    summary: str
    problem: str
    method: str
    key_findings: List[str] = Field(default_factory=list)
    limitations: List[str] = Field(default_factory=list)
    why_it_matters: str
    relation_to_interests: str
    read_next: str
    topics: List[str] = Field(default_factory=list)
    relevance_score: float = 0.0
    my_notes: str = ""
    generated_at: datetime = Field(default_factory=datetime.now)

    def to_retrieval_text(self) -> str:
        return "\n".join(
            [
                f"Title: {self.title}",
                f"Problem: {self.problem}",
                f"Method: {self.method}",
                f"Key Findings: {'; '.join(self.key_findings)}",
                f"Limitations: {'; '.join(self.limitations)}",
                f"Why It Matters: {self.why_it_matters}",
                f"Relation To Interests: {self.relation_to_interests}",
                f"Read Next: {self.read_next}",
                f"Topics: {', '.join(self.topics)}",
                f"Summary: {self.summary}",
                f"My Notes: {self.my_notes}",
            ]
        )


class DigestEntry(BaseModel):
    """일일 리서치 다이제스트 항목"""

    paper_id: str
    title: str
    source_url: str
    published_date: datetime
    score: float
    why_it_matters: str
    relation_to_interests: str
    read_next: str
    topics: List[str] = Field(default_factory=list)


class DailyDigest(BaseModel):
    """개인 연구용 일일 다이제스트"""

    date: str
    generated_at: datetime = Field(default_factory=datetime.now)
    summary: str
    entries: List[DigestEntry] = Field(default_factory=list)
    profile_focus: List[str] = Field(default_factory=list)
