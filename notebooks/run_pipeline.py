import subprocess
import sys
import os
from pathlib import Path

# 1. 경로 설정 (사용자 환경에 맞춤)
# 현재 파일 위치 기준 상위 폴더를 프로젝트 루트로 설정
PROJECT_ROOT = Path(__file__).parent.parent if Path(Path.cwd()).name == 'notebooks' else Path.cwd()
SCRIPTS_DIR = PROJECT_ROOT / "notebooks"  # 실제 스크립트들이 모여 있는 곳
PYTHON_EXE = sys.executable  # 현재 가상환경의 python 경로를 자동으로 사용

def run_step(script_name, description):
    """지정한 스크립트를 실행하고 결과를 확인합니다."""
    script_path = SCRIPTS_DIR / script_name
    
    if not script_path.exists():
        print(f"❌ 파일을 찾을 수 없습니다: {script_path}")
        return False

    print(f"\n" + "="*50)
    print(f"🚀 {description} 실행 중...")
    print(f"📍 경로: {script_path}")
    print("="*50)

    # subprocess를 사용하여 별도 프로세스로 실행
    result = subprocess.run([PYTHON_EXE, str(script_path)], capture_output=False, text=True)

    if result.returncode != 0:
        print(f"❌ {description} 실패 (Exit Code: {result.returncode})")
        return False
    
    print(f"✅ {description} 완료!")
    return True

def main_pipeline():
    # --- [데이터 정합성 확인] ---
    # 0단계: 메타데이터 및 DB 기초 정제 (필요 시 활성화)
    # if not run_step("00_metadata_sync.py", "메타데이터 동기화"): return

    # --- [본문 및 시각 자료 추출] ---
    # 1단계: Marker (PDF -> MD + Image Assets 추출)
    # *주의*: 이 스크립트는 '이미지가 없는 경우에만 재실행'하는 로직이 포함된 버전이어야 합니다.
    if not run_step("marker_batch_process.py", "Marker 본문 및 이미지 추출"): return

    # --- [AI 분석 단계 (RTX 5090 활용)] ---
    # 2단계: Qwen2-VL (추출된 PNG 이미지를 텍스트로 캡셔닝)
    if not run_step("vlm_captioning.py", "VLM 이미지/수식 분석"): return

    # 3단계: Stable Diffusion (논문 제목 기반 뉴스레터 썸네일 생성)
    if not run_step("sd_generator.py", "SDXL 썸네일 자동 생성"): return

    # --- [최종 발행 및 저장] ---
    # 4단계: Gemini 요약 및 Supabase 최종 적재
    # (MD + VLM 캡션 결합 -> Gemini 요약 -> Supabase Storage & Table 업로드)
    if not run_step("final_summarizer.py", "Gemini 최종 요약 및 Supabase 발행"): return

    print("\n" + "🎉"*20)
    print("모든 논문의 뉴스레터 발행 및 DB 적재가 완료되었습니다!")
    print("🎉"*20)

if __name__ == "__main__":
    # 작업 디렉토리 고정 (상대 경로 오류 방지)
    os.chdir(PROJECT_ROOT)
    main_pipeline()