# Daily ArXiv Insights Ops

> Personal research copilot for daily paper digests and grounded Q&A

ArXiv 최신 AI 논문을 수집하고, 초록을 구조화된 연구 메모로 바꾼 뒤, 다이제스트와 메모 기반 질의응답으로 재사용하는 개인 연구용 프로젝트입니다. 기본 방향은 `minimal self-hosting`, `structured research memory`, `digest-first UX` 입니다.

이 프로젝트는 다음 제품 방향을 참고해 정렬했습니다.
- [Khoj](https://github.com/khoj-ai/khoj): second-brain 검색과 개인 지식 축적
- [OpenPaper](https://github.com/khoj-ai/openpaper): paper-library 중심 UX
- [autoresearch](https://github.com/karpathy/autoresearch): 명시적인 research program 운용

## Core Features
- `Daily digest`: 최신 논문을 개인 연구 적합도 기준으로 정렬
- `Research memory`: 논문을 문제, 방법, 발견, 한계, 다음 읽을 거리로 구조화
- `Grounded Q&A`: 저장된 연구 메모를 우선 사용하는 질의응답

## Active API
- `POST /research/refresh`
- `GET /digest/latest`
- `POST /search`
- `POST /chat`

## Quick Start
빠른 실행은 [QUICKSTART.md](/home/wsm/workspace/daily-arxiv-insights-ops/QUICKSTART.md)를 보면 됩니다.

## Documentation
- [docs/01-product.md](/home/wsm/workspace/daily-arxiv-insights-ops/docs/01-product.md)
- [docs/02-architecture.md](/home/wsm/workspace/daily-arxiv-insights-ops/docs/02-architecture.md)
- [docs/03-backend.md](/home/wsm/workspace/daily-arxiv-insights-ops/docs/03-backend.md)
- [docs/04-operations.md](/home/wsm/workspace/daily-arxiv-insights-ops/docs/04-operations.md)
- [docs/05-secret-remediation.md](/home/wsm/workspace/daily-arxiv-insights-ops/docs/05-secret-remediation.md)
- [INFRASTRUCTURE.md](/home/wsm/workspace/daily-arxiv-insights-ops/INFRASTRUCTURE.md)

## Current Default Stack
- FastAPI
- ChromaDB
- file-based research memory
- Next.js frontend
- OpenAI optional for higher-quality note enrichment and answers

Airflow, Prometheus, Grafana, LangSmith는 저장소에 남아 있지만 현재 기본 실행 경로의 필수 요소는 아닙니다.
