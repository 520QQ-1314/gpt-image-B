"""
AI Prompt增强器 - 将简单描述转化为专业绘画指令
仿Midjourney风格，支持多种艺术风格
"""

import openai
import httpx
import os
from loguru import logger
from typing import Optional

class PromptEnhancer:
    """
    AI Prompt智能增强器
    将用户输入的简单描述转化为专业级绘画提示词
    """
    
    def __init__(self):
        self.openai_client = openai.AsyncOpenAI(
            api_key=os.getenv("OPENAI_API_KEY", "")
        )
        
        # 免费备用：使用Groq或本地LLM增强Prompt
        self.groq_api_key = os.getenv("GROQ_API_KEY", "")
        self.groq_base_url = "https://api.groq.com/openai/v1"
        
        # 专业绘画词汇库
        self.quality_boosters = [
            "masterpiece", "best quality", "ultra detailed",
            "8k uhd", "high resolution", "sharp focus",
            "professional photography", "award winning",
            "trending on artstation", "cinematic lighting"
        ]
        
        self.negative_prompts = {
            "universal": "ugly, blurry, low quality, distorted, deformed, bad anatomy, watermark, signature, text, jpeg artifacts, low resolution, worst quality, bad quality",
            "portrait": "extra fingers, mutated hands, poorly drawn hands, poorly drawn face, deformed, extra limbs",
            "landscape": "oversaturated, flat, boring composition",
        }
        
        # 艺术家风格参考库
        self.style_artists = {
            "cyberpunk": "in the style of Blade Runner, Ghost in the Shell, inspired by Syd Mead, Simon Stålenhag",
            "minimal": "inspired by Dieter Rams, Swiss Design, Bauhaus principles",
            "abstract": "inspired by Kandinsky, Mark Rothko, abstract expressionism",
            "3d": "Octane render, Blender 3D, CGI, by BEEPLE, hyperrealistic",
            "fisheye": "ultra wide angle lens, gopro effect, immersive perspective",
            "complex": "intricate, by Greg Rutkowski, detailed fantasy art, Warhammer 40K aesthetics",
        }
    
    async def enhance_prompt(
        self, 
        user_input: str, 
        style: str = "cyberpunk",
        aspect_ratio: str = "1:1",
        detail_level: str = "high"
    ) -> dict:
        """
        主增强函数 - 将用户输入转化为专业Prompt
        
        Args:
            user_input: 用户输入的简单描述
            style: 风格预设
            aspect_ratio: 图片比例
            detail_level: 细节程度
            
        Returns:
            dict: {positive_prompt, negative_prompt, metadata}
        """
        
        logger.info(f"🎨 增强Prompt: {user_input[:50]}...")
        
        try:
            # 尝试使用Groq（免费且快速）
            if self.groq_api_key:
                return await self._enhance_with_groq(
                    user_input, style, aspect_ratio, detail_level
                )
            # 备用：使用OpenAI
            elif os.getenv("OPENAI_API_KEY"):
                return await self._enhance_with_openai(
                    user_input, style, aspect_ratio, detail_level
                )
            # 最终备用：规则增强
            else:
                return self._enhance_with_rules(
                    user_input, style, aspect_ratio, detail_level
                )
                
        except Exception as e:
            logger.warning(f"AI增强失败，使用规则增强: {e}")
            return self._enhance_with_rules(
                user_input, style, aspect_ratio, detail_level
            )
    
    async def _enhance_with_groq(
        self, user_input, style, aspect_ratio, detail_level
    ) -> dict:
        """使用Groq LLM增强（免费API）"""
        
        system_prompt = """你是一个专业的AI绘画提示词专家，类似Midjourney Bot。
        你的任务是将用户的简单描述转化为高质量的英文绘画提示词。
        
        规则：
        1. 输出必须是英文
        2. 添加具体的视觉细节、光照、构图、材质描述
        3. 包含艺术风格关键词
        4. 添加质量提升词汇（masterpiece, ultra detailed等）
        5. 生成对应的负面提示词
        6. 参考Midjourney v6的提示词风格
        
        输出格式（JSON）：
        {
            "positive_prompt": "...",
            "negative_prompt": "...",
            "style_tags": ["...", "..."],
            "enhancement_notes": "..."
        }"""
        
        user_message = f"""
        用户描述: {user_input}
        风格: {style}
        比例: {aspect_ratio}
        细节程度: {detail_level}
        
        请生成专业的绘画提示词。
        """
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.groq_base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.groq_api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "llama-3.3-70b-versatile",  # Groq免费模型
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_message}
                    ],
                    "temperature": 0.8,
                    "max_tokens": 1024,
                    "response_format": {"type": "json_object"}
                },
                timeout=30.0
            )
            
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            
            import json
            enhanced = json.loads(content)
            
            # 添加质量增强词
            style_artist = self.style_artists.get(style, "")
            enhanced["positive_prompt"] = (
                f"{enhanced['positive_prompt']}, {style_artist}, "
                f"{', '.join(self.quality_boosters[:5])}"
            )
            
            return enhanced
    
    async def _enhance_with_openai(
        self, user_input, style, aspect_ratio, detail_level
    ) -> dict:
        """使用OpenAI增强"""
        
        response = await self.openai_client.chat.completions.create(
            model="gpt-4o-mini",  # 最便宜的模型
            messages=[
                {
                    "role": "system",
                    "content": "你是AI绘画提示词专家。将用户描述转化为专业英文绘画提示词，输出JSON格式，包含positive_prompt和negative_prompt字段。"
                },
                {
                    "role": "user",
                    "content": f"描述: {user_input}, 风格: {style}, 请优化为专业绘画提示词"
                }
            ],
            response_format={"type": "json_object"},
            max_tokens=512
        )
        
        import json
        return json.loads(response.choices[0].message.content)
    
    def _enhance_with_rules(
        self, user_input, style, aspect_ratio, detail_level
    ) -> dict:
        """规则增强（完全免费，无需API）"""
        
        # 中文转英文关键词映射
        cn_to_en = {
            "城市": "city", "夜晚": "night", "赛博": "cyberpunk",
            "机器人": "robot", "宇宙": "universe", "森林": "forest",
            "人物": "character", "龙": "dragon", "未来": "futuristic",
            "抽象": "abstract", "简约": "minimal", "复杂": "complex",
            "山": "mountain", "海": "ocean", "天空": "sky",
            "花": "flower", "建筑": "architecture", "战士": "warrior",
        }
        
        # 基础翻译
        enhanced_input = user_input
        for cn, en in cn_to_en.items():
            enhanced_input = enhanced_input.replace(cn, en)
        
        # 风格修饰词
        style_modifiers = {
            "cyberpunk": [
                "neon lights", "dark rainy streets", "holographic displays",
                "futuristic megacity", "chrome and steel", "neon signs",
                "flying cars", "dystopian atmosphere", "rain reflections",
                "high contrast", "dramatic lighting", "blade runner aesthetic"
            ],
            "minimal": [
                "minimalist", "clean composition", "white background",
                "negative space", "simple geometric forms", "elegant",
                "sophisticated", "modern design", "swiss style"
            ],
            "abstract": [
                "abstract expressionism", "bold geometric shapes",
                "vibrant colors", "dynamic composition", "non-figurative",
                "artistic expression", "modern art", "color field painting"
            ],
            "3d": [
                "3D render", "octane render", "cinema 4d", "photorealistic",
                "subsurface scattering", "global illumination", "ray tracing",
                "depth of field", "volumetric light", "PBR materials"
            ],
            "fisheye": [
                "fisheye lens", "ultra wide 8mm", "barrel distortion",
                "immersive perspective", "dramatic angle", "curved horizon"
            ],
            "complex": [
                "intricate details", "highly ornate", "baroque",
                "detailed textures", "elaborate", "complex composition",
                "maximalist", "rich in detail"
            ],
        }
        
        selected_style = style_modifiers.get(style, style_modifiers["cyberpunk"])
        style_text = ", ".join(selected_style[:6])
        artist_ref = self.style_artists.get(style, "")
        quality_text = ", ".join(self.quality_boosters[:6])
        
        positive_prompt = f"{enhanced_input}, {style_text}, {artist_ref}, {quality_text}"
        negative_prompt = self.negative_prompts["universal"]
        
        return {
            "positive_prompt": positive_prompt,
            "negative_prompt": negative_prompt,
            "style_tags": selected_style[:4],
            "enhancement_notes": f"规则增强 | 风格: {style} | 比例: {aspect_ratio}"
        }


# 全局实例
prompt_enhancer = PromptEnhancer()
