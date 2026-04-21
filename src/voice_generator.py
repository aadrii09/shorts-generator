"""Generación de voz con ElevenLabs."""
from pathlib import Path
from elevenlabs.client import ElevenLabs
from . import config


def generate_voice(text: str, output_path: Path, voice_id: str = None) -> Path:
    """
    Genera audio de voz a partir de texto usando ElevenLabs.

    Args:
        text: Texto a narrar.
        output_path: Path donde guardar el MP3.
        voice_id: ID de voz (opcional, usa el de config si no se pasa).

    Returns:
        Path al archivo de audio generado.
    """
    client = ElevenLabs(api_key=config.ELEVENLABS_API_KEY)
    voice = voice_id or config.ELEVENLABS_VOICE_ID

    print(f"  → Generando voz con ElevenLabs (voice_id={voice})...")

    audio_stream = client.text_to_speech.convert(
        voice_id=voice,
        model_id=config.ELEVENLABS_MODEL,
        text=text,
        output_format="mp3_44100_128",
        voice_settings={
            "stability": 0.5,
            "similarity_boost": 0.75,
            "style": 0.3,
            "use_speaker_boost": True,
        },
    )

    # audio_stream es un generador de bytes
    with open(output_path, "wb") as f:
        for chunk in audio_stream:
            if chunk:
                f.write(chunk)

    print(f"  ✓ Voz guardada en {output_path.name}")
    return output_path
