import torch
from diffusers import StableDiffusionXLPipeline, UNet2DConditionModel, EulerDiscreteScheduler
from huggingface_hub import hf_hub_download
from safetensors.torch import load_file
import os
from pathlib import Path

# --- 경로 자동 설정 (스크립트 위치 기반) ---
# notebooks/sd_generator.py 위치에서 상위로 이동하여 프로젝트 루트 확보
BASE_DIR = Path(__file__).resolve().parent.parent
ASSETS_DIR = BASE_DIR / "datasets" / "assets"
ASSETS_DIR.mkdir(parents=True, exist_ok=True)

# --- 설정 ---
base = "stabilityai/stable-diffusion-xl-base-1.0"
repo = "ByteDance/SDXL-Lightning"
ckpt = "sdxl_lightning_4step_unet.safetensors"
DEVICE = "cuda"

# --- 모델 로드 (최초 1회 실행 시 다운로드 발생) ---
print(f"🎨 Stable Diffusion XL Lightning 로딩 중 ({DEVICE})...")
unet = UNet2DConditionModel.from_config(base, subfolder="unet").to(DEVICE, torch.float16)
unet.load_state_dict(load_file(hf_hub_download(repo, ckpt), device=DEVICE))
pipe = StableDiffusionXLPipeline.from_pretrained(base, unet=unet, torch_dtype=torch.float16, variant="fp16").to(DEVICE)
pipe.scheduler = EulerDiscreteScheduler.from_config(pipe.scheduler.config, timestep_spacing="trailing")

def generate_thumbnail(title, filename):
    """논문 제목을 기반으로 썸네일 생성"""
    output_path = ASSETS_DIR / filename
    
    prompt = f"A futuristic technology illustration for a blog post titled '{title}'. isometric view, digital art, vibrant colors, highly detailed, unreal engine 5 render, trending on artstation, data visualization concepts, glowing circuits."
    negative_prompt = "ugly, deformed, noisy, blurry, low contrast, realism, photo"

    print(f"⚡ 썸네일 생성 시작: {title}...")
    image = pipe(prompt, negative_prompt=negative_prompt, num_inference_steps=4, guidance_scale=0).images[0]
    
    # 저장
    image.save(output_path)
    print(f"✅ 썸네일 저장 완료: {output_path}")
    return str(output_path)

if __name__ == "__main__":
    test_title = "Machine Learning Operations (MLOps): Overview and Architecture"
    generate_thumbnail(test_title, "test_thumb.png")