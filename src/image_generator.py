"""Generación de imágenes con Gemini 2.5 Flash Image (Nano Banana)."""
from pathlib import Path
from google import genai
from google.genai import types
from PIL import Image
from io import BytesIO
from . import config


def generate_image(prompt: str, output_path: Path, style: str = "photorealistic cinematic") -> Path:
    """
    Genera una imagen a partir de un prompt usando Gemini.

    Args:
        prompt: Descripción de la imagen en inglés.
        output_path: Path donde guardar el PNG.
        style: Estilo visual aplicado a todas las imágenes.

    Returns:
        Path al archivo de imagen generado.
    """
    client = genai.Client(api_key=config.GOOGLE_API_KEY)

    # Prompt enriquecido para formato vertical y estilo consistente
    full_prompt = (
        f"{prompt}. Style: {style}, vertical 9:16 aspect ratio, "
        f"high detail, dramatic lighting, professional composition."
    )

    response = client.models.generate_content(
        model=config.GEMINI_IMAGE_MODEL,
        contents=full_prompt,
    )

    # Extraer la imagen de la respuesta
    image_saved = False
    for part in response.candidates[0].content.parts:
        if part.inline_data is not None:
            image = Image.open(BytesIO(part.inline_data.data))

            # Asegurar formato vertical 9:16 (1080x1920)
            image = _fit_to_vertical(image)
            image.save(output_path, "PNG")
            image_saved = True
            break

    if not image_saved:
        raise RuntimeError(f"Gemini no devolvió imagen para el prompt: {prompt}")

    return output_path


def _fit_to_vertical(image: Image.Image) -> Image.Image:
    """Ajusta la imagen al formato 1080x1920 (vertical) con crop centrado."""
    target_w, target_h = config.VIDEO_WIDTH, config.VIDEO_HEIGHT
    src_w, src_h = image.size
    target_ratio = target_w / target_h
    src_ratio = src_w / src_h

    if src_ratio > target_ratio:
        # Imagen más ancha: recortamos laterales
        new_w = int(src_h * target_ratio)
        left = (src_w - new_w) // 2
        image = image.crop((left, 0, left + new_w, src_h))
    else:
        # Imagen más alta: recortamos arriba/abajo
        new_h = int(src_w / target_ratio)
        top = (src_h - new_h) // 2
        image = image.crop((0, top, src_w, top + new_h))

    return image.resize((target_w, target_h), Image.LANCZOS)


def generate_all_images(scenes: list, temp_dir: Path, style: str) -> list[Path]:
    """
    Genera todas las imágenes de las escenas.

    Args:
        scenes: Lista de escenas con 'visual_prompt'.
        temp_dir: Directorio donde guardar las imágenes.
        style: Estilo visual global.

    Returns:
        Lista de Paths a las imágenes generadas, en orden.
    """
    print(f"  → Generando {len(scenes)} imágenes con Gemini...")
    image_paths = []
    for i, scene in enumerate(scenes):
        img_path = temp_dir / f"scene_{i:02d}.png"
        print(f"    [{i+1}/{len(scenes)}] {scene['visual_prompt'][:60]}...")
        generate_image(scene["visual_prompt"], img_path, style)
        image_paths.append(img_path)
    print(f"  ✓ Todas las imágenes generadas")
    return image_paths
