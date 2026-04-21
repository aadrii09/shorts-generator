"""Configuración central del proyecto."""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Directorios
ROOT_DIR = Path(__file__).parent.parent
OUTPUT_DIR = ROOT_DIR / "output"
TEMP_DIR = ROOT_DIR / "temp"
ASSETS_DIR = ROOT_DIR / "assets"

OUTPUT_DIR.mkdir(exist_ok=True)
TEMP_DIR.mkdir(exist_ok=True)
ASSETS_DIR.mkdir(exist_ok=True)

# API Keys
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "XrExE9yKIg1WjnnlVkGX")

# Configuración de vídeo
VIDEO_WIDTH = 1080
VIDEO_HEIGHT = 1920
VIDEO_FPS = 30

# Modelo de Claude
CLAUDE_MODEL = "claude-sonnet-4-5"

# Modelo TTS de ElevenLabs
ELEVENLABS_MODEL = "eleven_multilingual_v2"

# Modelo de imagen (Gemini 2.5 Flash Image / Nano Banana)
GEMINI_IMAGE_MODEL = "gemini-2.5-flash-image"


def validate_config():
    """Valida que todas las claves necesarias estén configuradas."""
    missing = []
    if not ANTHROPIC_API_KEY or ANTHROPIC_API_KEY.startswith("sk-ant-xxx"):
        missing.append("ANTHROPIC_API_KEY")
    if not ELEVENLABS_API_KEY or ELEVENLABS_API_KEY == "xxxxx":
        missing.append("ELEVENLABS_API_KEY")
    if not GOOGLE_API_KEY or GOOGLE_API_KEY == "xxxxx":
        missing.append("GOOGLE_API_KEY")

    if missing:
        raise RuntimeError(
            f"Faltan variables en .env: {', '.join(missing)}. "
            "Copia .env.example a .env y rellena tus claves."
        )
