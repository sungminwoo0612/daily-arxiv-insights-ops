# Secret Remediation Checklist

GitHub secret scanning alert를 받았을 때 바로 따라갈 수 있는 체크리스트다.  
현재 저장소에서는 Google API Key 유출 사례에 맞춰 작성했다.

## Immediate Actions
1. 노출된 secret이 실제로 활성 상태인지 확인한다.
2. 활성 상태라면 먼저 `rotate` 가능한지 확인한다.
3. 더 이상 필요 없거나 공개 저장소에 노출된 경우 즉시 `revoke` 한다.
4. 애플리케이션과 노트북, `.env`, 배포 환경에서 새 키로 교체한다.

## Repo Actions
1. 하드코딩된 secret을 코드와 노트북에서 제거한다.
2. 환경변수 참조 방식으로 바꾼다.
3. `.gitignore`에 민감 파일이 빠져 있지 않은지 확인한다.
4. 예제 파일에는 실제 값 대신 placeholder만 남긴다.
5. `rg`로 동일 secret 문자열이 작업 트리에 남아 있지 않은지 확인한다.

예시:
```bash
rg -n "AIzaSy[A-Za-z0-9_-]{20,}|sk-[A-Za-z0-9_-]+|lsv2_pt_" .
```

## Git History Check
1. secret이 현재 파일뿐 아니라 과거 커밋에도 남아 있는지 확인한다.
2. 이미 revoke한 경우:
   - 우선순위는 alert closure
   - history rewrite는 정책 또는 추가 위험이 있을 때만 진행한다.
3. history rewrite가 필요하면 팀 합의 후 `git filter-repo` 또는 BFG로 진행한다.

예시:
```bash
git grep -n "<leaked-secret>" $(git rev-list --all)
```

## Provider-Side Actions
Google API Key 기준:
1. Google Cloud Console에서 해당 key를 찾는다.
2. 사용 중이면 새 key 발급 후 교체한다.
3. 기존 key를 revoke 또는 delete 한다.
4. API usage, quota, audit log를 확인한다.
5. 허용된 referrer/IP 제한이 적절했는지 검토한다.

## GitHub Alert Closure
1. GitHub secret scanning alert 페이지로 이동한다.
2. remediation steps가 완료됐는지 확인한다.
3. 상태를 `revoked`로 close 한다.
4. 내부 메모에 다음 정보를 남긴다.
   - 어떤 secret이 유출됐는지
   - 어디서 노출됐는지
   - 언제 revoke/rotate 했는지
   - 추가 피해 확인 결과

## Recommended Follow-ups
1. `gitleaks` 또는 유사 도구를 pre-commit / CI에 추가한다.
2. notebook, `.env`, credentials 파일 정책을 문서화한다.
3. API key는 최소 권한과 referrer/IP 제한을 기본값으로 둔다.
4. 공개 저장소에서 쓰는 예제는 항상 placeholder만 사용한다.

## This Incident
- Secret type: Google API Key
- Detected by GitHub: 2026-01-08 alert
- Exposed path: `notebooks/00_etl_pipeline.ipynb`
- Historical commit: `6752d3b`
- Current local mitigation: hardcoded key removed, `GEMINI_API_KEY` env lookup로 변경
