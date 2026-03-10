# Quick Start

## 1. Prerequisites
```bash
python --version
node --version
```

## 2. Environment
```bash
cp env.example .env
```

선택:
- `OPENAI_API_KEY`를 설정하면 답변 품질과 note enrichment 품질이 좋아집니다.
- 설정하지 않아도 heuristic note generation과 digest 저장은 동작합니다.

## 3. Run
백엔드:
```bash
cd backend
python -m uvicorn src.api:app --reload --host 0.0.0.0 --port 8000
```

프론트엔드:
```bash
cd frontend
npm install
npm run dev
```

## 4. First Refresh
```bash
curl -X POST http://localhost:8000/research/refresh
curl http://localhost:8000/digest/latest
```

브라우저:
- API docs: `http://localhost:8000/docs`
- Frontend: `http://localhost:3000`

## 5. Recommended Defaults
```bash
ARXIV_QUERY=cat:cs.AI AND ("RAG" OR "Agents")
RESEARCH_FOCUS_AREAS=retrieval augmented generation,agentic workflows,ai research automation
RERANKER_STRATEGY=none
ENABLE_RERANKER=false
ENABLE_WEB_FALLBACK=false
USE_LLM_NOTE_ENRICHMENT=false
```

## 6. Optional Legacy Stack
Airflow, Prometheus, Grafana 기반 실행은 아직 저장소에 남아 있습니다.
- 운영 문서: [INFRASTRUCTURE.md](/home/wsm/workspace/daily-arxiv-insights-ops/INFRASTRUCTURE.md)
- Airflow 참고: [AIRFLOW_3X_QUICKSTART.md](/home/wsm/workspace/daily-arxiv-insights-ops/AIRFLOW_3X_QUICKSTART.md)
