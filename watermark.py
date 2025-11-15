"""
Модуль для добавления watermark на изображения
"""
from PIL import Image
from io import BytesIO
import os

WATERMARK_PATH = "usp.png"
WATERMARK_OFFSET = 25  # Отступ от края в пикселях


def add_watermark(image_bytes, watermark_path=WATERMARK_PATH, offset=WATERMARK_OFFSET):
    """
    Добавляет watermark на изображение

    Args:
        image_bytes: BytesIO объект с изображением или путь к файлу
        watermark_path: путь к файлу watermark
        offset: отступ от правого нижнего угла в пикселях

    Returns:
        BytesIO объект с изображением с watermark
    """
    try:
        print(f"[INFO] Adding watermark from {watermark_path}")

        # Загружаем основное изображение
        if isinstance(image_bytes, str):
            # Если передан путь к файлу
            base_image = Image.open(image_bytes)
            print(f"[INFO] Loaded base image from file")
        else:
            # Если передан BytesIO
            image_bytes.seek(0)
            base_image = Image.open(image_bytes)
            print(f"[INFO] Loaded base image from BytesIO")

        # Конвертируем в RGBA если нужно
        if base_image.mode != 'RGBA':
            base_image = base_image.convert('RGBA')

        # Загружаем watermark
        if not os.path.exists(watermark_path):
            print(f"[WARNING] Watermark file not found: {watermark_path}")
            # Возвращаем оригинал без watermark
            output = BytesIO()
            if base_image.mode == 'RGBA':
                base_image = base_image.convert('RGB')
            base_image.save(output, format='PNG')
            output.seek(0)
            return output

        watermark = Image.open(watermark_path)

        # Конвертируем watermark в RGBA
        if watermark.mode != 'RGBA':
            watermark = watermark.convert('RGBA')

        # Уменьшаем размер watermark на 20% (оставляем 80%)
        original_size = watermark.size
        new_size = (int(watermark.width * 0.8), int(watermark.height * 0.8))
        watermark = watermark.resize(new_size, Image.Resampling.LANCZOS)
        print(f"[INFO] Watermark resized: {original_size} -> {new_size}")

        # Устанавливаем прозрачность 70% (255 * 0.7 = 178)
        watermark_data = watermark.getdata()
        new_data = []
        for item in watermark_data:
            r, g, b, a = item
            # Устанавливаем 70% непрозрачности
            if a > 0:  # Только для непрозрачных пикселей
                new_alpha = int(255 * 0.7)  # 70% непрозрачности
                new_data.append((r, g, b, new_alpha))
            else:
                new_data.append((r, g, b, 0))
        watermark.putdata(new_data)
        print(f"[INFO] Watermark opacity set to 70%")

        # Вычисляем позицию watermark (правый нижний угол с отступом)
        base_width, base_height = base_image.size
        watermark_width, watermark_height = watermark.size

        position = (
            base_width - watermark_width - offset,
            base_height - watermark_height - offset
        )

        # Создаем прозрачный слой для watermark
        transparent = Image.new('RGBA', base_image.size, (0, 0, 0, 0))
        transparent.paste(watermark, position, watermark)

        # Накладываем watermark на основное изображение
        watermarked = Image.alpha_composite(base_image, transparent)
        print(f"[OK] Watermark applied successfully at position {position}")

        # Конвертируем обратно в RGB для сохранения
        watermarked = watermarked.convert('RGB')

        # Сохраняем в BytesIO
        output = BytesIO()
        watermarked.save(output, format='PNG', quality=95)
        output.seek(0)

        print(f"[OK] Watermarked image saved, size: {len(output.getvalue())} bytes")
        return output

    except Exception as e:
        print(f"[ERROR] Watermark error: {e}")
        # В случае ошибки возвращаем оригинал
        if isinstance(image_bytes, str):
            with open(image_bytes, 'rb') as f:
                return BytesIO(f.read())
        else:
            image_bytes.seek(0)
            return image_bytes


def add_watermark_to_file(input_path, output_path, watermark_path=WATERMARK_PATH, offset=WATERMARK_OFFSET):
    """
    Добавляет watermark на изображение из файла и сохраняет в файл

    Args:
        input_path: путь к исходному изображению
        output_path: путь для сохранения результата
        watermark_path: путь к файлу watermark
        offset: отступ от правого нижнего угла

    Returns:
        True если успешно, False если ошибка
    """
    try:
        watermarked_bytes = add_watermark(input_path, watermark_path, offset)

        with open(output_path, 'wb') as f:
            f.write(watermarked_bytes.read())

        return True

    except Exception as e:
        print(f"[ERROR] Failed to add watermark to file: {e}")
        return False
