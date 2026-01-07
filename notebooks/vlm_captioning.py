import os
import torch
from pathlib import Path
from PIL import Image
from transformers import Qwen2VLForConditionalGeneration, AutoProcessor
from qwen_vl_utils import process_vision_info
from tqdm import tqdm

# 1. 모델 및 프로세서 로드 (RTX 5090 최적화)
model_name = "Qwen/Qwen2-VL-7B-Instruct"
print(f"🚀 {model_name} 로딩 중...")

# 5090의 성능을 위해 bfloat16과 flash_attention_2 사용
model = Qwen2VLForConditionalGeneration.from_pretrained(
    model_name,
    torch_dtype=torch.bfloat16,
    attn_implementation="flash_attention_2",
    device_map="auto",
)
processor = AutoProcessor.from_pretrained(model_name)

def generate_caption(image_path):
    """이미지/수식을 분석하여 텍스트로 설명 생성"""
    
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "image", "image": str(image_path)},
                {"type": "text", "text": "이 이미지는 논문에서 추출된 것입니다. 도표라면 내용을 요약하고, 수식이라면 LaTeX로 변환해줘. 그림이라면 무엇을 설명하는지 한국어로 자세히 설명해줘."}
            ],
        }
    ]

    # 프로세서 처리
    text = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    image_inputs, video_inputs = process_vision_info(messages)
    inputs = processor(
        text=[text],
        images=image_inputs,
        videos=video_inputs,
        padding=True,
        return_tensors="pt",
    ).to("cuda")

    # 추론
    generated_ids = model.generate(**inputs, max_new_tokens=512)
    generated_ids_trimmed = [
        out_ids[len(in_ids) :] for in_ids, out_ids in zip(inputs.input_ids, generated_ids)
    ]
    output_text = processor.batch_decode(
        generated_ids_trimmed, skip_special_tokens=True, clean_up_tokenization_spaces=False
    )[0]
    
    return output_text

def process_all_images(base_dir):
    """Marker가 만든 이미지 폴더들을 순회하며 캡션 파일 생성"""
    target_dir = Path(base_dir)
    # Marker가 이미지들을 저장하는 경로 구조에 맞춰 탐색 (예: datasets/done/images)
    image_files = list(target_dir.glob("**/*.png")) + list(target_dir.glob("**/*.jpg"))
    
    print(f"📸 총 {len(image_files)}개의 이미지를 발견했습니다.")

    for img_path in tqdm(image_files, desc="VLM 분석 중"):
        caption_file = img_path.with_suffix(".txt")
        
        # 이미 처리된 파일은 건너뛰기
        if caption_file.exists():
            continue
            
        try:
            caption = generate_caption(img_path)
            with open(caption_file, "w", encoding="utf-8") as f:
                f.write(caption)
        except Exception as e:
            print(f"❌ {img_path.name} 처리 실패: {e}")

if __name__ == "__main__":
    # 프로젝트 루트에서 실행 중이므로 바로 datasets/done을 봅니다.
    # resolve()를 사용하여 절대 경로로 확실하게 잡습니다.
    DONE_DIR = Path("datasets/done").resolve() 
    
    if not DONE_DIR.exists():
        print(f"❌ 경로를 찾을 수 없습니다: {DONE_DIR}")
    else:
        process_all_images(DONE_DIR)