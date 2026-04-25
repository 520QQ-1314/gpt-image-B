"""
多模型图片生成核心
支持: SDXL本地、HuggingFace API、OpenAI、Together AI
自动降级：本地 > HF API > OpenAI > Together AI
"""

import os
import io
import uuid
import asyncio
import httpx
import base64
from pathlib import Path
from PIL import Image
from loguru import logger
from typing import Optional, Callable
import torch

class ImageGenerator:
    """
    统一图片生成接口
    自动选择最优可用模型
    """
    
    def __init__(self):
        self.local_pipeline = None
        self.save_dir = Path("./static/images")
        self.save_dir.mkdir(parents=True, exist_ok=True)
        
        self.hf_headers = {
            "Authorization": f"Bearer {os.getenv('HF_API_KEY', '')}"
        }
        
        # 模型优先级（免费优先）
        self.model_priority = [
            "sdxl-local",
            "huggingface-sdxl",
            "huggingface-sd21",
            "together-ai",
            "openai-gpt-image"
        ]
    
    async def initialize_local_model(self):
        """初始化本地SDXL模型（异步加载，不阻塞启动）"""
        try:
            logger.info("📦 正在加载本地SDXL模型...")
            
            from diffusers import (
                StableDiffusionXLPipeline, 
                DPMSolverMultistepScheduler,
                AutoencoderKL
            )
            
            # 检查CUDA可用性
            device = "cuda" if torch.cuda.is_available() else "cpu"
            dtype = torch.float16 if device == "cuda" else torch.float32
            
            logger.info(f"🖥️ 使用设备: {device}")
            
            # 加载VAE（更好的图片质量）
            vae = AutoencoderKL.from_pretrained(
                "madebyollin/sdxl-vae-fp16-fix",
                torch_dtype=dtype
            )
            
            # 加载SDXL Pipeline
            self.local_pipeline = StableDiffusionXLPipeline.from_pretrained(
                "stabilityai/stable-diffusion-xl-base-1.0",
                vae=vae,
                torch_dtype=dtype,
                use_safetensors=True,
                variant="fp16" if device == "cuda" else None
            )
            
            # 优化调度器
            self.local_pipeline.scheduler = DPMSolverMultistepScheduler.from_config(
                self.local_pipeline.scheduler.config,
                algorithm_type="sde-dpmsolver++"
            )
            
            if device == "cuda":
                self.local_pipeline.enable_model_cpu_offload()
                self.local_pipeline.enable_xformers_memory_efficient_attention()
            
            self.local_pipeline = self.local_pipeline.to(device)
            logger.info("✅ 本地SDXL模型加载完成！")
            return True
            
        except Exception as e:
            logger.warning(f"⚠️ 本地模型加载失败: {e}")
            logger.info("将使用API模型作为备选")
            return False
    
    async def generate(
        self,
        positive_prompt: str,
        negative_prompt: str = "",
        model: str = "auto",
        width: int = 1024,
        height: int = 1024,
        steps: int = 30,
        guidance_scale: float = 7.5,
        seed: int = -1,
        progress_callback: Optional[Callable] = None
    ) -> dict:
        """
        统一生成接口
        
        Returns:
            dict: {
                image_url: str,
                image_path: str, 
                model_used: str,
                generation_time: float,
                seed: int
            }
        """
        import time
        start_time = time.time()
        
        if seed == -1:
            import random
            seed = random.randint(0, 2**32 - 1)
        
        image_id = str(uuid.uuid4())[:8]
        
        # 自动选择模型
        if model == "auto":
            model = await self._select_best_model()
        
        logger.info(f"🎨 开始生成 | 模型: {model} | 尺寸: {width}x{height}")
        
        try:
            if model == "sdxl-local" and self.local_pipeline:
                image = await self._generate_local(
                    positive_prompt, negative_prompt, 
                    width, height, steps, guidance_scale, seed,
                    progress_callback
                )
            elif model == "huggingface-sdxl":
                image = await self._generate_huggingface_sdxl(
                    positive_prompt, negative_prompt, width, height
                )
            elif model == "huggingface-sd21":
                image = await self._generate_huggingface_sd21(
                    positive_prompt, negative_prompt, width, height
                )
            elif model == "together-ai":
                image = await self._generate_together_ai(
                    positive_prompt, width, height
                )
            elif model == "openai-gpt-image":
                image = await self._generate_openai(
                    positive_prompt, width, height
                )
            else:
                # 降级链
                image = await self._generate_with_fallback(
                    positive_prompt, negative_prompt, width, height
                )
            
            # 保存图片
            image_path = self.save_dir / f"{image_id}.png"
            image.save(str(image_path), "PNG", quality=95)
            
            generation_time = time.time() - start_time
            
            logger.info(f"✅ 生成完成 | 耗时: {generation_time:.2f}s | ID: {image_id}")
            
            return {
                "success": True,
                "image_url": f"/static/images/{image_id}.png",
                "image_path": str(image_path),
                "image_id": image_id,
                "model_used": model,
                "generation_time": round(generation_time, 2),
                "seed": seed,
                "dimensions": f"{width}x{height}"
            }
            
        except Exception as e:
            logger.error(f"❌ 生成失败: {e}")
            # 尝试降级
            return await self._emergency_fallback(
                positive_prompt, negative_prompt, width, height, image_id
            )
    
    async def _generate_local(
        self, positive_prompt, negative_prompt, 
        width, height, steps, guidance_scale, seed,
        progress_callback
    ) -> Image.Image:
        """本地SDXL生成"""
        
        generator = torch.Generator().manual_seed(seed)
        
        # 在线程池中运行，避免阻塞事件循环
        loop = asyncio.get_event_loop()
        
        def run_pipeline():
            result = self.local_pipeline(
                prompt=positive_prompt,
                negative_prompt=negative_prompt,
