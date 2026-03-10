# Airflow 3.x Quickstart

이 문서는 현재 기본 경로가 아니라 `optional legacy stack` 참고용입니다.

현재 기본 경로:
- FastAPI
- ChromaDB
- research memory files
- Next.js

Airflow를 다시 활성화해야 하는 경우에만 이 문서를 사용하세요.

## When To Use
- 정해진 시각에 수집을 강제해야 할 때
- DAG UI와 실행 이력이 필요할 때
- 개인 도구를 팀 운영 파이프라인으로 확장할 때

## Minimal Steps
```bash
make init
make up
make logs-airflow
```

## Notes
- Airflow 관련 파일은 현재 기본 제품 방향과 분리되어 있습니다.
- 최신 제품 기능은 `research_service`와 digest-first API에 맞춰 구현되어 있습니다.
