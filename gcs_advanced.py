"""
GCS Advanced Features
Расширенные функции для работы с Google Cloud Storage
"""

import json
import zipfile
from io import BytesIO
from typing import Optional, List, Dict
from datetime import datetime, timedelta
import gcs_helper as gcs


def save_image_metadata(user_id: int, blob_name: str, metadata: dict) -> bool:
    """Сохранить метаданные изображения"""
    try:
        bucket = gcs.get_bucket()
        if not bucket:
            return False
        meta_blob_name = blob_name.replace('.png', '.json').replace('.jpg', '.json').replace('.jpeg', '.json')
        meta_blob = bucket.blob(meta_blob_name)
        if 'timestamp' not in metadata:
            metadata['timestamp'] = datetime.now().isoformat()
        meta_blob.upload_from_string(
            json.dumps(metadata, ensure_ascii=False, indent=2),
            content_type='application/json'
        )
        print(f'[OK] Metadata saved: {meta_blob_name}')
        return True
    except Exception as e:
        print(f'[ERROR] Failed to save metadata: {e}')
        return False


def get_image_metadata(blob_name: str) -> Optional[dict]:
    """Получить метаданные изображения"""
    try:
        bucket = gcs.get_bucket()
        if not bucket:
            return None
        meta_blob_name = blob_name.replace('.png', '.json').replace('.jpg', '.json').replace('.jpeg', '.json')
        meta_blob = bucket.blob(meta_blob_name)
        if not meta_blob.exists():
            return None
        metadata_str = meta_blob.download_as_text()
        return json.loads(metadata_str)
    except Exception as e:
        print(f'[ERROR] Failed to get metadata: {e}')
        return None


def add_to_favorites(user_id: int, blob_name: str) -> bool:
    """Добавить изображение в избранное"""
    try:
        bucket = gcs.get_bucket()
        if not bucket:
            return False
        if not blob_name.startswith(f'users/{user_id}/'):
            return False
        filename = blob_name.split('/')[-1]
        fav_blob_name = f'users/{user_id}/favorites/{filename}'
        source_blob = bucket.blob(blob_name)
        bucket.copy_blob(source_blob, bucket, fav_blob_name)
        meta_source = blob_name.replace('.png', '.json').replace('.jpg', '.json')
        meta_dest = fav_blob_name.replace('.png', '.json').replace('.jpg', '.json')
        meta_blob = bucket.blob(meta_source)
        if meta_blob.exists():
            bucket.copy_blob(meta_blob, bucket, meta_dest)
        print(f'[OK] Added to favorites: {fav_blob_name}')
        return True
    except Exception as e:
        print(f'[ERROR] Failed to add to favorites: {e}')
        return False


def remove_from_favorites(user_id: int, blob_name: str) -> bool:
    """Удалить изображение из избранного"""
    try:
        if not blob_name.startswith(f'users/{user_id}/favorites/'):
            return False
        return gcs.delete_user_image(user_id, blob_name)
    except Exception as e:
        print(f'[ERROR] Failed to remove from favorites: {e}')
        return False


def is_in_favorites(user_id: int, filename: str) -> bool:
    """Проверить находится ли изображение в избранном"""
    try:
        bucket = gcs.get_bucket()
        if not bucket:
            return False
        fav_blob_name = f'users/{user_id}/favorites/{filename}'
        blob = bucket.blob(fav_blob_name)
        return blob.exists()
    except Exception as e:
        return False


def get_user_images_filtered(user_id: int, category=None, days=None, limit: int = 100, offset: int = 0) -> List[Dict]:
    """Получить изображения пользователя с фильтрацией"""
    bucket = gcs.get_bucket()
    if not bucket:
        return []
    prefix = f'users/{user_id}/{category}/' if category else f'users/{user_id}/'
    blobs = list(bucket.list_blobs(prefix=prefix))
    images = []
    cutoff_date = None
    if days and blobs:
        cutoff_date = datetime.now(blobs[0].time_created.tzinfo) - timedelta(days=days)
    for blob in blobs:
        if blob.name.endswith('/') or blob.name.endswith('.json'):
            continue
        if cutoff_date and blob.time_created < cutoff_date:
            continue
        parts = blob.name.split('/')
        img_category = parts[2] if len(parts) > 2 else 'unknown'
        filename = blob.name.split('/')[-1]
        metadata = get_image_metadata(blob.name)
        in_fav = is_in_favorites(user_id, filename) if img_category != 'favorites' else True
        images.append({
            'url': f'{gcs.PUBLIC_URL_BASE}/{blob.name}',
            'name': filename,
            'category': img_category,
            'size': blob.size,
            'created': blob.time_created,
            'blob_name': blob.name,
            'metadata': metadata or {},
            'in_favorites': in_fav
        })
    images.sort(key=lambda x: x['created'], reverse=True)
    return images[offset:offset + limit]


def export_user_images(user_id: int, category=None) -> Optional[BytesIO]:
    """Экспорт всех изображений пользователя в ZIP архив"""
    try:
        bucket = gcs.get_bucket()
        if not bucket:
            return None
        prefix = f'users/{user_id}/{category}/' if category else f'users/{user_id}/'
        blobs = bucket.list_blobs(prefix=prefix)
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for blob in blobs:
                if blob.name.endswith('/') or blob.name.endswith('.json'):
                    continue
                image_data = blob.download_as_bytes()
                filename = blob.name.replace(f'users/{user_id}/', '')
                zip_file.writestr(filename, image_data)
                metadata = get_image_metadata(blob.name)
                if metadata:
                    meta_filename = filename.replace('.png', '.json').replace('.jpg', '.json')
                    zip_file.writestr(meta_filename, json.dumps(metadata, ensure_ascii=False, indent=2))
        zip_buffer.seek(0)
        print(f'[OK] Exported images for user {user_id}')
        return zip_buffer
    except Exception as e:
        print(f'[ERROR] Failed to export images: {e}')
        return None


def add_tags_to_image(user_id: int, blob_name: str, tags: list) -> bool:
    """Добавить теги к изображению"""
    try:
        metadata = get_image_metadata(blob_name) or {}
        existing_tags = metadata.get('tags', [])
        new_tags = list(set(existing_tags + tags))
        metadata['tags'] = new_tags
        return save_image_metadata(user_id, blob_name, metadata)
    except Exception as e:
        print(f'[ERROR] Failed to add tags: {e}')
        return False


def search_by_tags(user_id: int, tags: list, category=None) -> List[Dict]:
    """Поиск изображений по тегам"""
    try:
        images = get_user_images_filtered(user_id, category=category, limit=1000)
        results = []
        for img in images:
            img_tags = img.get('metadata', {}).get('tags', [])
            if any(tag in img_tags for tag in tags):
                results.append(img)
        return results
    except Exception as e:
        print(f'[ERROR] Failed to search by tags: {e}')
        return []


def get_operation_stats(user_id: int, days=30) -> Dict:
    """Получить статистику использования операций редактирования"""
    try:
        images = get_user_images_filtered(user_id, days=days, limit=1000)
        stats = {}
        for img in images:
            operation = img.get('metadata', {}).get('operation_type', 'unknown')
            stats[operation] = stats.get(operation, 0) + 1
        return stats
    except Exception as e:
        print(f'[ERROR] Failed to get operation stats: {e}')
        return {}


def get_images_near_expiry(user_id: int, days_before=7) -> List[Dict]:
    """Получить изображения которые будут удалены через N дней"""
    try:
        bucket = gcs.get_bucket()
        if not bucket:
            return []
        lifecycle_days = 60
        images = []
        for category in ['generated', 'uploaded', 'edited', 'favorites']:
            prefix = f'users/{user_id}/{category}/'
            blobs = list(bucket.list_blobs(prefix=prefix))
            if not blobs:
                continue
            cutoff_date = datetime.now(blobs[0].time_created.tzinfo) - timedelta(days=lifecycle_days - days_before)
            for blob in blobs:
                if blob.name.endswith('/') or blob.name.endswith('.json'):
                    continue
                if blob.time_created < cutoff_date:
                    days_left = lifecycle_days - (datetime.now(blob.time_created.tzinfo) - blob.time_created).days
                    images.append({
                        'url': f'{gcs.PUBLIC_URL_BASE}/{blob.name}',
                        'name': blob.name.split('/')[-1],
                        'category': category,
                        'days_left': days_left,
                        'blob_name': blob.name
                    })
        return images
    except Exception as e:
        print(f'[ERROR] Failed to get images near expiry: {e}')
        return []


def toggle_favorite(user_id: int, blob_name: str) -> bool:
    """Переключить статус избранного для изображения"""
    filename = blob_name.split('/')[-1]
    if is_in_favorites(user_id, filename):
        fav_blob = f'users/{user_id}/favorites/{filename}'
        return remove_from_favorites(user_id, fav_blob)
    else:
        return add_to_favorites(user_id, blob_name)
