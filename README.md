# Shorts Generator

Generador automático de vídeos verticales (Shorts/Reels/TikTok) a partir de un prompt.

Pipeline: **Prompt → Guion (Claude) → Voz (ElevenLabs) → Imágenes (Gemini) → Subtítulos (Whisper) → Vídeo montado (FFmpeg)**

## Requisitos

- Python 3.10+
- FFmpeg instalado en el sistema
- Cuentas y API keys de:
  - [Anthropic](https://console.anthropic.com) (Claude)
  - [ElevenLabs](https://elevenlabs.io)
  - [Google AI Studio](https://aistudio.google.com/apikey) (Gemini para imágenes)

## Instalación

### 1. Instalar FFmpeg

- **Windows**: `winget install ffmpeg` o descargar de [ffmpeg.org](https://ffmpeg.org/download.html)
- **macOS**: `brew install ffmpeg`
- **Linux**: `sudo apt install ffmpeg`

Verifica: `ffmpeg -version`

### 2. Clonar y preparar el entorno

```bash
cd shorts-generator
python -m venv venv

# Activar entorno virtual
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

pip install -r requirements.txt
```

### 3. Configurar API keys

Copia `.env.example` a `.env` y rellena tus claves:

```bash
cp .env.example .env
```

Edita `.env`:

```
ANTHROPIC_API_KEY=sk-ant-...
ELEVENLABS_API_KEY=...
GOOGLE_API_KEY=...
ELEVENLABS_VOICE_ID=21m00Tcm4TlvDq8ikWAM
```

## Uso desde VS Code

1. Abre la carpeta del proyecto en VS Code (`File > Open Folder`).
2. Selecciona el intérprete del venv: `Ctrl+Shift+P` → "Python: Select Interpreter" → elige el del venv.
3. Abre una terminal integrada (`Ctrl+ñ`).
4. Ejecuta:

```bash
python -m src.main "Cuéntame 3 curiosidades sobre los pulpos que no conocía"
```

El vídeo se genera en `output/short_YYYYMMDD_HHMMSS.mp4`.

### Opciones del CLI

```bash
python -m src.main "tu prompt aquí" [--duration 45] [--voice-id XXX] [--style cinematic]
```

- `--duration`: duración objetivo en segundos (default: 50)
- `--voice-id`: ID de voz de ElevenLabs (override del .env)
- `--style`: estilo visual para las imágenes (default: "photorealistic cinematic")
- `--keep-temp`: no borrar archivos temporales (útil para debug)

## Estructura del proyecto

```
shorts-generator/
├── src/
│   ├── __init__.py
│   ├── main.py              # Entry point / CLI
│   ├── config.py            # Configuración y carga de .env
│   ├── script_generator.py  # Guion con Claude
│   ├── voice_generator.py   # Voz con ElevenLabs
│   ├── image_generator.py   # Imágenes con Gemini
│   ├── subtitle_generator.py# Subtítulos con Whisper
│   └── video_composer.py    # Ensamblaje con FFmpeg
├── output/                  # Vídeos finales
├── temp/                    # Archivos intermedios
├── assets/                  # Música de fondo opcional
├── .env.example
├── requirements.txt
└── README.md
```

## Música de fondo (opcional)

Coloca un archivo `background.mp3` en `assets/` y se mezclará automáticamente con ducking.

## Costes estimados por Short

- Claude (guion): ~$0.002
- ElevenLabs (voz): ~$0.12
- Gemini (8-10 imágenes): ~$0.30-0.40
- **Total: ~$0.45 por vídeo**

## Siguientes pasos

Cuando el MVP funcione, añadir módulos en `src/`:
- `uploader_youtube.py` — subida automática
- `uploader_tiktok.py`
- `scheduler.py` — generación programada
