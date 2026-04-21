"""Ensamblaje del vídeo final con FFmpeg.

Pipeline:
1. Calcular duración por escena según duración total del audio
2. Crear clips de vídeo con efecto Ken Burns (zoom lento) sobre cada imagen
3. Concatenar clips
4. Mezclar con audio de voz + (opcional) música de fondo con ducking
5. Quemar subtítulos
"""
import subprocess
from pathlib import Path
from . import config


def _run_ffmpeg(cmd: list, step_name: str):
    """Ejecuta FFmpeg y falla con error claro si algo va mal."""
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"ERROR en paso '{step_name}':")
        print(f"Comando: {' '.join(cmd)}")
        print(f"stderr:\n{result.stderr}")
        raise RuntimeError(f"FFmpeg falló en {step_name}")


def create_ken_burns_clip(image_path: Path, duration: float, output_path: Path, zoom_in: bool = True):
    """
    Crea un clip de vídeo de una imagen estática con efecto Ken Burns (zoom lento).

    Alterna entre zoom-in y zoom-out para que no todas las escenas se sientan iguales.
    """
    fps = config.VIDEO_FPS
    total_frames = int(duration * fps)
    w, h = config.VIDEO_WIDTH, config.VIDEO_HEIGHT

    if zoom_in:
        zoom_expr = f"min(zoom+0.0015,1.3)"
    else:
        zoom_expr = f"if(lte(zoom,1.0),1.3,max(1.001,zoom-0.0015))"

    zoompan = (
        f"zoompan=z='{zoom_expr}':"
        f"d={total_frames}:"
        f"x='iw/2-(iw/zoom/2)':"
        f"y='ih/2-(ih/zoom/2)':"
        f"s={w}x{h}:fps={fps}"
    )

    cmd = [
        "ffmpeg", "-y",
        "-loop", "1",
        "-i", str(image_path),
        "-vf", zoompan,
        "-t", f"{duration}",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-preset", "fast",
        "-crf", "20",
        str(output_path),
    ]
    _run_ffmpeg(cmd, f"Ken Burns clip {image_path.name}")


def concat_clips(clip_paths: list[Path], output_path: Path, temp_dir: Path):
    """Concatena varios clips de vídeo en uno solo."""
    concat_file = temp_dir / "concat_list.txt"
    concat_file.write_text(
        "\n".join(f"file '{p.resolve()}'" for p in clip_paths),
        encoding="utf-8",
    )

    cmd = [
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", str(concat_file),
        "-c", "copy",
        str(output_path),
    ]
    _run_ffmpeg(cmd, "concat clips")


def merge_audio_with_video(video_path: Path, voice_path: Path, output_path: Path, music_path: Path = None):
    """
    Añade la pista de voz al vídeo. Si hay música de fondo, la mezcla con ducking.
    """
    if music_path and music_path.exists():
        # Voz + música de fondo con ducking (música baja cuando habla la voz)
        cmd = [
            "ffmpeg", "-y",
            "-i", str(video_path),
            "-i", str(voice_path),
            "-i", str(music_path),
            "-filter_complex",
            # Música al 15%, voz al 100%, mezcla con sidechain compression
            "[2:a]volume=0.15[music];"
            "[1:a]volume=1.0[voice];"
            "[music][voice]sidechaincompress=threshold=0.03:ratio=8:attack=20:release=1000[ducked];"
            "[voice][ducked]amix=inputs=2:duration=first:dropout_transition=0[aout]",
            "-map", "0:v",
            "-map", "[aout]",
            "-c:v", "copy",
            "-c:a", "aac",
            "-b:a", "192k",
            "-shortest",
            str(output_path),
        ]
    else:
        # Solo voz
        cmd = [
            "ffmpeg", "-y",
            "-i", str(video_path),
            "-i", str(voice_path),
            "-map", "0:v",
            "-map", "1:a",
            "-c:v", "copy",
            "-c:a", "aac",
            "-b:a", "192k",
            "-shortest",
            str(output_path),
        ]
    _run_ffmpeg(cmd, "merge audio")


def burn_subtitles(video_path: Path, srt_path: Path, output_path: Path):
    """Quema los subtítulos en el vídeo con estilo para Shorts."""
    # Escape del path para filtergraph (Windows-friendly)
    srt_str = str(srt_path.resolve()).replace("\\", "/").replace(":", r"\:")

    style = (
        "FontName=Arial,FontSize=16,"
        "PrimaryColour=&HFFFFFF&,"
        "OutlineColour=&H000000&,"
        "BorderStyle=1,Outline=3,Shadow=0,"
        "Bold=1,Alignment=2,MarginV=150"
    )

    cmd = [
        "ffmpeg", "-y",
        "-i", str(video_path),
        "-vf", f"subtitles='{srt_str}':force_style='{style}'",
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "20",
        "-c:a", "copy",
        str(output_path),
    ]
    _run_ffmpeg(cmd, "burn subtitles")


def compose_video(
    image_paths: list[Path],
    voice_path: Path,
    srt_path: Path,
    output_path: Path,
    temp_dir: Path,
    audio_duration: float,
    music_path: Path = None,
):
    """
    Ensambla el vídeo final completo.

    Args:
        image_paths: Lista de imágenes por escena.
        voice_path: Archivo de voz (MP3).
        srt_path: Archivo de subtítulos.
        output_path: Path del vídeo final.
        temp_dir: Directorio temporal para clips intermedios.
        audio_duration: Duración del audio en segundos.
        music_path: Archivo de música de fondo (opcional).
    """
    print(f"  → Ensamblando vídeo con FFmpeg...")

    # Duración por escena (repartida uniformemente sobre la duración del audio)
    per_scene_duration = audio_duration / len(image_paths)
    print(f"    {len(image_paths)} escenas × {per_scene_duration:.2f}s = {audio_duration:.2f}s")

    # 1. Generar clips Ken Burns de cada imagen
    clip_paths = []
    for i, img_path in enumerate(image_paths):
        clip_path = temp_dir / f"clip_{i:02d}.mp4"
        create_ken_burns_clip(
            img_path,
            per_scene_duration,
            clip_path,
            zoom_in=(i % 2 == 0),
        )
        clip_paths.append(clip_path)

    # 2. Concatenar clips
    concat_video = temp_dir / "concat.mp4"
    concat_clips(clip_paths, concat_video, temp_dir)

    # 3. Añadir audio
    video_with_audio = temp_dir / "with_audio.mp4"
    merge_audio_with_video(concat_video, voice_path, video_with_audio, music_path)

    # 4. Quemar subtítulos
    burn_subtitles(video_with_audio, srt_path, output_path)

    print(f"  ✓ Vídeo final: {output_path}")
