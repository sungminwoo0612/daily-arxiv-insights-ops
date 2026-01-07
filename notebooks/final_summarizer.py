import os
import re
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client, Client
# 최신 라이브러리로 변경 (FutureWarning 해결)
from google import genai
from google.genai import types

# 앞서 작성한 sd_generator.py에서 함수 임포트
from sd_generator import generate_thumbnail

# 1. 환경 설정 로드 및 검증
# 프로젝트 루트의 .env를 명시적으로 로드
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

api_key = os.environ.get("GOOGLE_API_KEY") # 00_etl_pipeline.ipynb와 이름 통일

if not api_key:
    print("❌ 오류: .env 파일에서 GOOGLE_API_KEY를 찾을 수 없습니다.")
    print(f"📍 .env 확인 경로: {env_path}")
    exit(1)

# 2. 클라이언트 초기화
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DONE_DIR = PROJECT_ROOT / "datasets" / "done"

# 최신 SDK 클라이언트 생성
client = genai.Client(api_key=api_key)
MODEL_ID = "gemini-2.0-flash" # 혹은 "gemini-1.5-pro"

supabase: Client = create_client(
    os.environ.get("SUPABASE_URL"), 
    os.environ.get("SUPABASE_KEY")
)

def enrich_markdown(md_path):
    """마크다운 내 이미지 태그를 VLM 분석 텍스트로 치환 (기존 로직 유지)"""
    with open(md_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    asset_dir = md_path.parent / f"{md_path.stem}_assets"
    img_pattern = r"!\[\]\((.*?)\)"
    
    def replace_with_caption(match):
        img_filename = match.group(1)
        caption_path = asset_dir / f"{img_filename}.txt"
        
        if caption_path.exists():
            with open(caption_path, "r", encoding="utf-8") as cf:
                caption_text = cf.read()
            return f"\n\n> 📊 **[논문 시각자료 분석]**: {caption_text}\n\n"
        return match.group(0)

    return re.sub(img_pattern, replace_with_caption, content)

def generate_blog_post(enriched_text):
    """최신 SDK 방식을 사용한 요약 생성"""
    prompt = f"""
    당신은 최신 AI 및 MLOps 기술을 전문적으로 다루는 기술 블로거입니다. 
    제공된 '시각자료 분석이 포함된 논문 본문'을 바탕으로 고품질 기술 블로그 포스팅을 작성하세요.

    [작성 가이드라인]
    1. 제목: 본문의 핵심을 관통하는 매력적인 제목 (# 사용)
    2. 구조: 서론 - 핵심 아이디어 - 시각자료 상세 분석 - 인사이트 순
    3. 기술적 깊이와 가독성을 동시에 확보할 것
    
    [논문 데이터]
    {enriched_text}
    """
    
    response = client.models.generate_content(
        model=MODEL_ID,
        contents=prompt
    )
    return response.text

def upload_to_supabase(md_path, title, final_content):
    try:
        # 1. 썸네일 생성 및 업로드
        thumb_filename = f"thumb_{md_path.stem}.png"
        thumb_path = generate_thumbnail(title, thumb_filename)
        
        with open(thumb_path, 'rb') as f:
            storage_res = supabase.storage.from_("newsletters").upload(
                path=thumb_filename,
                file=f,
                file_options={"content-type": "image/png", "upsert": "true"}
            )
        
        public_url = supabase.storage.from_("newsletters").get_public_url(thumb_filename)
        
        # 2. DB Insert/Upsert 시도
        data = {
            "original_pdf_filename": f"{md_path.stem}.pdf",
            "title": title,
            "content_md": final_content,
            "thumbnail_url": public_url
        }
        
        # 에러 확인을 위해 결과를 변수에 담고 출력
        response = supabase.table("newsletter_posts").upsert(data, on_conflict="original_pdf_filename").execute()
        print(f"✅ DB 응답 확인: {response}")
        
    except Exception as e:
        print(f"❌ Supabase 업로드 실패 ({md_path.stem}): {str(e)}")

def process_single_paper(md_path):
    print(f"🧐 처리 시작: {md_path.name}")
    
    try:
        enriched = enrich_markdown(md_path)
        final_post = generate_blog_post(enriched)
        
        # 제목 추출
        first_line = final_post.split('\n')[0]
        title = re.sub(r'^#\s*', '', first_line).strip()
        
        upload_to_supabase(md_path, title, final_post)
        
        # 로컬 백업
        output_file = md_path.parent / f"FINAL_POST_{md_path.stem}.md"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(final_post)
        
        print(f"✨ 발행 완료: {title}")
    except Exception as e:
        print(f"❌ {md_path.name} 처리 중 에러: {e}")

# notebooks/final_summarizer.py 하단 수정본
if __name__ == "__main__":
    # UUID 형식만 골라내는 정규표현식
    uuid_pattern = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$')
    
    md_files = list(DONE_DIR.glob("*.md"))
    
    for md_file in md_files:
        # 1. 파일명이 UUID 형태인 것(원본)만 처리합니다.
        # 2. FINAL_POST_... 형태의 파일은 처리 대상에서 제외하여 에러를 방지합니다.
        if uuid_pattern.match(md_file.stem):
            print(f"🚀 {md_file.name} 요약 및 업로드 시도 중...")
            process_single_paper(md_file)