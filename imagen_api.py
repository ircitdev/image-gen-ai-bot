"""
Google AI Studio Imagen 4 API Integration
Supports: Imagen 4, Imagen 4 Ultra, Imagen 4 Fast
Uses Gemini API predict endpoint
"""

import requests
import base64
from io import BytesIO
from settings import GOOGLE_AI_API_KEY
from imagen_models import get_model_endpoint, get_model_emoji

# Legacy URL (для обратной совместимости)
IMAGEN_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/imagen-4.0-generate-001:predict"

# Маппинг форматов из нашего бота в форматы Imagen
ASPECT_RATIO_MAP = {
    "1:1": "1:1",
    "16:9": "16:9",
    "9:16": "9:16",
    "3:2": "3:4",   # Imagen не поддерживает 3:2, используем 3:4
    "2:3": "4:3",   # Imagen не поддерживает 2:3, используем 4:3
    "4:3": "4:3",
    "3:4": "3:4",
    "21:9": "16:9", # Imagen не поддерживает 21:9, используем 16:9
    "9:21": "9:16", # Imagen не поддерживает 9:21, используем 9:16
    "5:4": "4:3",   # Imagen не поддерживает 5:4, используем 4:3
    "4:5": "3:4"    # Imagen не поддерживает 4:5, используем 3:4
}


def generate_with_imagen(prompt: str, aspect_ratio: str = "1:1", num_images: int = 1, model: str = "imagen-4") -> list:
    """
    Генерирует изображение через Google Imagen 4 API

    Args:
        prompt: Текстовый промпт для генерации
        aspect_ratio: Соотношение сторон (1:1, 3:4, 4:3, 9:16, 16:9)
        num_images: Количество изображений (1-4)
        model: Модель Imagen ("imagen-4", "imagen-4-ultra", "imagen-4-fast")

    Returns:
        Список BytesIO объектов с изображениями
    """
    if not GOOGLE_AI_API_KEY:
        raise ValueError("GOOGLE_AI_API_KEY not configured")

    # Преобразуем формат если нужно
    imagen_ratio = ASPECT_RATIO_MAP.get(aspect_ratio, "1:1")

    # Ограничиваем количество изображений
    num_images = min(max(1, num_images), 4)

    # URL с API ключом как query параметр
    # Используем динамический endpoint в зависимости от модели
    endpoint = get_model_endpoint(model)
    url = f"{endpoint}?key={GOOGLE_AI_API_KEY}"
    emoji = get_model_emoji(model)

    headers = {
        "Content-Type": "application/json"
    }

    # Формат запроса для predict endpoint (Imagen 4)
    payload = {
        "instances": [
            {
                "prompt": prompt
            }
        ],
        "parameters": {
            "sampleCount": num_images,
            "aspectRatio": imagen_ratio
        }
    }

    print(f"[Imagen API] {emoji} Generating with model: {model}")
    print(f"[Imagen API] Prompt: {prompt[:100]}...")
    print(f"[Imagen API] Aspect ratio: {aspect_ratio} -> {imagen_ratio}")

    try:
        response = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=120  # 2 минуты таймаут
        )

        print(f"[Imagen API] Response status: {response.status_code}")

        if response.status_code != 200:
            error_text = response.text
            print(f"[Imagen API] Error: {error_text}")
            raise Exception(f"Imagen API error: {response.status_code} - {error_text}")

        data = response.json()

        # Извлекаем изображения из ответа (формат predict)
        images = []
        predictions = data.get("predictions", [])

        for prediction in predictions:
            # Изображение в base64
            image_b64 = prediction.get("bytesBase64Encoded")
            if image_b64:
                image_bytes = base64.b64decode(image_b64)
                images.append(BytesIO(image_bytes))

        print(f"[Imagen API] Generated {len(images)} image(s)")
        return images

    except requests.exceptions.Timeout:
        print("[Imagen API] Request timeout")
        raise Exception("Imagen API request timeout (120s)")
    except requests.exceptions.RequestException as e:
        print(f"[Imagen API] Request error: {e}")
        raise Exception(f"Imagen API request failed: {e}")


# Тест функции (запуск напрямую)
if __name__ == "__main__":
    try:
        images = generate_with_imagen("A cute cat sitting on a couch", "1:1", 1)
        print(f"Success! Generated {len(images)} image(s)")

        # Сохраняем первое изображение для проверки
        if images:
            with open("test_imagen.png", "wb") as f:
                f.write(images[0].getvalue())
            print("Saved test_imagen.png")
    except Exception as e:
        print(f"Error: {e}")
