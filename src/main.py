"""
Shorts Generator - Genera un vídeo vertical automáticamente desde un prompt.

Uso:
    python -m src.main "tu prompt aquí"
    python -m src.main "curiosidades sobre los pulpos" --duration 45 --style cinematic
"""
import argparse
import shutil
import sys
from datetime import datetime
from pathlib import Path

from . import config
from .script_generator import generate_script, get_full_narration
from .voice_generator import generate_voice
from .image_generator import generate_all_images
from .subtitle_generator import generate_subtitles, get_audio_duration
from .video_composer import compose_video


def main():
    parser = argparse.ArgumentParser(
        description="Genera un Short vertical a partir de un prompt."
    )
    parser.add_argument("prompt", help="Tema o idea del vídeo")
    parser.add_argument("--duration", type=int, default=50,
                        help="Duración objetivo en segundos (default: 50)")
    parser.add_argument("--voice-id", default=None,
                        help="ID de voz de ElevenLabs (override del .env)")
    parser.add_argument("--style", default="photorealistic cinematic",
                        help="Estilo visual de las imágenes")
    parser.add_argument("--keep-temp", action="store_true",
                        help="No borrar archivos temporales")
    parser.add_argument("--language", default="es",
                        help="Idioma para subtítulos (default: es)")
    args = parser.parse_args()

    try:
        config.validate_config()
    except RuntimeError as e:
        print(f"✗ {e}")
        sys.exit(1)

    # Comprobar que ffmpeg está disponible
    if shutil.which("ffmpeg") is None:
        print("✗ FFmpeg no encontrado. Instálalo y asegúrate de que está en el PATH.")
        sys.exit(1)

    # Preparar directorio temporal único por ejecución
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_temp_dir = config.TEMP_DIR / f"run_{timestamp}"
    run_temp_dir.mkdir(parents=True, exist_ok=True)

    output_path = config.OUTPUT_DIR / f"short_{timestamp}.mp4"

    print(f"\n{'='*60}")
    print(f"SHORTS GENERATOR")
    print(f"{'='*60}")
    print(f"Prompt: {args.prompt}")
    print(f"Duración objetivo: {args.duration}s")
    print(f"Estilo: {args.style}")
    print(f"Output: {output_path}")
    print(f"{'='*60}\n")

    try:
        # 1. Guion
        print("[1/5] GUION")
        script = generate_script(args.prompt, args.duration)
        narration = get_full_narration(script)
        print(f"    Narración: {len(narration)} caracteres\n")

        # 2. Voz
        print("[2/5] VOZ")
        voice_path = run_temp_dir / "voice.mp3"
        generate_voice(narration, voice_path, args.voice_id)
        audio_duration = get_audio_duration(voice_path)
        print(f"    Duración real del audio: {audio_duration:.2f}s\n")

        # 3. Imágenes
        print("[3/5] IMÁGENES")
        image_paths = generate_all_images(script["scenes"], run_temp_dir, args.style)
        print()

        # 4. Subtítulos
        print("[4/5] SUBTÍTULOS")
        srt_path = run_temp_dir / "subs.srt"
        generate_subtitles(voice_path, srt_path, args.language)
        print()

        # 5. Ensamblaje
        print("[5/5] ENSAMBLAJE")
        music_path = config.ASSETS_DIR / "background.mp3"
        music = music_path if music_path.exists() else None
        if music:
            print(f"    Usando música de fondo: {music_path.name}")

        compose_video(
            image_paths=image_paths,
            voice_path=voice_path,
            srt_path=srt_path,
            output_path=output_path,
            temp_dir=run_temp_dir,
            audio_duration=audio_duration,
            music_path=music,
        )

        print(f"\n{'='*60}")
        print(f"✓ VÍDEO GENERADO CORRECTAMENTE")
        print(f"  {output_path}")
        print(f"{'='*60}\n")

    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        if args.keep_temp:
            print(f"  Archivos temporales en: {run_temp_dir}")
        raise
    finally:
        if not args.keep_temp and run_temp_dir.exists():
            shutil.rmtree(run_temp_dir, ignore_errors=True)


if __name__ == "__main__":
    main()
