"""
平台核心配置 - 支持免费API和本地模型
"""
import os
from pydantic_settings import BaseSettings
from typing import List, Optional

class Settings(BaseSettings):
    # ============================================================
    # 免费API配置（优先使用免费额度）
    # ============================================================
    
    # OpenAI GPT-Image-2 (免费tier)
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = "gpt-image-1"
    
    # Hugging Face (完全免费)
    HF_API_KEY: str = os.getenv("HF_API_KEY", "")
    HF_SDXL_ENDPOINT: str = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"
    HF_SD21_ENDPOINT: str = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-2-1"
    
    # Together AI (免费额度)
    TOGETHER_API_KEY: str = os.getenv("TOGETHER_API_KEY", "")
    TOGETHER_ENDPOINT: str = "https://api.together.xyz/v1/images/generations"
    
    # Replicate (免费额度)
    REPLICATE_API_TOKEN: str = os.getenv("REPLICATE_API_TOKEN", "")
    
    # ============================================================
    # 本地模型配置（完全免费，需要GPU）
    # ============================================================
    LOCAL_MODEL_PATH: str = "./models/checkpoints"
    USE_LOCAL_MODEL: bool = True
    LOCAL_MODEL_NAME: str = "stabilityai/stable-diffusion-xl-base-1.0"
    
    # ============================================================
    # 爬虫配置
    # ============================================================
    BEHANCE_BASE_URL: str = "https://www.behance.net"
    PINTEREST_BASE_URL: str = "https://www.pinterest.com"
    SCRAPER_DELAY: float = 1.5  # 礼貌爬取延迟
    MAX_REFERENCE_IMAGES: int = 20
    
    # ============================================================
    # 图片存储配置
    # ============================================================
    IMAGE_SAVE_DIR: str = "./static/images"
    ENHANCED_SAVE_DIR: str = "./static/enhanced"
    MAX_IMAGE_SIZE: int = 2048
    
    # ============================================================
    # 平台配置
    # ============================================================
    APP_NAME: str = "AI绘画平台"
    DEBUG: bool = True
    NO_LOGIN_REQUIRED: bool = True  # 无需登录
    
    # 可用模型列表
    AVAILABLE_MODELS: List[str] = [
        "sdxl-local",          # 本地SDXL（免费）
        "huggingface-sdxl",    # HF SDXL API（免费）
        "huggingface-sd21",    # HF SD2.1 API（免费）
        "openai-gpt-image",    # OpenAI（有免费额度）
        "together-ai",         # Together AI（免费额度）
    ]
    
    # 风格预设
    STYLE_PRESETS: dict = {
        "cyberpunk": "cyberpunk style, neon lights, dark atmosphere, futuristic city, rain, reflections, high contrast, dramatic lighting",
        "minimal": "minimalist design, clean lines, negative space, simple composition, elegant, modern",
        "abstract": "abstract art, geometric shapes, bold colors, artistic expression, non-representational",
        "3d": "3D rendering, octane render, photorealistic, depth of field, caustics, subsurface scattering",
        "fisheye": "fisheye lens, ultra wide angle, perspective distortion, immersive, dramatic",
        "complex": "intricate details, highly detailed, complex composition, elaborate, ornate, maximalist",
    }
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()
