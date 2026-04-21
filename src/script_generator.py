"""Generación del guion estructurado usando Claude."""
import json
import re
from anthropic import Anthropic
from . import config


SYSTEM_PROMPT = """Eres un guionista experto en vídeos cortos virales para YouTube Shorts, TikTok e Instagram Reels.

Tu tarea es escribir guiones en español (España neutro) que:
- Enganchen en los primeros 3 segundos (hook potente)
- Mantengan ritmo alto, frases cortas, sin paja
- Suenen humanos y naturales, no a texto de IA
- Eviten clichés tipo "¿sabías que...?", "prepárate para...", "en este vídeo te voy a contar..."
- Usen datos concretos, cifras, ejemplos, no generalidades
- Cierren con una frase que genere comentario o curiosidad, no con "suscríbete"

Divide el guion en escenas. Cada escena es 1-2 frases que se corresponden con una imagen visual.

Devuelve EXCLUSIVAMENTE un JSON válido, sin texto adicional, sin markdown, sin ```json```, con esta estructura:

{
  "title": "Título corto del vídeo (max 60 caracteres)",
  "scenes": [
    {
      "text": "Frase que se narrará en voz alta",
      "visual_prompt": "Descripción en INGLÉS de la imagen que acompaña esta frase. Detallada, con estilo visual, iluminación y composición. Formato vertical 9:16."
    }
  ]
}

Reglas del JSON:
- Entre 6 y 10 escenas
- Cada "text" entre 8 y 20 palabras
- Cada "visual_prompt" en inglés, 20-40 palabras, cinematográfico
- No uses comillas dobles dentro de los strings, usa comillas simples si es necesario"""


def generate_script(user_prompt: str, target_duration: int = 50) -> dict:
    """
    Genera un guion estructurado a partir del prompt del usuario.

    Args:
        user_prompt: Tema o idea del vídeo.
        target_duration: Duración objetivo en segundos.

    Returns:
        dict con keys: title, scenes[{text, visual_prompt}]
    """
    client = Anthropic(api_key=config.ANTHROPIC_API_KEY)

    user_message = f"""Tema del vídeo: {user_prompt}

Duración objetivo: {target_duration} segundos (aprox {int(target_duration * 2.5)} palabras totales).

Genera el guion ahora en formato JSON."""

    print(f"  → Generando guion con Claude...")
    response = client.messages.create(
        model=config.CLAUDE_MODEL,
        max_tokens=2000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    )

    raw_text = response.content[0].text.strip()

    # Limpiar posibles bloques de código markdown por si acaso
    raw_text = re.sub(r"^```(?:json)?\s*", "", raw_text)
    raw_text = re.sub(r"\s*```$", "", raw_text)

    try:
        script = json.loads(raw_text)
    except json.JSONDecodeError as e:
        print(f"Error parseando JSON de Claude:\n{raw_text}")
        raise RuntimeError(f"Claude no devolvió JSON válido: {e}")

    # Validar estructura mínima
    if "scenes" not in script or not isinstance(script["scenes"], list):
        raise RuntimeError("El guion no tiene 'scenes'")
    for i, scene in enumerate(script["scenes"]):
        if "text" not in scene or "visual_prompt" not in scene:
            raise RuntimeError(f"Escena {i} mal formada: {scene}")

    print(f"  ✓ Guion generado: {len(script['scenes'])} escenas")
    print(f"    Título: {script.get('title', '(sin título)')}")
    return script


def get_full_narration(script: dict) -> str:
    """Concatena todos los textos de las escenas en un único string narrable."""
    return " ".join(scene["text"] for scene in script["scenes"])
