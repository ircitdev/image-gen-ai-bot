"""
Google Imagen 4 Models Configuration
Поддерживаемые модели на основе актуального API
"""

# Доступные Imagen модели
IMAGEN_MODELS = {
    "imagen-4": {
        "id": "imagen-4.0-generate-001",
        "name": "🍌 Imagen 4 (Nano Banana)",
        "description": "Стандартная версия - баланс качества и скорости",
        "emoji": "🍌",
        "speed": "medium",
        "quality": "high"
    },
    "imagen-4-ultra": {
        "id": "imagen-4.0-ultra-generate-001",
        "name": "💎 Imagen 4 Ultra",
        "description": "Максимальное качество - медленнее, но лучше",
        "emoji": "💎",
        "speed": "slow",
        "quality": "ultra"
    },
    "imagen-4-fast": {
        "id": "imagen-4.0-fast-generate-001",
        "name": "⚡ Imagen 4 Fast",
        "description": "Быстрая генерация - хорошее качество",
        "emoji": "⚡",
        "speed": "fast",
        "quality": "good"
    }
}

# Дефолтная модель
DEFAULT_IMAGEN_MODEL = "imagen-4"

def get_model_endpoint(model_key: str = None) -> str:
    """Получить endpoint для модели"""
    if model_key is None or model_key not in IMAGEN_MODELS:
        model_key = DEFAULT_IMAGEN_MODEL

    model_id = IMAGEN_MODELS[model_key]["id"]
    return f"https://generativelanguage.googleapis.com/v1beta/models/{model_id}:predict"

def get_model_name(model_key: str = None) -> str:
    """Получить красивое имя модели"""
    if model_key is None or model_key not in IMAGEN_MODELS:
        model_key = DEFAULT_IMAGEN_MODEL

    return IMAGEN_MODELS[model_key]["name"]

def get_model_emoji(model_key: str = None) -> str:
    """Получить эмодзи модели"""
    if model_key is None or model_key not in IMAGEN_MODELS:
        model_key = DEFAULT_IMAGEN_MODEL

    return IMAGEN_MODELS[model_key]["emoji"]
