from functools import lru_cache

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from prometheus_fastapi_instrumentator import Instrumentator

from src.config import settings
from src.research_service import ResearchService

app = FastAPI(
    title="Personal Research Copilot API",
    description="개인 연구용 다이제스트와 논문 기반 질의응답 API",
    version="3.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Instrumentator().instrument(app).expose(app)


@lru_cache(maxsize=1)
def get_research_service() -> ResearchService:
    return ResearchService()


class QueryRequest(BaseModel):
    query: str
    use_web_search: bool = False


class SourceMetadata(BaseModel):
    title: str
    url: str
    date: str


class DigestEntryResponse(BaseModel):
    paper_id: str
    title: str
    source_url: str
    published_date: str
    score: float
    why_it_matters: str
    relation_to_interests: str
    read_next: str
    topics: list[str]


class DigestResponse(BaseModel):
    date: str
    generated_at: str
    summary: str
    profile_focus: list[str]
    entries: list[DigestEntryResponse]


class QueryResponse(BaseModel):
    answer: str
    sources: list[SourceMetadata]
    metadata: dict


class RefreshResponse(BaseModel):
    fetched: int
    new_papers: int
    notes_created: int
    digest_entries: int
    digest_date: str


class SearchResponse(BaseModel):
    results: list[dict]


@app.get("/health")
def health_check():
    return {"status": "ok", "mode": "research_copilot"}


@app.get("/digest/latest", response_model=DigestResponse)
def latest_digest():
    digest = get_research_service().get_latest_digest()
    return DigestResponse(
        date=digest.date,
        generated_at=digest.generated_at.isoformat(),
        summary=digest.summary,
        profile_focus=digest.profile_focus,
        entries=[
            DigestEntryResponse(
                paper_id=entry.paper_id,
                title=entry.title,
                source_url=entry.source_url,
                published_date=entry.published_date.isoformat(),
                score=entry.score,
                why_it_matters=entry.why_it_matters,
                relation_to_interests=entry.relation_to_interests,
                read_next=entry.read_next,
                topics=entry.topics,
            )
            for entry in digest.entries
        ],
    )


@app.post("/research/refresh", response_model=RefreshResponse)
def refresh_research_library():
    result = get_research_service().refresh_library()
    return RefreshResponse(**result)


@app.post("/search", response_model=SearchResponse)
def search_endpoint(request: QueryRequest):
    return SearchResponse(results=get_research_service().search_library(request.query))


@app.post("/chat", response_model=QueryResponse)
def chat_endpoint(request: QueryRequest):
    try:
        answer, sources, metadata = get_research_service().answer_query(
            query=request.query,
            use_web_search=request.use_web_search,
        )

        return QueryResponse(
            answer=answer,
            sources=[
                {
                    "title": source["metadata"].get("title", "Untitled"),
                    "url": source["metadata"].get("url", ""),
                    "date": source["metadata"].get("date", ""),
                }
                for source in sources
            ],
            metadata=metadata,
        )
    except Exception as exc:
        print(f"Error: {str(exc)}")
        raise HTTPException(status_code=500, detail=str(exc))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
