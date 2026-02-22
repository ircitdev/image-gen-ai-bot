"""
Google AI Studio Imagen 3 Customization API Integration
Model: imagen-3.0-capability-001
Supports: Subject conditioning (person, animal, product) with reference images
"""

import requests
import base64
from io import BytesIO
from settings import GOOGLE_AI_API_KEY

# ВРЕМЕННО ОТКЛЮЧЕНО: Imagen 3 Custom API не доступен
# Google изменил API, модель imagen-3.0-capability-001 больше не поддерживается
# Нужно найти актуальную модель или использовать другой endpoint
IMAGEN3_CUSTOM_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/imagen-3.0-generate-001:predict"

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


def generate_with_imagen3_custom(
    prompt: str,
    reference_images: list,
    aspect_ratio: str = "1:1",
    num_images: int = 1,
    subject_type: str = "person"
) -> list:
    """
    Генерирует изображение через Google Imagen 3 Customization API с референсными изображениями

    Args:
        prompt: Текстовый промпт с маркерами [1], [2] и т.д. для референсов
                Например: "A photo of person [1] standing on a beach"
        reference_images: Список BytesIO объектов с референсными изображениями (1-4 шт)
        aspect_ratio: Соотношение сторон (1:1, 3:4, 4:3, 9:16, 16:9)
        num_images: Количество изображений (1-4)
        subject_type: Тип субъекта - "person", "animal", "product", "default"

    Returns:
        Список BytesIO объектов с сгенерированными изображениями
    """
    # ВРЕМЕННОЕ ОТКЛЮЧЕНИЕ
    raise Exception(
        "⚠️ Imagen 3 Custom временно недоступен\n\n"
        "Google изменил API, модель imagen-3.0-capability-001 больше не поддерживается.\n"
        "Пожалуйста, используйте другие движки:\n"
        "• 🍌 Nano Banana 4 (Imagen 4) - text-to-image\n"
        "• 🤖 DALL-E 3 - text-to-image\n"
        "• 🎨 Stable Diffusion 3.5 - text-to-image"
    )

    if not GOOGLE_AI_API_KEY:
        raise ValueError("GOOGLE_AI_API_KEY not configured")

    if not reference_images or len(reference_images) == 0:
        raise ValueError("At least one reference image is required")

    if len(reference_images) > 4:
        raise ValueError("Maximum 4 reference images allowed")

    # Преобразуем формат
    imagen_ratio = ASPECT_RATIO_MAP.get(aspect_ratio, "1:1")
    num_images = min(max(1, num_images), 4)

    # URL с API ключом
    url = f"{IMAGEN3_CUSTOM_API_URL}?key={GOOGLE_AI_API_KEY}"

    headers = {
        "Content-Type": "application/json"
    }

    # Подготавливаем референсные изображения
    reference_configs = []
    for idx, ref_img in enumerate(reference_images, start=1):
        # Конвертируем BytesIO в base64
        ref_img.seek(0)
        img_bytes = ref_img.read()
        img_base64 = base64.b64encode(img_bytes).decode('utf-8')

        reference_configs.append({
            "referenceId": idx,
            "referenceImage": {
                "bytesBase64Encoded": img_base64
            },
            "referenceType": subject_type
        })

    # Формат запроса для customization endpoint
    payload = {
        "instances": [
            {
                "prompt": prompt,
                "referenceImages": reference_configs
            }
        ],
        "parameters": {
            "sampleCount": num_images,
            "aspectRatio": imagen_ratio
        }
    }

    print(f"[Imagen 3 Custom] Generating with prompt: {prompt[:100]}...")
    print(f"[Imagen 3 Custom] Reference images: {len(reference_images)}")
    print(f"[Imagen 3 Custom] Subject type: {subject_type}")
    print(f"[Imagen 3 Custom] Aspect ratio: {aspect_ratio} -> {imagen_ratio}")

    try:
        response = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=180  # 3 минуты для customization
        )

        print(f"[Imagen 3 Custom] Response status: {response.status_code}")

        if response.status_code != 200:
            error_text = response.text
            print(f"[Imagen 3 Custom] Error: {error_text}")
            raise Exception(f"Imagen 3 Custom API error: {response.status_code} - {error_text}")

        data = response.json()

        # Извлекаем изображения
        images = []
        predictions = data.get("predictions", [])

        for prediction in predictions:
            image_b64 = prediction.get("bytesBase64Encoded")
            if image_b64:
                image_bytes = base64.b64decode(image_b64)
                images.append(BytesIO(image_bytes))

        print(f"[Imagen 3 Custom] Generated {len(images)} image(s)")
        return images

    except requests.exceptions.Timeout:
        print("[Imagen 3 Custom] Request timeout")
        raise Exception("Imagen 3 Custom API request timeout (180s)")
    except requests.exceptions.RequestException as e:
        print(f"[Imagen 3 Custom] Request error: {e}")
        raise Exception(f"Imagen 3 Custom API request failed: {e}")


# Тест функции
if __name__ == "__main__":
    print("Imagen 3 Customization API requires reference images")
    print("Use this module through the bot interface to upload reference photos")
