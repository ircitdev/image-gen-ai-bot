"""
Модуль для управления пресетами параметров генерации
"""
import json
import os
from datetime import datetime

PRESETS_FILE = "user_presets.json"


def load_presets():
    """Загружает пресеты из файла"""
    if os.path.exists(PRESETS_FILE):
        try:
            with open(PRESETS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}


def save_presets(presets_data):
    """Сохраняет пресеты в файл"""
    with open(PRESETS_FILE, 'w', encoding='utf-8') as f:
        json.dump(presets_data, f, ensure_ascii=False, indent=2)


def create_preset(user_id, preset_name, model, format_ratio, style="none", negative_prompt=""):
    """Создает новый пресет для пользователя"""
    presets = load_presets()
    user_key = str(user_id)

    if user_key not in presets:
        presets[user_key] = {}

    # Проверяем, не существует ли уже пресет с таким именем
    if preset_name in presets[user_key]:
        return False, "Пресет с таким именем уже существует"

    # Создаем пресет
    presets[user_key][preset_name] = {
        "model": model,
        "format": format_ratio,
        "style": style,
        "negative_prompt": negative_prompt,
        "created": datetime.now().isoformat()
    }

    save_presets(presets)
    return True, "Пресет успешно создан"


def get_user_presets(user_id):
    """Получает все пресеты пользователя"""
    presets = load_presets()
    user_key = str(user_id)

    if user_key not in presets:
        return {}

    return presets[user_key]


def get_preset(user_id, preset_name):
    """Получает конкретный пресет"""
    presets = load_presets()
    user_key = str(user_id)

    if user_key not in presets or preset_name not in presets[user_key]:
        return None

    return presets[user_key][preset_name]


def delete_preset(user_id, preset_name):
    """Удаляет пресет"""
    presets = load_presets()
    user_key = str(user_id)

    if user_key not in presets or preset_name not in presets[user_key]:
        return False

    del presets[user_key][preset_name]
    save_presets(presets)
    return True


def rename_preset(user_id, old_name, new_name):
    """Переименовывает пресет"""
    presets = load_presets()
    user_key = str(user_id)

    if user_key not in presets or old_name not in presets[user_key]:
        return False, "Пресет не найден"

    if new_name in presets[user_key]:
        return False, "Пресет с таким именем уже существует"

    # Копируем данные под новым именем и удаляем старое
    presets[user_key][new_name] = presets[user_key][old_name]
    del presets[user_key][old_name]

    save_presets(presets)
    return True, "Пресет переименован"
