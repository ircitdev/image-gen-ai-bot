"""
Модуль для дополнительных AI функций:
- Upscale (увеличение разрешения)
- Remove Background (удаление фона)
- Variations (создание вариаций изображения)
- Inpainting (редактирование частей изображения)
- Face Restore (улучшение лиц на фото)
"""
import requests
from io import BytesIO
from settings import STABILITY_API_KEY
from openai_helper import translate_to_english


def upscale_image(image_input, scale_factor=2):
    """
    Увеличивает разрешение изображения через Stability.ai

    Args:
        image_input: BytesIO объект или путь к файлу
        scale_factor: множитель масштабирования (2 или 4)

    Returns:
        BytesIO с upscaled изображением или строку с ошибкой
    """
    try:
        # Подготовка файла
        if isinstance(image_input, str):
            with open(image_input, 'rb') as f:
                image_bytes = f.read()
        else:
            image_input.seek(0)
            image_bytes = image_input.read()

        # Stability.ai upscale endpoint
        api_url = "https://api.stability.ai/v2beta/stable-image/upscale/conservative"

        headers = {
            "authorization": f"Bearer {STABILITY_API_KEY}",
            "accept": "image/*"
        }

        # Multipart form data
        files = {
            "image": ("image.png", image_bytes, "image/png")
        }

        data = {
            "output_format": "png"
        }

        print(f"[INFO] Upscaling image with {scale_factor}x...")

        response = requests.post(api_url, headers=headers, files=files, data=data)

        if response.status_code == 200:
            result = BytesIO(response.content)
            result.seek(0)
            print(f"[INFO] Upscale successful")
            return result
        else:
            error_msg = f"Upscale error: {response.status_code}"
            print(f"[ERROR] {error_msg}")
            print(f"[ERROR] Response: {response.text}")
            return f"❌ Ошибка upscale: {response.status_code}"

    except Exception as e:
        error_msg = f"Upscale exception: {str(e)}"
        print(f"[ERROR] {error_msg}")
        return f"❌ Ошибка: {str(e)}"


def remove_background(image_input):
    """
    Удаляет фон с изображения

    Args:
        image_input: BytesIO объект или путь к файлу

    Returns:
        BytesIO с изображением без фона или строку с ошибкой
    """
    try:
        # Подготовка файла
        if isinstance(image_input, str):
            with open(image_input, 'rb') as f:
                image_bytes = f.read()
        else:
            image_input.seek(0)
            image_bytes = image_input.read()

        # Stability.ai remove background endpoint
        api_url = "https://api.stability.ai/v2beta/stable-image/edit/remove-background"

        headers = {
            "authorization": f"Bearer {STABILITY_API_KEY}",
            "accept": "image/*"
        }

        files = {
            "image": ("image.png", image_bytes, "image/png")
        }

        data = {
            "output_format": "png"
        }

        print("[INFO] Removing background...")

        response = requests.post(api_url, headers=headers, files=files, data=data)

        if response.status_code == 200:
            result = BytesIO(response.content)
            result.seek(0)
            print("[INFO] Background removal successful")
            return result
        else:
            error_msg = f"Remove background error: {response.status_code}"
            print(f"[ERROR] {error_msg}")
            print(f"[ERROR] Response: {response.text}")
            return f"❌ Ошибка удаления фона: {response.status_code}"

    except Exception as e:
        error_msg = f"Remove background exception: {str(e)}"
        print(f"[ERROR] {error_msg}")
        return f"❌ Ошибка: {str(e)}"


def create_variations(image_input, prompt="", num_variations=1):
    """
    Создает вариации изображения

    Args:
        image_input: BytesIO объект или путь к файлу
        prompt: текстовое описание (опционально)
        num_variations: количество вариаций

    Returns:
        список BytesIO объектов или строка с ошибкой
    """
    try:
        # Подготовка файла
        if isinstance(image_input, str):
            with open(image_input, 'rb') as f:
                image_bytes = f.read()
        else:
            image_input.seek(0)
            image_bytes = image_input.read()

        # Используем image-to-image для создания вариаций
        api_url = "https://api.stability.ai/v2beta/stable-image/generate/sd3"

        headers = {
            "authorization": f"Bearer {STABILITY_API_KEY}",
            "accept": "image/*"
        }

        files = {
            "image": ("image.png", image_bytes, "image/png")
        }

        # Переводим промпт на английский, если он есть
        english_prompt = prompt if prompt else "variation of this image, slightly different"
        if prompt:
            print(f"[INFO] Translating prompt: {prompt}")
            english_prompt = translate_to_english(prompt)
            print(f"[OK] Translated prompt: {english_prompt}")

        # Используем низкий strength для создания вариаций
        data = {
            "prompt": english_prompt,
            "mode": "image-to-image",
            "strength": 0.5,  # 0.5 для умеренных изменений
            "output_format": "png",
            "model": "sd3.5-large"
        }

        print(f"[INFO] Creating {num_variations} variation(s)...")

        response = requests.post(api_url, headers=headers, files=files, data=data)

        if response.status_code == 200:
            result = BytesIO(response.content)
            result.seek(0)
            print("[INFO] Variation created successfully")
            return [result]
        else:
            error_msg = f"Variations error: {response.status_code}"
            print(f"[ERROR] {error_msg}")
            print(f"[ERROR] Response: {response.text}")
            return f"❌ Ошибка создания вариаций: {response.status_code}"

    except Exception as e:
        error_msg = f"Variations exception: {str(e)}"
        print(f"[ERROR] {error_msg}")
        return f"❌ Ошибка: {str(e)}"


def inpaint_image(image_input, mask_input, prompt=""):
    """
    Редактирует части изображения используя маску

    Args:
        image_input: BytesIO объект или путь к исходному изображению
        mask_input: BytesIO объект или путь к маске (белые области = редактировать)
        prompt: описание того, что должно быть на месте маски

    Returns:
        BytesIO с отредактированным изображением или строку с ошибкой
    """
    try:
        # Подготовка исходного изображения
        if isinstance(image_input, str):
            with open(image_input, 'rb') as f:
                image_bytes = f.read()
        else:
            image_input.seek(0)
            image_bytes = image_input.read()

        # Подготовка маски
        if isinstance(mask_input, str):
            with open(mask_input, 'rb') as f:
                mask_bytes = f.read()
        else:
            mask_input.seek(0)
            mask_bytes = mask_input.read()

        # Stability.ai inpaint endpoint
        api_url = "https://api.stability.ai/v2beta/stable-image/edit/inpaint"

        headers = {
            "authorization": f"Bearer {STABILITY_API_KEY}",
            "accept": "image/*"
        }

        files = {
            "image": ("image.png", image_bytes, "image/png"),
            "mask": ("mask.png", mask_bytes, "image/png")
        }

        # Переводим промпт на английский, если он есть
        english_prompt = prompt if prompt else "improve and enhance the masked area"
        if prompt:
            print(f"[INFO] Translating inpaint prompt: {prompt}")
            english_prompt = translate_to_english(prompt)
            print(f"[OK] Translated prompt: {english_prompt}")

        data = {
            "prompt": english_prompt,
            "output_format": "png"
        }

        print("[INFO] Inpainting image...")

        response = requests.post(api_url, headers=headers, files=files, data=data)

        if response.status_code == 200:
            result = BytesIO(response.content)
            result.seek(0)
            print("[INFO] Inpainting successful")
            return result
        else:
            error_msg = f"Inpaint error: {response.status_code}"
            print(f"[ERROR] {error_msg}")
            print(f"[ERROR] Response: {response.text}")
            return f"❌ Ошибка inpainting: {response.status_code}"

    except Exception as e:
        error_msg = f"Inpaint exception: {str(e)}"
        print(f"[ERROR] {error_msg}")
        return f"❌ Ошибка: {str(e)}"


def restore_face(image_input):
    """
    Улучшает качество лиц на фотографиях

    Args:
        image_input: BytesIO объект или путь к файлу

    Returns:
        BytesIO с улучшенным изображением или строку с ошибкой
    """
    try:
        # Подготовка файла
        if isinstance(image_input, str):
            with open(image_input, 'rb') as f:
                image_bytes = f.read()
        else:
            image_input.seek(0)
            image_bytes = image_input.read()

        # Используем creative upscale для улучшения деталей лица
        api_url = "https://api.stability.ai/v2beta/stable-image/upscale/creative"

        headers = {
            "authorization": f"Bearer {STABILITY_API_KEY}",
            "accept": "image/*"
        }

        files = {
            "image": ("image.png", image_bytes, "image/png")
        }

        data = {
            "prompt": "enhance and restore facial details, improve skin quality, professional portrait photography",
            "output_format": "png",
            "creativity": 0.3  # Низкая креативность для сохранения оригинала
        }

        print("[INFO] Restoring faces...")

        response = requests.post(api_url, headers=headers, files=files, data=data)

        if response.status_code == 200:
            result = BytesIO(response.content)
            result.seek(0)
            print("[INFO] Face restoration successful")
            return result
        else:
            error_msg = f"Face restore error: {response.status_code}"
            print(f"[ERROR] {error_msg}")
            print(f"[ERROR] Response: {response.text}")
            return f"❌ Ошибка восстановления лица: {response.status_code}"

    except Exception as e:
        error_msg = f"Face restore exception: {str(e)}"
        print(f"[ERROR] {error_msg}")
        return f"❌ Ошибка: {str(e)}"


def outpaint_image(image_input, prompt="", left=0, right=0, up=0, down=0):
    """
    Расширяет изображение за его границы

    Args:
        image_input: BytesIO объект или путь к файлу
        prompt: описание для генерации расширенных областей
        left, right, up, down: количество пикселей для расширения в каждом направлении (0-2000)

    Returns:
        BytesIO с расширенным изображением или строку с ошибкой
    """
    try:
        # Подготовка файла
        if isinstance(image_input, str):
            with open(image_input, 'rb') as f:
                image_bytes = f.read()
        else:
            image_input.seek(0)
            image_bytes = image_input.read()

        # Переводим промпт на английский, если он есть
        english_prompt = prompt if prompt else "extend the image naturally"
        if prompt:
            print(f"[INFO] Translating outpaint prompt: {prompt}")
            english_prompt = translate_to_english(prompt)
            print(f"[OK] Translated prompt: {english_prompt}")

        api_url = "https://api.stability.ai/v2beta/stable-image/edit/outpaint"

        headers = {
            "authorization": f"Bearer {STABILITY_API_KEY}",
            "accept": "image/*"
        }

        files = {
            "image": ("image.png", image_bytes, "image/png")
        }

        data = {
            "prompt": english_prompt,
            "left": left,
            "right": right,
            "up": up,
            "down": down,
            "output_format": "png"
        }

        print(f"[INFO] Outpainting image (L:{left}, R:{right}, U:{up}, D:{down})...")

        response = requests.post(api_url, headers=headers, files=files, data=data)

        if response.status_code == 200:
            result = BytesIO(response.content)
            result.seek(0)
            print("[INFO] Outpaint successful")
            return result
        else:
            error_msg = f"Outpaint error: {response.status_code}"
            print(f"[ERROR] {error_msg}")
            print(f"[ERROR] Response: {response.text}")
            return f"❌ Ошибка outpaint: {response.status_code}"

    except Exception as e:
        error_msg = f"Outpaint exception: {str(e)}"
        print(f"[ERROR] {error_msg}")
        return f"❌ Ошибка: {str(e)}"


def search_and_recolor(image_input, search_prompt, recolor_prompt):
    """
    Находит объект и перекрашивает его

    Args:
        image_input: BytesIO объект или путь к файлу
        search_prompt: описание объекта для поиска
        recolor_prompt: описание нового цвета/стиля

    Returns:
        BytesIO с перекрашенным изображением или строку с ошибкой
    """
    try:
        # Подготовка файла
        if isinstance(image_input, str):
            with open(image_input, 'rb') as f:
                image_bytes = f.read()
        else:
            image_input.seek(0)
            image_bytes = image_input.read()

        # Переводим промпты на английский
        print(f"[INFO] Translating search prompt: {search_prompt}")
        english_search = translate_to_english(search_prompt)
        print(f"[OK] Translated search: {english_search}")

        print(f"[INFO] Translating recolor prompt: {recolor_prompt}")
        english_recolor = translate_to_english(recolor_prompt)
        print(f"[OK] Translated recolor: {english_recolor}")

        api_url = "https://api.stability.ai/v2beta/stable-image/edit/search-and-recolor"

        headers = {
            "authorization": f"Bearer {STABILITY_API_KEY}",
            "accept": "image/*"
        }

        files = {
            "image": ("image.png", image_bytes, "image/png")
        }

        data = {
            "prompt": english_recolor,
            "select_prompt": english_search,
            "output_format": "png"
        }

        print(f"[INFO] Search and recolor: '{english_search}' -> '{english_recolor}'...")

        response = requests.post(api_url, headers=headers, files=files, data=data)

        if response.status_code == 200:
            result = BytesIO(response.content)
            result.seek(0)
            print("[INFO] Search and recolor successful")
            return result
        else:
            error_msg = f"Search and recolor error: {response.status_code}"
            print(f"[ERROR] {error_msg}")
            print(f"[ERROR] Response: {response.text}")
            return f"❌ Ошибка перекраски: {response.status_code}"

    except Exception as e:
        error_msg = f"Search and recolor exception: {str(e)}"
        print(f"[ERROR] {error_msg}")
        return f"❌ Ошибка: {str(e)}"


def search_and_replace(image_input, search_prompt, replace_prompt):
    """
    Находит объект и заменяет его на другой

    Args:
        image_input: BytesIO объект или путь к файлу
        search_prompt: описание объекта для поиска
        replace_prompt: описание объекта для замены

    Returns:
        BytesIO с измененным изображением или строку с ошибкой
    """
    try:
        # Подготовка файла
        if isinstance(image_input, str):
            with open(image_input, 'rb') as f:
                image_bytes = f.read()
        else:
            image_input.seek(0)
            image_bytes = image_input.read()

        # Переводим промпты на английский
        print(f"[INFO] Translating search prompt: {search_prompt}")
        english_search = translate_to_english(search_prompt)
        print(f"[OK] Translated search: {english_search}")

        print(f"[INFO] Translating replace prompt: {replace_prompt}")
        english_replace = translate_to_english(replace_prompt)
        print(f"[OK] Translated replace: {english_replace}")

        api_url = "https://api.stability.ai/v2beta/stable-image/edit/search-and-replace"

        headers = {
            "authorization": f"Bearer {STABILITY_API_KEY}",
            "accept": "image/*"
        }

        files = {
            "image": ("image.png", image_bytes, "image/png")
        }

        data = {
            "prompt": english_replace,
            "search_prompt": english_search,
            "output_format": "png"
        }

        print(f"[INFO] Search and replace: '{english_search}' -> '{english_replace}'...")

        response = requests.post(api_url, headers=headers, files=files, data=data)

        if response.status_code == 200:
            result = BytesIO(response.content)
            result.seek(0)
            print("[INFO] Search and replace successful")
            return result
        else:
            error_msg = f"Search and replace error: {response.status_code}"
            print(f"[ERROR] {error_msg}")
            print(f"[ERROR] Response: {response.text}")
            return f"❌ Ошибка замены: {response.status_code}"

    except Exception as e:
        error_msg = f"Search and replace exception: {str(e)}"
        print(f"[ERROR] {error_msg}")
        return f"❌ Ошибка: {str(e)}"


def erase_object(image_input, search_prompt):
    """
    Находит и удаляет объект с изображения

    Args:
        image_input: BytesIO объект или путь к файлу
        search_prompt: описание объекта для удаления

    Returns:
        BytesIO с изображением без объекта или строку с ошибкой
    """
    try:
        # Подготовка файла
        if isinstance(image_input, str):
            with open(image_input, 'rb') as f:
                image_bytes = f.read()
        else:
            image_input.seek(0)
            image_bytes = image_input.read()

        # Переводим промпт на английский
        print(f"[INFO] Translating erase prompt: {search_prompt}")
        english_search = translate_to_english(search_prompt)
        print(f"[OK] Translated prompt: {english_search}")

        api_url = "https://api.stability.ai/v2beta/stable-image/edit/erase"

        headers = {
            "authorization": f"Bearer {STABILITY_API_KEY}",
            "accept": "image/*"
        }

        files = {
            "image": ("image.png", image_bytes, "image/png")
        }

        data = {
            "search_prompt": english_search,
            "output_format": "png"
        }

        print(f"[INFO] Erasing object: '{english_search}'...")

        response = requests.post(api_url, headers=headers, files=files, data=data)

        if response.status_code == 200:
            result = BytesIO(response.content)
            result.seek(0)
            print("[INFO] Erase successful")
            return result
        else:
            error_msg = f"Erase error: {response.status_code}"
            print(f"[ERROR] {error_msg}")
            print(f"[ERROR] Response: {response.text}")
            return f"❌ Ошибка удаления: {response.status_code}"

    except Exception as e:
        error_msg = f"Erase exception: {str(e)}"
        print(f"[ERROR] {error_msg}")
        return f"❌ Ошибка: {str(e)}"
