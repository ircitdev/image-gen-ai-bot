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

        # Используем низкий strength для создания вариаций
        data = {
            "prompt": prompt if prompt else "variation of this image, slightly different",
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

        data = {
            "prompt": prompt if prompt else "improve and enhance the masked area",
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
