"""
Shorts Generator - Genera un vídeo vertical automáticamente desde un prompt.

Uso CLI:
    python -m src.main "tu prompt aquí"
    python -m src.main "curiosidades sobre los pulpos" --duration 45 --style cinematic

Uso programático (usado por el backend web):
    from src.main import generate_short
    video_path = generate_short("prompt", duration=50)
"""
import argparse
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional

from . import config
from .script_generator import generate_script, get_full_narration
from .voice_generator import generate_voice
from .image_generator import generate_all_images
from .subtitle_generator import generate_subtitles, get_audio_duration
from .video_composer import compose_video


# Callback de progreso: (step_name, progress_pct, message)
ProgressCallback = Callable[[str, int, str], None]


def _default_progress(step: str, pct: int, msg: str):
    print(f"[{pct:3d}%] {step}: {msg}")


def generate_short(
    prompt: str,
    duration: int = 50,
    voice_id: Optional[str] = None,
    style: str = "photorealistic cinematic",
    language: str = "es",
    keep_temp: bool = False,
    progress_callback: Optional[ProgressCallback] = None,
) -> Path:
    """
    Genera un Short vertical a partir de un prompt.

    Returns:
        Path al vídeo MP4 generado.
    """
    cb = progress_callback or _default_progress
    config.validate_config()

    if shutil.which("ffmpeg") is None:
        raise RuntimeError("FFmpeg no encontrado en el PATH del sistema.")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_temp_dir = config.TEMP_DIR / f"run_{timestamp}"
    run_temp_dir.mkdir(parents=True, exist_ok=True)
    output_path = config.OUTPUT_DIR / f"short_{timestamp}.mp4"

    try:
        cb("script", 5, "Generando guion con Claude...")
        script = generate_script(prompt, duration)
        narration = get_full_narration(script)
        cb("script", 15, f"Guion listo: {len(script['scenes'])} escenas")

        cb("voice", 20, "Sintetizando voz con ElevenLabs...")
        voice_path = run_temp_dir / "voice.mp3"
        generate_voice(narration, voice_path, voice_id)
        audio_duration = get_audio_duration(voice_path)
        cb("voice", 35, f"Voz generada ({audio_duration:.1f}s)")

        n_scenes = len(script["scenes"])
        cb("images", 40, f"Generando {n_scenes} imágenes con Gemini...")
        image_paths = generate_all_images(script["scenes"], run_temp_dir, style)
        cb("images", 70, "Imágenes generadas")

        cb("subtitles", 75, "Transcribiendo audio para subtítulos...")
        srt_path = run_temp_dir / "subs.srt"
        generate_subtitles(voice_path, srt_path, language)
        cb("subtitles", 80, "Subtítulos generados")

        cb("compose", 85, "Montando vídeo con FFmpeg...")
        music_path = config.ASSETS_DIR / "background.mp3"
        music = music_path if music_path.exists() else None

        compose_video(
            image_paths=image_paths,
            voice_path=voice_path,
            srt_path=srt_path,
            output_path=output_path,
            temp_dir=run_temp_dir,
            audio_duration=audio_duration,
            music_path=music,
        )
        cb("done", 100, f"Vídeo completado: {output_path.name}")
        return output_path

    finally:
        if not keep_temp and run_temp_dir.exists():
            shutil.rmtree(run_temp_dir, ignore_errors=True)


def main():
    parser = argparse.ArgumentParser(description="Genera un Short vertical.")
    parser.add_argument("prompt", help="Tema o idea del vídeo")
    parser.add_argument("--duration", type=int, default=50)
    parser.add_argument("--voice-id", default=None)
    parser.add_argument("--style", default="photorealistic cinematic")
    parser.add_argument("--keep-temp", action="store_true")
    parser.add_argument("--language", default="es")
    args = parser.parse_args()

    print(f"\n{'='*60}\nSHORTS GENERATOR\n{'='*60}")
    print(f"Prompt: {args.prompt}\nDuración: {args.duration}s\n{'='*60}\n")

    try:
        output_path = generate_short(
            prompt=args.prompt,
            duration=args.duration,
            voice_id=args.voice_id,
            style=args.style,
            language=args.language,
            keep_temp=args.keep_temp,
        )
        print(f"\n✓ VÍDEO: {output_path}\n")
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
