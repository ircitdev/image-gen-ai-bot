"""
Google Cloud Storage Helper
Управление изображениями в Google Cloud Storage
"""

import os
import io
import uuid
from typing import Optional, Union
from datetime import datetime, timedelta
from google.cloud import storage
from PIL import Image
from settings import GCS_BUCKET_NAME, GCS_CREDENTIALS_PATH

# Настройки
CREDENTIALS_PATH = GCS_CREDENTIALS_PATH
BUCKET_NAME = GCS_BUCKET_NAME
PUBLIC_URL_BASE = f"https://storage.googleapis.com/{BUCKET_NAME}"

# Инициализация клиента GCS
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = CREDENTIALS_PATH
storage_client = storage.Client()


def get_bucket():
    """Получить bucket для хранения изображений"""
    try:
        bucket = storage_client.bucket(BUCKET_NAME)

        # Проверяем существует ли bucket, если нет - создаем
        if not bucket.exists():
            print(f"[INFO] Creating bucket {BUCKET_NAME}...")
            bucket = storage_client.create_bucket(BUCKET_NAME, location="us-central1")

            # Делаем bucket публичным для чтения
            bucket.make_public(recursive=True, future=True)
            print(f"[OK] Bucket {BUCKET_NAME} created and made public")

        return bucket
    except Exception as e:
        print(f"[ERROR] Failed to get bucket: {e}")
        return None


def upload_image(image_data: Union[bytes, io.BytesIO], folder: str = "images",
                 filename: Optional[str] = None, content_type: str = "image/png") -> Optional[str]:
    """
    Загрузить изображение в GCS

    Args:
        image_data: Данные изображения (bytes или BytesIO)
        folder: Папка в bucket (по умолчанию "images")
        filename: Имя файла (если None, генерируется автоматически)
        content_type: MIME тип файла

    Returns:
        Публичный URL изображения или None при ошибке
    """
    try:
        bucket = get_bucket()
        if not bucket:
            return None

        # Генерируем уникальное имя файла если не указано
        if not filename:
            file_extension = content_type.split("/")[-1]
            filename = f"{uuid.uuid4().hex}.{file_extension}"

        # Путь к файлу в bucket
        blob_name = f"{folder}/{filename}"

        # Создаем blob
        blob = bucket.blob(blob_name)

        # Конвертируем BytesIO в bytes если нужно
        if isinstance(image_data, io.BytesIO):
            image_data.seek(0)
            data = image_data.read()
        else:
            data = image_data

        # Загружаем файл
        blob.upload_from_string(data, content_type=content_type)

        # Делаем blob публичным
        blob.make_public()

        # Получаем публичный URL
        public_url = blob.public_url

        print(f"[OK] Image uploaded to GCS: {public_url}")
        return public_url

    except Exception as e:
        print(f"[ERROR] Failed to upload image to GCS: {e}")
        return None


def upload_pil_image(pil_image: Image.Image, folder: str = "images",
                     filename: Optional[str] = None, format: str = "PNG") -> Optional[str]:
    """
    Загрузить PIL Image в GCS

    Args:
        pil_image: PIL Image объект
        folder: Папка в bucket
        filename: Имя файла
        format: Формат изображения (PNG, JPEG, etc.)

    Returns:
        Публичный URL изображения
    """
    try:
        # Конвертируем PIL Image в bytes
        img_byte_arr = io.BytesIO()
        pil_image.save(img_byte_arr, format=format)
        img_byte_arr.seek(0)

        # Определяем content type
        content_type = f"image/{format.lower()}"

        return upload_image(img_byte_arr, folder=folder, filename=filename, content_type=content_type)

    except Exception as e:
        print(f"[ERROR] Failed to upload PIL image: {e}")
        return None


def delete_image(blob_name: str) -> bool:
    """
    Удалить изображение из GCS

    Args:
        blob_name: Путь к файлу в bucket (например: "images/abc123.png")

    Returns:
        True если удалено успешно
    """
    try:
        bucket = get_bucket()
        if not bucket:
            return False

        blob = bucket.blob(blob_name)
        blob.delete()

        print(f"[OK] Image deleted from GCS: {blob_name}")
        return True

    except Exception as e:
        print(f"[ERROR] Failed to delete image: {e}")
        return False


def delete_old_images(folder: str = "images", days_old: int = 7) -> int:
    """
    Удалить изображения старше указанного количества дней

    Args:
        folder: Папка в bucket
        days_old: Удалить файлы старше N дней

    Returns:
        Количество удаленных файлов
    """
    try:
        bucket = get_bucket()
        if not bucket:
            return 0

        cutoff_date = datetime.now() - timedelta(days=days_old)
        deleted_count = 0

        # Получаем список всех файлов в папке
        blobs = bucket.list_blobs(prefix=f"{folder}/")

        for blob in blobs:
            # Проверяем дату создания
            if blob.time_created.replace(tzinfo=None) < cutoff_date:
                blob.delete()
                deleted_count += 1
                print(f"[INFO] Deleted old image: {blob.name}")

        print(f"[OK] Deleted {deleted_count} old images")
        return deleted_count

    except Exception as e:
        print(f"[ERROR] Failed to delete old images: {e}")
        return 0


def get_public_url(blob_name: str) -> str:
    """
    Получить публичный URL для файла в GCS

    Args:
        blob_name: Путь к файлу в bucket

    Returns:
        Публичный URL
    """
    return f"{PUBLIC_URL_BASE}/{blob_name}"


def list_images(folder: str = "images", limit: int = 100) -> list:
    """
    Получить список изображений в папке

    Args:
        folder: Папка в bucket
        limit: Максимальное количество результатов

    Returns:
        Список публичных URL изображений
    """
    try:
        bucket = get_bucket()
        if not bucket:
            return []

        blobs = bucket.list_blobs(prefix=f"{folder}/", max_results=limit)
        return [blob.public_url for blob in blobs]

    except Exception as e:
        print(f"[ERROR] Failed to list images: {e}")
        return []


# Тестовая функция
if __name__ == "__main__":
    print("Testing GCS Helper...")

    # Создаем тестовое изображение
    test_img = Image.new('RGB', (100, 100), color='red')

    # Загружаем в GCS
    url = upload_pil_image(test_img, folder="test", filename="test.png")

    if url:
        print(f"Test image uploaded: {url}")
    else:
        print("Failed to upload test image")
