"""
AI绘画平台 - 主应用
支持: GPT-Image, SDXL, Stable Diffusion
作者: AI Paint Studio
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse
import uvicorn
import asyncio
import os
from loguru import logger
from dotenv import load_dotenv

# 导入路由模块
from routers import generate, enhance, scraper, agent, gallery
from core.config import settings
from core.database import init_db

load_dotenv()

# ============================================================
# FastAPI 应用初始化
# ============================================================
app = FastAPI(
    title="AI绘画平台 - AI Paint Studio",
    description="全自动AI图片生成平台，支持多模型、爬虫参考、Prompt增强",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS配置 - 允许所有来源（无登录限制）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静态文件服务
os.makedirs("static/images", exist_ok=True)
os.makedirs("static/enhanced", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

# 注册路由
app.include_router(generate.router, prefix="/api/generate", tags=["图片生成"])
app.include_router(enhance.router, prefix="/api/enhance", tags=["图片增强"])
app.include_router(scraper.router, prefix="/api/scraper", tags=["爬虫参考"])
app.include_router(agent.router, prefix="/api/agent", tags=["AI代理"])
app.include_router(gallery.router, prefix="/api/gallery", tags=["作品库"])

@app.on_event("startup")
async def startup_event():
    logger.info("🚀 AI绘画平台启动中...")
    await init_db()
    logger.info("✅ 数据库初始化完成")
    logger.info("✅ AI绘画平台已就绪！")

@app.get("/")
async def root():
    return {"message": "AI绘画平台运行中", "version": "2.0.0", "status": "online"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "models": settings.AVAILABLE_MODELS}

# WebSocket实时通信
@app.websocket("/ws/progress/{task_id}")
async def websocket_progress(websocket: WebSocket, task_id: str):
    await websocket.accept()
    try:
        while True:
            # 推送生成进度
            from core.task_manager import get_task_progress
            progress = await get_task_progress(task_id)
            await websocket.send_json(progress)
            if progress.get("status") in ["completed", "failed"]:
                break
            await asyncio.sleep(0.5)
    except Exception as e:
        logger.error(f"WebSocket错误: {e}")
    finally:
        await websocket.close()

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        workers=1,
        log_level="info"
    )
