import os
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client, Client

# 환경 설정
load_dotenv()
supabase: Client = create_client(os.environ.get("SUPABASE_URL"), os.environ.get("SUPABASE_KEY"))
BUCKET_NAME = "newsletters"
TABLE_NAME = "newsletter_posts"

def upload_thumbnail(image_path):
    """이미지 파일을 Supabase Storage에 업로드하고 공개 URL 반환"""
    file_name = Path(image_path).name
    with open(image_path, 'rb') as f:
        supabase.storage.from_(BUCKET_NAME).upload(
            path=file_name,
            file=f,
            file_options={"content-type": "image/png", "upsert": "true"}
        )
    # 공개 URL 가져오기
    public_url = supabase.storage.from_(BUCKET_NAME).get_public_url(file_name)
    return public_url

def save_final_post(pdf_filename, title, md_content, thumbnail_url):
    """최종 뉴스레터 데이터를 DB 테이블에 저장"""
    data = {
        "original_pdf_filename": pdf_filename,
        "title": title,
        "content_md": md_content,
        "thumbnail_url": thumbnail_url
    }
    supabase.table(TABLE_NAME).insert(data).execute()
    print(f"🎉 Supabase 최종 포스팅 저장 완료: {title}")