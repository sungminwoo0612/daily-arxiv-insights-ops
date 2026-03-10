# Architecture

## Active Architecture
```text
ArXiv API
  -> collector
  -> structured note builder
  -> research memory store
  -> vector store
  -> digest generator
  -> FastAPI endpoints
  -> Next.js digest-first UI
```

## Core Modules
- `collector.py`: ArXiv 수집
- `research_service.py`: refresh, digest, Q&A orchestration
- `research_memory.py`: notes/digests/profile 저장
- `vector_store.py`: note-backed retrieval
- `api.py`: active product API

## Data Objects
- `ArxivPaper`
- `PaperNote`
- `DigestEntry`
- `DailyDigest`
- `ResearchProfile`

## Retrieval Policy
- local research memory 우선
- note text와 metadata를 함께 검색
- low confidence일 때만 optional web fallback 사용

## Legacy Components
다음 구성은 저장소에 있지만 현재 기본 경로는 아님:
- Airflow DAGs
- Grafana
- Prometheus
- LangGraph hybrid path
