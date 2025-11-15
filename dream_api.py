import requests
import io
import base64
from settings import STABILITY_API_KEY

def generate_dream(prompt: str, images=None, format_ratio="1:1", model="sd3.5-large", style=None, negative_prompt=""):
    """
    Генерирует изображение через Stability.ai (Stable Diffusion 3.5)

    Args:
        prompt: Текст промпта на английском
        images: Референсные изображения (пока не используется)
        format_ratio: Соотношение сторон (1:1, 21:9, 16:9, 3:2, 5:4, 4:5, 2:3, 9:16, 9:21)
        model: Модель для генерации (sd3.5-large, sd3.5-large-turbo, sd3.5-medium, sd3.5-flash)
        style: Стиль изображения (опционально)
        negative_prompt: Negative prompt (что НЕ должно быть на изображении)
    """
    try:
        print(f"[INFO] Generating image with Stability.ai...")
        print(f"[INFO] Model: {model}")
        print(f"[INFO] Format: {format_ratio}")
        print(f"[INFO] Style: {style}")
        print(f"[INFO] Prompt: {prompt[:100]}...")
        if negative_prompt:
            print(f"[INFO] Negative Prompt: {negative_prompt[:100]}...")

        # API endpoint для SD 3.5
        model_map = {
            "sd3.5-large": "sd3.5-large",
            "sd3.5-large-turbo": "sd3.5-large-turbo",
            "sd3.5-medium": "sd3.5-medium",
            "sd3.5-flash": "sd3.5-flash"
        }

        engine_id = model_map.get(model, "sd3.5-large")
        api_url = f"https://api.stability.ai/v2beta/stable-image/generate/sd3"

        headers = {
            "Authorization": f"Bearer {STABILITY_API_KEY}",
            "Accept": "image/*"
        }

        # Формируем данные для multipart/form-data
        data = {
            "prompt": prompt,
            "model": engine_id,
            "aspect_ratio": format_ratio,
            "output_format": "png"
        }

        # Добавляем стиль если он указан и не "none"
        if style and style != "none":
            data["style_preset"] = style

        # Добавляем negative prompt если указан
        if negative_prompt:
            data["negative_prompt"] = negative_prompt

        # Отправляем запрос
        response = requests.post(
            api_url,
            headers=headers,
            files={"none": ''},  # Пустой файл для корректной работы multipart
            data=data,
            timeout=60
        )

        if response.status_code != 200:
            error_msg = response.text
            print(f"[ERROR] Stability.ai API error: {response.status_code}")
            print(f"[ERROR] Response: {error_msg}")
            return [f"Ошибка генерации: {response.status_code}. Проверьте баланс API или параметры."]

        # В новом API возвращается напрямую изображение
        image_bytes = response.content

        print(f"[OK] Image generated successfully! Size: {len(image_bytes)} bytes")

        # Возвращаем BytesIO объект для отправки в Telegram
        return [io.BytesIO(image_bytes)]

    except requests.exceptions.Timeout:
        print(f"[ERROR] Request timeout")
        return ["Превышено время ожидания. Попробуйте еще раз."]
    except Exception as e:
        print(f"[ERROR] Exception in generate_dream: {str(e)}")
        import traceback
        traceback.print_exc()
        return [f"Ошибка: {str(e)}"]
