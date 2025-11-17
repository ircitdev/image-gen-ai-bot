"""
Модуль для отслеживания лимитов генераций пользователей
"""
import json
import os
from datetime import datetime

LIMITS_FILE = "user_limits.json"
FREE_GENERATIONS_LIMIT = 10


def load_limits():
    """Загружает данные о лимитах из файла"""
    if os.path.exists(LIMITS_FILE):
        try:
            with open(LIMITS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}


def save_limits(limits_data):
    """Сохраняет данные о лимитах в файл"""
    with open(LIMITS_FILE, 'w', encoding='utf-8') as f:
        json.dump(limits_data, f, ensure_ascii=False, indent=2)


def get_user_generations(user_id):
    """Получает количество использованных генераций пользователя"""
    limits = load_limits()
    user_key = str(user_id)

    if user_key not in limits:
        limits[user_key] = {
            "used": 0,
            "first_generation": None
        }
        save_limits(limits)

    return limits[user_key]["used"]


def can_generate(user_id):
    """Проверяет, может ли пользователь генерировать изображение"""
    used = get_user_generations(user_id)
    remaining = FREE_GENERATIONS_LIMIT - used
    return remaining > 0, remaining


def use_generation(user_id):
    """Использует одну генерацию"""
    limits = load_limits()
    user_key = str(user_id)

    if user_key not in limits:
        limits[user_key] = {
            "used": 0,
            "first_generation": None,
            "referrer_id": None,
            "referrals": []
        }

    # Проверяем, это первая генерация?
    is_first_generation = limits[user_key]["first_generation"] is None

    # Записываем время первой генерации
    if is_first_generation:
        limits[user_key]["first_generation"] = datetime.now().isoformat()

    limits[user_key]["used"] += 1
    save_limits(limits)

    # Если это первая генерация, начисляем бонус пригласившему
    if is_first_generation:
        reward_referrer(user_id)

    remaining = FREE_GENERATIONS_LIMIT - limits[user_key]["used"]
    return remaining


def get_user_stats(user_id):
    """Получает статистику пользователя"""
    limits = load_limits()
    user_key = str(user_id)

    if user_key not in limits:
        return {
            "used": 0,
            "remaining": FREE_GENERATIONS_LIMIT,
            "first_generation": None
        }

    used = limits[user_key]["used"]
    return {
        "used": used,
        "remaining": FREE_GENERATIONS_LIMIT - used,
        "first_generation": limits[user_key].get("first_generation")
    }


def reset_user_limit(user_id):
    """Сбрасывает лимит пользователя (для админа)"""
    limits = load_limits()
    user_key = str(user_id)

    if user_key in limits:
        limits[user_key] = {
            "used": 0,
            "first_generation": None
        }
        save_limits(limits)
        return True
    return False


def get_all_users():
    """Получает список всех пользователей с их статистикой (для админа)"""
    limits = load_limits()
    users_list = []

    for user_id, data in limits.items():
        used = data.get("used", 0)
        remaining = FREE_GENERATIONS_LIMIT - used
        first_gen = data.get("first_generation", "Не было")
        referrals = data.get("referrals", [])
        referrals_count = len(referrals)

        users_list.append({
            "user_id": user_id,
            "used": used,
            "remaining": remaining,
            "first_generation": first_gen,
            "referrals_count": referrals_count
        })

    return users_list


def add_generations(user_id, amount):
    """Добавляет генерации пользователю (для админа)"""
    limits = load_limits()
    user_key = str(user_id)

    if user_key not in limits:
        limits[user_key] = {
            "used": 0,
            "first_generation": None,
            "referrer_id": None,
            "referrals": []
        }

    # Уменьшаем количество использованных генераций
    limits[user_key]["used"] = max(0, limits[user_key]["used"] - amount)
    save_limits(limits)

    remaining = FREE_GENERATIONS_LIMIT - limits[user_key]["used"]
    return remaining


def register_referral(user_id, referrer_id):
    """Регистрирует пользователя по реферальной ссылке"""
    limits = load_limits()
    user_key = str(user_id)
    referrer_key = str(referrer_id)

    # Нельзя быть своим рефералом
    if user_key == referrer_key:
        return False

    # Создаем запись для нового пользователя
    if user_key not in limits:
        limits[user_key] = {
            "used": 0,
            "first_generation": None,
            "referrer_id": referrer_id,
            "referrals": []
        }
    else:
        # Если пользователь уже есть, но у него нет referrer - устанавливаем
        if limits[user_key].get("referrer_id") is None:
            limits[user_key]["referrer_id"] = referrer_id
        else:
            # У пользователя уже есть реферер
            return False

    # Добавляем в список рефералов пригласившего
    if referrer_key not in limits:
        limits[referrer_key] = {
            "used": 0,
            "first_generation": None,
            "referrer_id": None,
            "referrals": []
        }

    if user_id not in limits[referrer_key].get("referrals", []):
        if "referrals" not in limits[referrer_key]:
            limits[referrer_key]["referrals"] = []
        limits[referrer_key]["referrals"].append(user_id)

    save_limits(limits)
    return True


def reward_referrer(user_id):
    """Начисляет бонус пригласившему при первой генерации реферала"""
    limits = load_limits()
    user_key = str(user_id)

    if user_key not in limits:
        return None

    referrer_id = limits[user_key].get("referrer_id")
    if not referrer_id:
        return None

    # Проверяем, не начислили ли уже бонус
    if limits[user_key].get("referral_bonus_given"):
        return None

    # Помечаем, что бонус начислен
    limits[user_key]["referral_bonus_given"] = True

    # Начисляем бонус пригласившему (+5 генераций)
    referrer_key = str(referrer_id)
    if referrer_key in limits:
        limits[referrer_key]["used"] = max(0, limits[referrer_key]["used"] - 5)
        save_limits(limits)
        return referrer_id

    return None


def get_referral_stats(user_id):
    """Получает статистику рефералов пользователя"""
    limits = load_limits()
    user_key = str(user_id)

    if user_key not in limits:
        return {
            "referrals_count": 0,
            "referrals_with_generations": 0,
            "referrer_id": None
        }

    referrals = limits[user_key].get("referrals", [])
    referrals_with_gen = 0

    # Считаем рефералов, которые сделали хотя бы одну генерацию
    for ref_id in referrals:
        ref_key = str(ref_id)
        if ref_key in limits and limits[ref_key].get("used", 0) > 0:
            referrals_with_gen += 1

    return {
        "referrals_count": len(referrals),
        "referrals_with_generations": referrals_with_gen,
        "referrer_id": limits[user_key].get("referrer_id")
    }
