"""Generación de subtítulos sincronizados usando Whisper."""
from pathlib import Path
import whisper


def generate_subtitles(audio_path: Path, srt_path: Path, language: str = "es") -> Path:
    """
    Transcribe el audio generando un archivo SRT con timestamps.

    Usa whisper 'base' por defecto (buen equilibrio velocidad/calidad).
    Para más precisión usa 'small' o 'medium'.

    Args:
        audio_path: Path al archivo de audio.
        srt_path: Path donde guardar el SRT.
        language: Código de idioma ISO (es, en, ...).

    Returns:
        Path al archivo SRT generado.
    """
    print(f"  → Transcribiendo audio con Whisper...")

    model = whisper.load_model("base")
    result = model.transcribe(
        str(audio_path),
        language=language,
        word_timestamps=True,
        verbose=False,
    )

    # Generar SRT con segmentos cortos (estilo Shorts: 2-4 palabras por línea)
    srt_lines = []
    subtitle_idx = 1

    for segment in result["segments"]:
        words = segment.get("words", [])
        if not words:
            continue

        # Agrupar palabras en chunks de 2-4 palabras
        chunk = []
        chunk_start = None
        for word in words:
            if chunk_start is None:
                chunk_start = word["start"]
            chunk.append(word["word"].strip())

            if len(chunk) >= 3:
                chunk_end = word["end"]
                srt_lines.append(_format_srt_entry(
                    subtitle_idx, chunk_start, chunk_end, " ".join(chunk)
                ))
                subtitle_idx += 1
                chunk = []
                chunk_start = None

        # Resto de palabras si queda chunk incompleto
        if chunk and chunk_start is not None:
            chunk_end = words[-1]["end"]
            srt_lines.append(_format_srt_entry(
                subtitle_idx, chunk_start, chunk_end, " ".join(chunk)
            ))
            subtitle_idx += 1

    srt_path.write_text("\n".join(srt_lines), encoding="utf-8")
    print(f"  ✓ Subtítulos guardados en {srt_path.name}")
    return srt_path


def _format_srt_entry(idx: int, start: float, end: float, text: str) -> str:
    """Formatea una entrada SRT."""
    return f"{idx}\n{_format_time(start)} --> {_format_time(end)}\n{text.upper()}\n"


def _format_time(seconds: float) -> str:
    """Formato SRT: HH:MM:SS,mmm"""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds - int(seconds)) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def get_audio_duration(audio_path: Path) -> float:
    """Devuelve la duración del audio en segundos usando Whisper."""
    import subprocess
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(audio_path)],
        capture_output=True, text=True, check=True,
    )
    return float(result.stdout.strip())
