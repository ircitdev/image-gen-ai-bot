"""
Модуль для Style Transfer через Google Imagen (Nano Banana Pro)
Переносит стиль одного изображения на другое
"""
from io import BytesIO
from nano_banana_pro_api import generate_with_nano_banana_pro


def apply_style_transfer_imagen(init_image: BytesIO, style_image: BytesIO,
                                prompt: str = "",
                                aspect_ratio: str = "1:1"):
    """
    Применяет стиль одного изображения к другому через Nano Banana Pro

    Args:
        init_image: Исходное изображение (BytesIO)
        style_image: Изображение стиля (BytesIO)
        prompt: Текстовый промпт (опционально)
        aspect_ratio: Соотношение сторон (1:1, 3:4, 4:3, 9:16, 16:9)

    Returns:
        Список BytesIO объектов с результатом или raises Exception
    """
    print(f"[Style Transfer Imagen] Starting...")
    print(f"[Style Transfer Imagen] Aspect ratio: {aspect_ratio}")
    print(f"[Style Transfer Imagen] Custom prompt: {prompt if prompt else 'None'}")

    # Формируем промпт для style transfer
    if prompt:
        full_prompt = (
            f"{prompt}. Apply the artistic style, color palette, and visual techniques "
            f"from the reference images while maintaining the subject and composition."
        )
    else:
        full_prompt = (
            "Apply the artistic style, color palette, lighting, and visual techniques "
            "from the reference images to create a cohesive stylized image. "
            "Preserve the subject and composition while adopting the aesthetic of the style reference."
        )

    print(f"[Style Transfer Imagen] Full prompt: {full_prompt[:100]}...")

    # Используем оба изображения как референсы
    reference_images = [init_image, style_image]

    # Генерируем через Nano Banana Pro
    result = generate_with_nano_banana_pro(
        prompt=full_prompt,
        reference_images=reference_images,
        aspect_ratio=aspect_ratio,
        num_images=1
    )

    if not result:
        raise Exception("Failed to generate style transfer image")

    print(f"[Style Transfer Imagen] Success! Generated {len(result)} image(s)")
    return result


def generate_with_style_guide_imagen(style_image: BytesIO, prompt: str,
                                     aspect_ratio: str = "1:1"):
    """
    Генерирует новое изображение используя стиль референсного изображения

    Args:
        style_image: Изображение-стиль (BytesIO)
        prompt: Текстовый промпт (обязательно!)
        aspect_ratio: Соотношение сторон (1:1, 3:4, 4:3, 9:16, 16:9)

    Returns:
        Список BytesIO объектов с результатом или raises Exception
    """
    print(f"[Style Guide Imagen] Starting...")
    print(f"[Style Guide Imagen] Prompt: {prompt}")
    print(f"[Style Guide Imagen] Aspect ratio: {aspect_ratio}")

    # Формируем промпт для style guide
    full_prompt = (
        f"{prompt}. Use the artistic style, color palette, lighting techniques, "
        f"and visual aesthetic from the reference image to create this new image."
    )

    print(f"[Style Guide Imagen] Full prompt: {full_prompt[:100]}...")

    # Используем одно изображение как референс стиля
    reference_images = [style_image]

    # Генерируем через Nano Banana Pro
    result = generate_with_nano_banana_pro(
        prompt=full_prompt,
        reference_images=reference_images,
        aspect_ratio=aspect_ratio,
        num_images=1
    )

    if not result:
        raise Exception("Failed to generate style guide image")

    print(f"[Style Guide Imagen] Success! Generated {len(result)} image(s)")
    return result
