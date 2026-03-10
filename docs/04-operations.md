# Operations

## Default Workflow
1. `.env` 준비
2. backend 실행
3. frontend 실행
4. `POST /research/refresh` 호출
5. frontend 또는 `/digest/latest`로 결과 확인

## Verification
현재 저장소에서 확인한 기본 검증:
- backend Python modules syntax compile
- frontend eslint

## Recommended Next Ops Improvements
- `pytest`를 개발 환경에 추가
- refresh job용 cron 또는 GitHub Actions 추가
- API 키 없는 상태에서도 동작하는 smoke test 추가

## Commit Strategy
권장 커밋 단위:
- product/backend refactor
- frontend digest UX
- docs and quickstart

## Push Requirements
- GitHub 인증 필요
- 네트워크 허용 필요
