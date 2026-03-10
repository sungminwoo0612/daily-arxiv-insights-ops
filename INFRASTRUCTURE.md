# Infrastructure Guide

## Default Runtime
현재 기본 런타임은 개인 연구용 경량 구성을 기준으로 합니다.

구성:
- FastAPI backend
- ChromaDB vector store
- file-based research memory under `data/research`
- Next.js frontend
- OpenAI optional

흐름:
1. ArXiv 수집
2. 구조화된 note 생성
3. note + metadata를 vector store와 research memory에 저장
4. digest 생성
5. local-first Q&A 제공

## Why This Is Default
- 개인 연구에는 항상 켜져 있는 오케스트레이션이 필수가 아님
- self-hosting 부담을 줄이는 것이 현재 목표
- 운영용 observability보다 research throughput이 우선

## Optional Legacy Stack
저장소에는 다음 인프라도 남아 있습니다.
- Airflow
- Prometheus
- Grafana
- LangSmith integration

이 스택은 다음 상황에서만 권장합니다.
- 주기 실행을 UI와 함께 관리해야 할 때
- 메트릭 대시보드가 실제로 필요한 때
- 개인 프로젝트를 넘어 장기 운영/협업 환경으로 확장할 때

## Ports
기본:
- `8000`: FastAPI
- `3000`: Next.js

레거시 선택 구성:
- `8080`: Airflow
- `9090`: Prometheus
- `13000`: Grafana

## Storage Layout
- `backend/data/raw`: fetched raw paper batches
- `backend/data/vectordb`: Chroma persistence
- `backend/data/research` or `data/research`: notes, digests, profile

## Deployment Recommendation
개인 사용 기준 권장 순서:
1. 로컬 실행
2. 단일 VM 또는 개인 서버에 backend/frontend만 배포
3. 필요해질 때만 scheduler 또는 observability 추가
