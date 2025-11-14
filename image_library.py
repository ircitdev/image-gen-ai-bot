"""
Модуль для управления библиотекой изображений пользователей
"""
import json
import os
from datetime import datetime

LIBRARY_FILE = "image_library.json"
MAX_HISTORY_PER_USER = 50  # Максимум записей в истории на пользователя


def load_library():
    """Загружает библиотеку из файла"""
    if os.path.exists(LIBRARY_FILE):
        try:
            with open(LIBRARY_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}


def save_library(library_data):
    """Сохраняет библиотеку в файл"""
    with open(LIBRARY_FILE, 'w', encoding='utf-8') as f:
        json.dump(library_data, f, ensure_ascii=False, indent=2)


def add_to_history(user_id, prompt, english_prompt, params, image_url=None, negative_prompt=""):
    """
    Добавляет генерацию в историю пользователя

    Args:
        user_id: ID пользователя
        prompt: Оригинальный промпт на русском
        english_prompt: Переведенный промпт на английском
        params: Параметры генерации (model, format, style)
        image_url: URL изображения (опционально)
        negative_prompt: Negative prompt (что НЕ должно быть)
    """
    library = load_library()
    user_key = str(user_id)

    if user_key not in library:
        library[user_key] = {
            "history": [],
            "favorites": []
        }

    # Создаем запись генерации
    generation = {
        "id": datetime.now().timestamp(),  # Уникальный ID
        "date": datetime.now().isoformat(),
        "prompt": prompt,
        "english_prompt": english_prompt,
        "model": params.get("model", ""),
        "format": params.get("format", ""),
        "style": params.get("style", "none"),
        "negative_prompt": negative_prompt,
        "image_url": image_url,
        "is_favorite": False
    }

    # Добавляем в начало списка (новые сверху)
    library[user_key]["history"].insert(0, generation)

    # Ограничиваем размер истории
    if len(library[user_key]["history"]) > MAX_HISTORY_PER_USER:
        library[user_key]["history"] = library[user_key]["history"][:MAX_HISTORY_PER_USER]

    save_library(library)
    return generation["id"]


def get_user_history(user_id, limit=10, offset=0):
    """
    Получает историю генераций пользователя

    Args:
        user_id: ID пользователя
        limit: Количество записей
        offset: Смещение (для пагинации)

    Returns:
        List of generations
    """
    library = load_library()
    user_key = str(user_id)

    if user_key not in library:
        return []

    history = library[user_key]["history"]
    return history[offset:offset+limit]


def get_favorites(user_id):
    """Получает избранные генерации пользователя"""
    library = load_library()
    user_key = str(user_id)

    if user_key not in library:
        return []

    # Возвращаем только помеченные как избранные
    return [gen for gen in library[user_key]["history"] if gen.get("is_favorite", False)]


def toggle_favorite(user_id, generation_id):
    """Добавляет/удаляет генерацию из избранного"""
    library = load_library()
    user_key = str(user_id)

    if user_key not in library:
        return False

    # Ищем генерацию по ID
    for gen in library[user_key]["history"]:
        if gen["id"] == generation_id:
            gen["is_favorite"] = not gen.get("is_favorite", False)
            save_library(library)
            return gen["is_favorite"]

    return False


def search_history(user_id, query):
    """
    Поиск по истории генераций

    Args:
        user_id: ID пользователя
        query: Поисковый запрос

    Returns:
        List of matching generations
    """
    library = load_library()
    user_key = str(user_id)

    if user_key not in library:
        return []

    query_lower = query.lower()
    results = []

    for gen in library[user_key]["history"]:
        # Ищем в промпте
        if query_lower in gen.get("prompt", "").lower() or \
           query_lower in gen.get("english_prompt", "").lower():
            results.append(gen)

    return results


def get_history_stats(user_id):
    """Получает статистику по истории пользователя"""
    library = load_library()
    user_key = str(user_id)

    if user_key not in library:
        return {
            "total": 0,
            "favorites": 0,
            "most_used_model": None,
            "most_used_style": None
        }

    history = library[user_key]["history"]

    # Считаем статистику
    models = {}
    styles = {}

    for gen in history:
        model = gen.get("model", "unknown")
        style = gen.get("style", "none")

        models[model] = models.get(model, 0) + 1
        styles[style] = styles.get(style, 0) + 1

    most_used_model = max(models.items(), key=lambda x: x[1])[0] if models else None
    most_used_style = max(styles.items(), key=lambda x: x[1])[0] if styles else None

    return {
        "total": len(history),
        "favorites": len(get_favorites(user_id)),
        "most_used_model": most_used_model,
        "most_used_style": most_used_style
    }


def clear_history(user_id):
    """Очищает историю пользователя (кроме избранного)"""
    library = load_library()
    user_key = str(user_id)

    if user_key not in library:
        return False

    # Оставляем только избранное
    favorites = get_favorites(user_id)
    library[user_key]["history"] = favorites

    save_library(library)
    return True
