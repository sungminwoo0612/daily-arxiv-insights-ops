# Airflow 3.x Migration Notes

이 문서는 현재 기본 런타임이 아닌 Airflow 경로를 유지보수할 때만 참고합니다.

## Current Product Reality
- 기본 실행 경로는 Airflow 없이 동작합니다.
- Airflow는 optional orchestration layer 입니다.
- 개인 연구용 기본 UX는 digest-first 입니다.

## Keep If Needed
- scheduled collection
- UI-based DAG monitoring
- task retry orchestration

## Migrate Only If
- backend refresh job를 DAG로 다시 승격할 필요가 있을 때
- 운영 파이프라인 신뢰성이 로컬 실행보다 중요해질 때

## Recommended Boundary
Airflow가 담당해야 할 일:
- `research/refresh`와 동일한 수집 배치 호출
- 실행 스케줄링과 실패 재시도

Airflow가 담당하지 않아야 할 일:
- 제품의 주 질의응답 로직
- frontend UX
- 연구 메모 데이터 모델 정의
