# Shorts Generator

Generador automático de vídeos verticales (Shorts / Reels / TikTok) a partir de un prompt, con **interfaz web** y CLI.

**Pipeline:** Prompt → Guion (Claude) → Voz (ElevenLabs) → Imágenes (Gemini) → Subtítulos (Whisper) → Vídeo montado (FFmpeg)

## Requisitos

- Python 3.10+
- FFmpeg instalado en el sistema
- API keys de: [Anthropic](https://console.anthropic.com), [ElevenLabs](https://elevenlabs.io), [Google AI Studio](https://aistudio.google.com/apikey)

## Instalación

### 1. FFmpeg

- **Windows**: `winget install ffmpeg`
- **macOS**: `brew install ffmpeg`
- **Linux**: `sudo apt install ffmpeg`

Verifica con: `ffmpeg -version`

### 2. Entorno Python

```bash
cd shorts-generator
python -m venv venv

# Activar:
venv\Scripts\activate        # Windows
source venv/bin/activate     # macOS/Linux

pip install -r requirements.txt
```

### 3. API keys

```bash
cp .env.example .env
```

Edita `.env` con tus claves:

```
ANTHROPIC_API_KEY=sk-ant-...
ELEVENLABS_API_KEY=...
GOOGLE_API_KEY=...
ELEVENLABS_VOICE_ID=XrExE9yKIg1WjnnlVkGX
```

## Uso (recomendado: interfaz web)

### Desde VS Code

1. Abre la carpeta en VS Code.
2. Selecciona intérprete del venv: `Ctrl+Shift+P` → "Python: Select Interpreter".
3. Pulsa **F5** y elige **"🌐 Servidor Web"**.
4. Abre [http://127.0.0.1:8000](http://127.0.0.1:8000) en el navegador.

### Desde terminal

```bash
python run_web.py
```

Luego abre [http://127.0.0.1:8000](http://127.0.0.1:8000).

### La interfaz te deja

- Escribir el prompt del vídeo
- Elegir duración, idioma, estilo visual
- Ver progreso en tiempo real (streaming)
- Reproducir el vídeo generado directamente
- Descargar el MP4
- Ver histórico de vídeos generados

## Uso CLI (alternativo)

```bash
python -m src.main "curiosidades sobre los pulpos" --duration 45
```

Opciones: `--duration`, `--voice-id`, `--style`, `--language`, `--keep-temp`.

## Estructura

```
shorts-generator/
├── src/
│   ├── main.py              # Lógica principal (reutilizable)
│   ├── config.py
│   ├── script_generator.py  # Guion con Claude
│   ├── voice_generator.py   # Voz con ElevenLabs
│   ├── image_generator.py   # Imágenes con Gemini
│   ├── subtitle_generator.py# Subtítulos con Whisper
│   └── video_composer.py    # Ensamblaje FFmpeg
├── web/
│   ├── server.py            # Backend FastAPI
│   └── static/index.html    # Frontal
├── output/                  # Vídeos generados
├── temp/                    # Archivos intermedios
├── assets/                  # background.mp3 opcional
├── run_web.py               # Lanzador del servidor
├── .env.example
└── requirements.txt
```

## Música de fondo (opcional)

Coloca `background.mp3` en `assets/` y se mezclará automáticamente con ducking.

## Costes aprox por Short

- Claude (guion): ~$0.002
- ElevenLabs (voz): ~$0.12
- Gemini (8-10 imágenes): ~$0.30-0.40
- **Total: ~$0.45 por vídeo**

## Próximas ampliaciones sugeridas

- `src/uploader_youtube.py` — subida automática a YouTube con la API oficial
- `src/uploader_tiktok.py` — TikTok Content Posting API
- `src/scheduler.py` — batch y publicación programada
- Historial persistente en SQLite con metadata
