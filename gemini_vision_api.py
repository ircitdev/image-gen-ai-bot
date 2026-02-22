"""
Google Gemini Vision API для анализа изображений
Использует Gemini для создания промптов из изображений
"""

import requests
import base64
from io import BytesIO
from settings import GOOGLE_AI_API_KEY

# Gemini Vision endpoint (используем gemini-2.5-flash для vision)
GEMINI_VISION_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"

# Промпт для анализа изображения
PROMPT_EXTRACTION_TEMPLATE = """Проанализируй это изображение и создай детальный промпт для AI-генератора изображений, который мог бы создать похожее изображение.

Включи в промпт:
→ **Основной объект/субъект** (что изображено)
→ **Стиль изображения** (фотореализм, арт, цифровая живопись, 3D-рендер и т.д.)
→ **Композиция и ракурс** (крупный план, широкий угол, с высоты птичьего полета)
→ **Освещение** (естественное, студийное, драматическое, мягкое)
→ **Цветовая палитра** (теплые/холодные тона, доминирующие цвета)
→ **Настроение/атмосфера** (весёлое, драматичное, спокойное, энергичное)
→ **Технические детали** (разрешение, качество, детализация)
→ **Художественные референсы** (если применимо: стиль художника, эпоха, движение)

Затем УЛУЧШИ этот промпт на 30%, добавив:
- Более точные технические термины
- Специфические художественные детали
- Профессиональную терминологию фотографии/искусства

Верни ТОЛЬКО финальный улучшенный промпт на английском языке, без объяснений и комментариев.
Промпт должен быть готов для копирования в AI-генератор изображений."""


def analyze_image_for_prompt(image_data: BytesIO) -> str:
    """
    Анализирует изображение и создаёт промпт для генерации похожего

    Args:
        image_data: BytesIO объект с изображением

    Returns:
        str: Сгенерированный промпт или сообщение об ошибке
    """
    if not GOOGLE_AI_API_KEY:
        raise ValueError("GOOGLE_AI_API_KEY not configured")

    # URL с API ключом
    url = f"{GEMINI_VISION_URL}?key={GOOGLE_AI_API_KEY}"

    headers = {
        "Content-Type": "application/json"
    }

    # Кодируем изображение в base64
    image_data.seek(0)
    img_bytes = image_data.read()
    img_base64 = base64.b64encode(img_bytes).decode('utf-8')

    # Формируем payload для Gemini
    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "inlineData": {
                            "mimeType": "image/jpeg",
                            "data": img_base64
                        }
                    },
                    {
                        "text": PROMPT_EXTRACTION_TEMPLATE
                    }
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.7,
            "topP": 0.95,
            "topK": 40,
            "maxOutputTokens": 1024
        }
    }

    print(f"[Gemini Vision] Analyzing image for prompt extraction...")

    try:
        response = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=60
        )

        print(f"[Gemini Vision] Response status: {response.status_code}")

        if response.status_code != 200:
            error_text = response.text
            print(f"[Gemini Vision] Error: {error_text}")
            raise Exception(f"Gemini Vision API error: {response.status_code} - {error_text}")

        data = response.json()

        # Извлекаем текст из ответа
        candidates = data.get("candidates", [])
        if not candidates:
            print(f"[Gemini Vision] No candidates in response: {data}")
            raise Exception("No response from Gemini Vision")

        content = candidates[0].get("content", {})
        parts = content.get("parts", [])

        if not parts:
            print(f"[Gemini Vision] No parts in response: {data}")
            raise Exception("Empty response from Gemini Vision")

        # Получаем текст промпта
        prompt_text = parts[0].get("text", "").strip()

        print(f"[Gemini Vision] Generated prompt length: {len(prompt_text)} chars")
        return prompt_text

    except requests.exceptions.Timeout:
        print("[Gemini Vision] Request timeout")
        raise Exception("Gemini Vision API request timeout (60s)")
    except requests.exceptions.RequestException as e:
        print(f"[Gemini Vision] Request error: {e}")
        raise Exception(f"Gemini Vision API request failed: {e}")


# Тест функции
if __name__ == "__main__":
    try:
        # Тестируем с локальным изображением
        with open("test_imagen4_output.png", "rb") as f:
            image_data = BytesIO(f.read())

        prompt = analyze_image_for_prompt(image_data)
        print(f"\n{'='*60}")
        print("Generated Prompt:")
        print(f"{'='*60}")
        print(prompt)
        print(f"{'='*60}\n")

    except Exception as e:
        print(f"Error: {e}")
