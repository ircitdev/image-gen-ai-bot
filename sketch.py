"""
Модуль для Sketch Control через Stability.ai API
Генерирует изображение на основе наброска
"""
import requests
import io
from settings import STABILITY_API_KEY
from ai_tools import translate_to_english


def generate_from_sketch(image_path: str, prompt: str,
                         negative_prompt: str = "",
                         control_strength: float = 0.5,
                         output_format: str = "png"):
    """
    Генерирует изображение на основе наброска/скетча

    Args:
        image_path: Путь к изображению наброска
        prompt: Текстовый промпт (обязательно!)
        negative_prompt: Негативный промпт (опционально)
        control_strength: Сила следования наброску (0.1-1.0)
        output_format: Формат вывода (png, jpeg, webp)

    Returns:
        BytesIO объект с результатом или строка с ошибкой
    """
    try:
        print(f"[INFO] Starting sketch generation...")
        print(f"[INFO] Sketch image: {image_path}")
        print(f"[INFO] Prompt: {prompt}")
        print(f"[INFO] Control strength: {control_strength}")

        # Переводим промпт на английский
        print(f"[INFO] Translating prompt to English...")
        english_prompt = translate_to_english(prompt)
        print(f"[OK] Translated prompt: {english_prompt}")

        # Переводим negative prompt если указан
        english_negative = ""
        if negative_prompt:
            print(f"[INFO] Translating negative prompt to English...")
            english_negative = translate_to_english(negative_prompt)
            print(f"[OK] Translated negative prompt: {english_negative}")

        api_url = "https://api.stability.ai/v2beta/stable-image/control/sketch"

        headers = {
            "Authorization": f"Bearer {STABILITY_API_KEY}",
            "Accept": "image/*"
        }

        # Параметры запроса
        data = {
            "prompt": english_prompt,
            "control_strength": control_strength,
            "output_format": output_format,
            "seed": 0
        }

        # Добавляем negative prompt если указан
        if english_negative:
            data["negative_prompt"] = english_negative

        # Открываем файл
        files = {
            "image": open(image_path, 'rb')
        }

        # Отправляем запрос
        response = requests.post(
            api_url,
            headers=headers,
            files=files,
            data=data,
            timeout=60
        )

        # Закрываем файл
        files["image"].close()

        if response.status_code != 200:
            error_msg = response.text
            print(f"[ERROR] Sketch API error: {response.status_code}")
            print(f"[ERROR] Response: {error_msg}")
            return f"Ошибка генерации: {response.status_code}. {error_msg}"

        # Проверяем результат
        finish_reason = response.headers.get("finish-reason")
        if finish_reason == 'CONTENT_FILTERED':
            print(f"[ERROR] Content filtered by NSFW classifier")
            return "Изображение отклонено фильтром NSFW"

        image_bytes = response.content
        print(f"[OK] Sketch generation complete! Size: {len(image_bytes)} bytes")

        return io.BytesIO(image_bytes)

    except Exception as e:
        print(f"[ERROR] Exception in sketch generation: {str(e)}")
        import traceback
        traceback.print_exc()
        return f"Ошибка: {str(e)}"
