"""
Backend FastAPI para el generador de Shorts.

Endpoints:
  GET  /              → frontal HTML
  POST /api/generate  → lanza generación, devuelve job_id
  GET  /api/progress/{job_id} → stream SSE con progreso
  GET  /api/video/{filename}  → descarga el MP4
  GET  /api/videos    → lista vídeos generados
"""
import asyncio
import json
import threading
import uuid
from datetime import datetime
from pathlib import Path
from queue import Queue, Empty
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from src import config
from src.main import generate_short


app = FastAPI(title="Shorts Generator")

# Directorio del frontal
WEB_DIR = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=str(WEB_DIR)), name="static")

# Jobs en memoria: job_id → Queue de eventos de progreso
# Para producción usarías Redis, pero para local esto sobra.
JOBS: dict[str, dict] = {}


class GenerateRequest(BaseModel):
    prompt: str
    duration: int = 50
    style: str = "photorealistic cinematic"
    voice_id: Optional[str] = None
    language: str = "es"


@app.get("/", response_class=HTMLResponse)
async def index():
    """Sirve el frontal HTML."""
    html_path = WEB_DIR / "index.html"
    return HTMLResponse(html_path.read_text(encoding="utf-8"))


@app.post("/api/generate")
async def start_generation(req: GenerateRequest):
    """Inicia la generación en un thread y devuelve el job_id."""
    if not req.prompt.strip():
        raise HTTPException(400, "El prompt no puede estar vacío")

    job_id = str(uuid.uuid4())
    JOBS[job_id] = {
        "queue": Queue(),
        "status": "running",
        "video_path": None,
        "error": None,
    }

    def progress_cb(step: str, pct: int, msg: str):
        JOBS[job_id]["queue"].put({
            "type": "progress",
            "step": step,
            "pct": pct,
            "msg": msg,
        })

    def run_job():
        try:
            video_path = generate_short(
                prompt=req.prompt,
                duration=req.duration,
                voice_id=req.voice_id,
                style=req.style,
                language=req.language,
                progress_callback=progress_cb,
            )
            JOBS[job_id]["status"] = "completed"
            JOBS[job_id]["video_path"] = str(video_path.name)
            JOBS[job_id]["queue"].put({
                "type": "completed",
                "filename": video_path.name,
            })
        except Exception as e:
            JOBS[job_id]["status"] = "error"
            JOBS[job_id]["error"] = str(e)
            JOBS[job_id]["queue"].put({
                "type": "error",
                "error": str(e),
            })

    thread = threading.Thread(target=run_job, daemon=True)
    thread.start()

    return {"job_id": job_id}


@app.get("/api/progress/{job_id}")
async def stream_progress(job_id: str):
    """Server-Sent Events: stream del progreso en tiempo real."""
    if job_id not in JOBS:
        raise HTTPException(404, "Job no encontrado")

    async def event_generator():
        job = JOBS[job_id]
        queue = job["queue"]

        while True:
            try:
                # Polling no bloqueante
                event = queue.get_nowait()
                yield f"data: {json.dumps(event)}\n\n"

                if event["type"] in ("completed", "error"):
                    break
            except Empty:
                # Si el job terminó y no hay más eventos, salimos
                if job["status"] in ("completed", "error") and queue.empty():
                    break
                await asyncio.sleep(0.3)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.get("/api/video/{filename}")
async def get_video(filename: str):
    """Devuelve el MP4 para reproducir/descargar."""
    # Seguridad básica: evitar path traversal
    if "/" in filename or "\\" in filename or ".." in filename:
        raise HTTPException(400, "Nombre inválido")

    video_path = config.OUTPUT_DIR / filename
    if not video_path.exists():
        raise HTTPException(404, "Vídeo no encontrado")

    return FileResponse(
        video_path,
        media_type="video/mp4",
        filename=filename,
    )


@app.get("/api/videos")
async def list_videos():
    """Lista los vídeos ya generados, más nuevos primero."""
    videos = []
    for mp4 in sorted(config.OUTPUT_DIR.glob("*.mp4"), reverse=True):
        stat = mp4.stat()
        videos.append({
            "filename": mp4.name,
            "size_mb": round(stat.st_size / (1024 * 1024), 2),
            "created": datetime.fromtimestamp(stat.st_mtime).isoformat(),
        })
    return {"videos": videos}


@app.get("/api/config-check")
async def config_check():
    """Comprueba si las API keys están configuradas."""
    try:
        config.validate_config()
        return {"ok": True}
    except RuntimeError as e:
        return {"ok": False, "error": str(e)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
