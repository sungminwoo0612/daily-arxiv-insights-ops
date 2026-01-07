import os
import json
from pathlib import Path
from tqdm import tqdm

# Marker 라이브러리 임포트
from marker.converters.pdf import PdfConverter
from marker.models import create_model_dict
from marker.output import text_from_rendered

def run_marker_batch():
    # 1. 경로 설정
    # 현재 파일(notebooks/marker_batch_process.py) 위치 기준 프로젝트 루트 확보
    PROJECT_ROOT = Path(__file__).resolve().parent.parent
    SOURCE_DIR = PROJECT_ROOT / "datasets"
    OUTPUT_DIR = SOURCE_DIR / "done"

    # 결과 저장 폴더 생성
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # 2. 모델 로드 (루프 밖에서 한 번만 실행하여 GPU 메모리 효율화)
    print("🚀 Marker 모델 로드 중 (RTX 5090 가속 활성화)...")
    model_lst = create_model_dict()
    converter = PdfConverter(artifact_dict=model_lst)

    # 3. 처리할 PDF 파일 목록 가져오기 (이미 UUID로 이름이 변경된 파일들)
    pdf_files = list(SOURCE_DIR.glob("*.pdf"))
    print(f"📂 총 {len(pdf_files)}개의 PDF 파일을 찾았습니다.")

    processed_count = 0
    skipped_count = 0

    # 4. 반복문 실행
    for pdf_path in tqdm(pdf_files, desc="논문 변환 및 이미지 추출"):
        try:
            # 출력 파일 및 자산 폴더 경로 설정
            # 예: datasets/done/UUID.md, datasets/done/UUID_assets/
            output_file_path = OUTPUT_DIR / f"{pdf_path.stem}.md"
            image_dir = OUTPUT_DIR / f"{pdf_path.stem}_assets"
            
            # [핵심 로직]: .md 파일과 이미지 폴더가 모두 존재할 때만 건너뜀
            # 만약 텍스트만 있고 이미지가 없다면 다시 실행하여 이미지를 추출합니다.
            if output_file_path.exists() and image_dir.exists() and any(image_dir.iterdir()):
                skipped_count += 1
                continue

            # 변환 실행
            # langs=["English", "Korean"] 등을 추가하여 OCR 정확도를 높일 수 있습니다.
            rendered = converter(str(pdf_path))
            full_text, output_format, images = text_from_rendered(rendered)

            # 1) Markdown 텍스트 저장
            with open(output_file_path, "w", encoding="utf-8") as f:
                f.write(full_text)
            
            # 2) 이미지(도표, 수식) 저장
            if images:
                image_dir.mkdir(parents=True, exist_ok=True)
                for img_name, img_obj in images.items():
                    # PIL Image 객체를 해당 폴더에 저장
                    img_obj.save(image_dir / img_name)
                # print(f"   📸 {pdf_path.stem}: {len(images)}개 이미지 저장 완료")
            
            processed_count += 1
            
        except Exception as e:
            print(f"❌ {pdf_path.name} 변환 실패: {str(e)}")

    print(f"\n" + "="*50)
    print(f"✅ 작업 완료 요약")
    print(f"   - 신규 처리(이미지 포함): {processed_count}건")
    print(f"   - 기존 파일 유지(스킵): {skipped_count}건")
    print(f"   - 결과물 위치: {OUTPUT_DIR}")
    print("="*50)

if __name__ == "__main__":
    run_marker_batch()