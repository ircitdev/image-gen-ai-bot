"""
Модуль для генерации изображений через OpenAI
Поддерживаемые модели:
- GPT Image 1.5 (gpt-image-1.5) - Latest, fastest, cheapest
- GPT Image 1 (gpt-image-1) - Previous generation
- GPT Image 1 Mini (gpt-image-1-mini) - Lightweight version
- DALL-E 3 (dall-e-3) - Deprecated (until May 12, 2026)
- DALL-E 2 (dall-e-2) - Deprecated (until May 12, 2026)
"""
import requests
import io
from openai import OpenAI
from settings import OPENAI_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY)

def generate_with_dalle(prompt: str, model: str = "gpt-image-1.5", size: str = "1024x1024", quality: str = "standard"):
    """
    Генерирует изображение через OpenAI Image API

    Args:
        prompt: Текстовый промпт на английском
        model: Модель для генерации
            - gpt-image-1.5: Latest, 4x faster, 20% cheaper
            - gpt-image-1: Previous generation GPT Image
            - gpt-image-1-mini: Lightweight version
            - dall-e-3: Deprecated (until May 12, 2026)
            - dall-e-2: Deprecated (until May 12, 2026)
        size: Размер изображения
            - GPT Image 1.5/1: 1024x1024, 1024x1792 (portrait), 1792x1024 (landscape)
            - DALL-E 3: 1024x1024, 1024x1792 (portrait), 1792x1024 (landscape)
            - DALL-E 2: 256x256, 512x512, 1024x1024
        quality: Качество (standard или hd) - для DALL-E 3 и GPT Image

    Returns:
        BytesIO объект с изображением или строка с ошибкой
    """
    try:
        print(f"[INFO] Generating image with DALL-E...")
        print(f"[INFO] Model: {model}")
        print(f"[INFO] Size: {size}")
        print(f"[INFO] Quality: {quality}")
        print(f"[INFO] Prompt: {prompt[:100]}...")

        # Параметры для DALL-E 3
        params = {
            "model": model,
            "prompt": prompt,
            "n": 1,
            "size": size
        }

        # Качество для DALL-E 3 и GPT Image моделей
        if model in ["dall-e-3", "gpt-image-1.5", "gpt-image-1", "gpt-image-1-mini"]:
            params["quality"] = quality

        # Генерируем изображение
        response = client.images.generate(**params)

        # Получаем URL изображения
        image_url = response.data[0].url
        print(f"[OK] Image generated, URL: {image_url}")

        # Скачиваем изображение
        print(f"[INFO] Downloading image from URL...")
        img_response = requests.get(image_url, timeout=30)

        if img_response.status_code != 200:
            print(f"[ERROR] Failed to download image: {img_response.status_code}")
            return f"Ошибка загрузки изображения: {img_response.status_code}"

        image_bytes = img_response.content
        print(f"[OK] Image downloaded successfully! Size: {len(image_bytes)} bytes")

        # Возвращаем BytesIO объект
        return io.BytesIO(image_bytes)

    except Exception as e:
        print(f"[ERROR] DALL-E generation failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return f"Ошибка генерации: {str(e)}"


def get_dalle_sizes(model: str):
    """
    Возвращает доступные размеры для выбранной модели OpenAI

    Args:
        model: gpt-image-1.5, gpt-image-1, gpt-image-1-mini, dall-e-2 или dall-e-3

    Returns:
        Список кортежей (display_name, size_value)
    """
    # GPT Image и DALL-E 3 поддерживают одинаковые размеры
    if model in ["gpt-image-1.5", "gpt-image-1", "gpt-image-1-mini", "dall-e-3"]:
        return [
            ("Квадрат (1024x1024)", "1024x1024"),
            ("Портрет (1024x1792)", "1024x1792"),
            ("Пейзаж (1792x1024)", "1792x1024")
        ]
    else:  # dall-e-2
        return [
            ("Маленький (256x256)", "256x256"),
            ("Средний (512x512)", "512x512"),
            ("Большой (1024x1024)", "1024x1024")
        ]
