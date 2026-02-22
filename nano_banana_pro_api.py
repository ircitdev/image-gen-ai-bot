"""
Google Gemini 3 Pro Image (Nano Banana Pro) API Integration
Model: nano-banana-pro-preview / gemini-3-pro-image-preview
Supports: Text-to-image with reference images (multimodal)
"""

import requests
import base64
from io import BytesIO
from settings import GOOGLE_AI_API_KEY

# Nano Banana Pro API endpoint
NANO_BANANA_PRO_URL = "https://generativelanguage.googleapis.com/v1beta/models/nano-banana-pro-preview:generateContent"

# Маппинг форматов
ASPECT_RATIO_MAP = {
    "1:1": "1:1",
    "16:9": "16:9",
    "9:16": "9:16",
    "3:2": "3:4",
    "2:3": "4:3",
    "4:3": "4:3",
    "3:4": "3:4",
    "21:9": "16:9",
    "9:21": "9:16",
    "5:4": "4:3",
    "4:5": "3:4"
}


def generate_with_nano_banana_pro(
    prompt: str,
    reference_images: list = None,
    aspect_ratio: str = "1:1",
    num_images: int = 1
) -> list:
    """
    Генерирует изображение через Nano Banana Pro (Gemini 3 Pro Image)

    Args:
        prompt: Текстовый промпт для генерации
        reference_images: Список BytesIO объектов с референсными изображениями (опционально)
        aspect_ratio: Соотношение сторон (1:1, 3:4, 4:3, 9:16, 16:9)
        num_images: Количество изображений (1-4)

    Returns:
        Список BytesIO объектов с изображениями
    """
    if not GOOGLE_AI_API_KEY:
        raise ValueError("GOOGLE_AI_API_KEY not configured")

    # Преобразуем формат
    imagen_ratio = ASPECT_RATIO_MAP.get(aspect_ratio, "1:1")
    num_images = min(max(1, num_images), 4)

    # URL с API ключом
    url = f"{NANO_BANANA_PRO_URL}?key={GOOGLE_AI_API_KEY}"

    headers = {
        "Content-Type": "application/json"
    }

    # Формируем content части (текст + изображения если есть)
    parts = []

    # Если есть референсные изображения, добавляем их
    if reference_images:
        for idx, ref_img in enumerate(reference_images, start=1):
            ref_img.seek(0)
            img_bytes = ref_img.read()
            img_base64 = base64.b64encode(img_bytes).decode('utf-8')

            parts.append({
                "inline_data": {
                    "mime_type": "image/png",
                    "data": img_base64
                }
            })

        # Промпт с упоминанием референсов
        full_prompt = f"{prompt}\n\nUse the provided reference image(s) as inspiration for style, composition, or subject."
    else:
        # Обычный текстовый промпт
        full_prompt = prompt

    # Добавляем текстовый промпт
    parts.append({
        "text": full_prompt
    })

    # Формат запроса для generateContent
    payload = {
        "contents": [
            {
                "parts": parts
            }
        ],
        "generationConfig": {
            "temperature": 1.0,
            "topP": 0.95,
            "topK": 64,
            "candidateCount": num_images,
            "responseModalities": ["image"],  # Генерируем изображения
            "aspectRatio": imagen_ratio
        }
    }

    print(f"[Nano Banana Pro] 🍌💎 Generating with prompt: {prompt[:100]}...")
    if reference_images:
        print(f"[Nano Banana Pro] Using {len(reference_images)} reference image(s)")
    print(f"[Nano Banana Pro] Aspect ratio: {aspect_ratio} -> {imagen_ratio}")

    try:
        response = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=180  # 3 минуты для мультимодальной генерации
        )

        print(f"[Nano Banana Pro] Response status: {response.status_code}")

        if response.status_code != 200:
            error_text = response.text
            print(f"[Nano Banana Pro] Error: {error_text}")
            raise Exception(f"Nano Banana Pro API error: {response.status_code} - {error_text}")

        data = response.json()

        # Извлекаем изображения из ответа
        images = []
        candidates = data.get("candidates", [])

        for candidate in candidates:
            content = candidate.get("content", {})
            parts = content.get("parts", [])

            for part in parts:
                # Изображение может быть в inline_data
                if "inline_data" in part:
                    image_b64 = part["inline_data"].get("data")
                    if image_b64:
                        image_bytes = base64.b64decode(image_b64)
                        images.append(BytesIO(image_bytes))

        if not images:
            print(f"[Nano Banana Pro] No images in response: {data}")
            raise Exception("No images generated")

        print(f"[Nano Banana Pro] Generated {len(images)} image(s)")
        return images

    except requests.exceptions.Timeout:
        print("[Nano Banana Pro] Request timeout")
        raise Exception("Nano Banana Pro API request timeout (180s)")
    except requests.exceptions.RequestException as e:
        print(f"[Nano Banana Pro] Request error: {e}")
        raise Exception(f"Nano Banana Pro API request failed: {e}")


# Тест функции
if __name__ == "__main__":
    try:
        # Тест без референса
        images = generate_with_nano_banana_pro("A cute cat sitting on a couch", aspect_ratio="1:1", num_images=1)
        print(f"Success! Generated {len(images)} image(s)")

        if images:
            with open("test_nano_banana_pro.png", "wb") as f:
                f.write(images[0].getvalue())
            print("Saved test_nano_banana_pro.png")
    except Exception as e:
        print(f"Error: {e}")
