import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
supabase = create_client(os.environ.get("SUPABASE_URL"), os.environ.get("SUPABASE_KEY"))

# 현재 생성된 모든 버킷 목록 출력
buckets = supabase.storage.list_buckets()
print("현재 버킷 목록:", [b.name for b in buckets])

# 'newsletters' 버킷이 목록에 있는지 확인
if "newsletters" not in [b.name for b in buckets]:
    print("❌ 'newsletters' 버킷이 없습니다. 대시보드에서 생성해 주세요.")
else:
    print("✅ 버킷 확인 완료!")