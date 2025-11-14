"""
Модуль для Style Transfer через Stability.ai API
"""
import requests
import io
from settings import STABILITY_API_KEY


def apply_style_transfer(init_image_path: str, style_image_path: str,
                         prompt: str = "", negative_prompt: str = "",
                         style_strength: float = 1.0,
                         composition_fidelity: float = 0.9,
                         change_strength: float = 0.9,
                         output_format: str = "png"):
    """
    Применяет стиль одного изображения к другому через Stability.ai

    Args:
        init_image_path: Путь к исходному изображению
        style_image_path: Путь к изображению стиля
        prompt: Текстовый промпт (опционально)
        negative_prompt: Негативный промпт (опционально)
        style_strength: Сила применения стиля (0.1-1.0)
        composition_fidelity: Точность композиции (0.1-1.0)
        change_strength: Сила изменений (0.1-1.0)
        output_format: Формат вывода (png, jpeg, webp)

    Returns:
        BytesIO объект с результатом или строка с ошибкой
    """
    try:
        print(f"[INFO] Starting style transfer...")
        print(f"[INFO] Init image: {init_image_path}")
        print(f"[INFO] Style image: {style_image_path}")
        print(f"[INFO] Style strength: {style_strength}")
        print(f"[INFO] Composition fidelity: {composition_fidelity}")
        print(f"[INFO] Change strength: {change_strength}")

        api_url = "https://api.stability.ai/v2beta/stable-image/control/style"

        headers = {
            "Authorization": f"Bearer {STABILITY_API_KEY}",
            "Accept": "image/*"
        }

        # Параметры запроса
        # Prompt обязателен для Style Transfer API
        data = {
            "prompt": prompt if prompt else "high quality image",
            "output_format": output_format,
            "style_strength": style_strength,
            "composition_fidelity": composition_fidelity,
            "change_strength": change_strength,
            "seed": 0
        }

        # Добавляем negative prompt если указан
        if negative_prompt:
            data["negative_prompt"] = negative_prompt

        # Открываем файлы
        files = {
            "image": open(init_image_path, 'rb'),
            "style_image": open(style_image_path, 'rb')
        }

        # Отправляем запрос
        response = requests.post(
            api_url,
            headers=headers,
            files=files,
            data=data,
            timeout=60
        )

        # Закрываем файлы
        for f in files.values():
            f.close()

        if response.status_code != 200:
            error_msg = response.text
            print(f"[ERROR] Style transfer API error: {response.status_code}")
            print(f"[ERROR] Response: {error_msg}")
            return f"Ошибка переноса стиля: {response.status_code}. {error_msg}"

        # Проверяем результат
        finish_reason = response.headers.get("finish-reason")
        if finish_reason == 'CONTENT_FILTERED':
            print(f"[ERROR] Content filtered by NSFW classifier")
            return "Изображение отклонено фильтром NSFW"

        image_bytes = response.content
        print(f"[OK] Style transfer complete! Size: {len(image_bytes)} bytes")

        return io.BytesIO(image_bytes)

    except Exception as e:
        print(f"[ERROR] Exception in style transfer: {str(e)}")
        import traceback
        traceback.print_exc()
        return f"Ошибка: {str(e)}"
