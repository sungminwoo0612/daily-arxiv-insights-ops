# Backend Reference

## Main Endpoints
- `GET /health`
- `GET /digest/latest`
- `POST /research/refresh`
- `POST /search`
- `POST /chat`

## Refresh Flow
1. ArXiv에서 최신 논문 수집
2. 기존 note 기준 dedupe
3. structured note 생성
4. raw batch 저장
5. vector DB upsert
6. daily digest 생성

## Q&A Flow
1. vector search over stored notes
2. confidence 계산
3. local answer 생성
4. optional web fallback 보강

## Configuration
핵심 설정:
- `ARXIV_QUERY`
- `RESEARCH_FOCUS_AREAS`
- `RESEARCH_PROGRAM_PATH`
- `ENABLE_RERANKER`
- `ENABLE_WEB_FALLBACK`
- `USE_LLM_NOTE_ENRICHMENT`

## Storage
- raw batches: `backend/data/raw`
- vector data: `backend/data/vectordb`
- research memory: `data/research` 또는 설정 경로
