"""
Модуль для Style Guide через Stability.ai API
Генерирует новое изображение на основе стиля референсного изображения
"""
import requests
import io
from settings import STABILITY_API_KEY


def generate_with_style_guide(image_path: str, prompt: str,
                               negative_prompt: str = "",
                               aspect_ratio: str = "1:1",
                               fidelity: float = 0.5,
                               output_format: str = "png"):
    """
    Генерирует новое изображение используя стиль референсного изображения

    Args:
        image_path: Путь к изображению-стилю
        prompt: Текстовый промпт (обязательно!)
        negative_prompt: Негативный промпт (опционально)
        aspect_ratio: Соотношение сторон (1:1, 21:9, 16:9, etc.)
        fidelity: Точность следования стилю (0.1-1.0)
        output_format: Формат вывода (png, jpeg, webp)

    Returns:
        BytesIO объект с результатом или строка с ошибкой
    """
    try:
        print(f"[INFO] Starting style guide generation...")
        print(f"[INFO] Style image: {image_path}")
        print(f"[INFO] Prompt: {prompt}")
        print(f"[INFO] Aspect ratio: {aspect_ratio}")
        print(f"[INFO] Fidelity: {fidelity}")

        api_url = "https://api.stability.ai/v2beta/stable-image/control/style"

        headers = {
            "Authorization": f"Bearer {STABILITY_API_KEY}",
            "Accept": "image/*"
        }

        # Параметры запроса
        data = {
            "prompt": prompt,
            "aspect_ratio": aspect_ratio,
            "fidelity": fidelity,
            "output_format": output_format,
            "seed": 0
        }

        # Добавляем negative prompt если указан
        if negative_prompt:
            data["negative_prompt"] = negative_prompt

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
            print(f"[ERROR] Style Guide API error: {response.status_code}")
            print(f"[ERROR] Response: {error_msg}")
            return f"Ошибка генерации: {response.status_code}. {error_msg}"

        # Проверяем результат
        finish_reason = response.headers.get("finish-reason")
        if finish_reason == 'CONTENT_FILTERED':
            print(f"[ERROR] Content filtered by NSFW classifier")
            return "Изображение отклонено фильтром NSFW"

        image_bytes = response.content
        print(f"[OK] Style guide generation complete! Size: {len(image_bytes)} bytes")

        return io.BytesIO(image_bytes)

    except Exception as e:
        print(f"[ERROR] Exception in style guide: {str(e)}")
        import traceback
        traceback.print_exc()
        return f"Ошибка: {str(e)}"
