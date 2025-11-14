"""
Модуль для обработки платежей через Telegram Stars и CryptoBot
"""
import requests
from settings import CRYPTOBOT_TOKEN, CRYPTOBOT_CURRENCY

# Пакеты генераций
# Цены в Telegram Stars и USDT
PACKAGES = {
    "small": {
        "name": "Starter",
        "generations": 50,
        "stars": 100,  # Telegram Stars
        "usdt": 1.0,   # USDT через CryptoBot
        "description": "50 генераций"
    },
    "medium": {
        "name": "Pro",
        "generations": 150,
        "stars": 250,
        "usdt": 2.5,
        "description": "150 генераций + бонус"
    },
    "large": {
        "name": "Premium",
        "generations": 500,
        "stars": 700,
        "usdt": 7.0,
        "description": "500 генераций + VIP поддержка"
    },
    "unlimited": {
        "name": "Unlimited",
        "generations": 9999,
        "stars": 2000,
        "usdt": 20.0,
        "description": "Безлимит на месяц"
    }
}


def get_package_info(package_id):
    """Получает информацию о пакете"""
    return PACKAGES.get(package_id)


def create_cryptobot_invoice(user_id, package_id):
    """
    Создает инвойс через CryptoBot API

    Args:
        user_id: Telegram user ID
        package_id: ID пакета (small, medium, large, unlimited)

    Returns:
        dict с данными инвойса или None при ошибке
    """
    package = PACKAGES.get(package_id)
    if not package:
        return None

    try:
        api_url = "https://pay.crypt.bot/api/createInvoice"

        headers = {
            "Crypto-Pay-API-Token": CRYPTOBOT_TOKEN
        }

        payload = {
            "currency_type": "crypto",
            "asset": CRYPTOBOT_CURRENCY,
            "amount": str(package["usdt"]),
            "description": f"{package['name']} - {package['description']}",
            "payload": f"{user_id}:{package_id}",  # Для идентификации платежа
            "return_url": f"https://t.me/imageGenBot",
            "paid_btn_name": "viewItem",
            "paid_btn_url": f"https://t.me/imageGenBot"
        }

        response = requests.post(api_url, json=payload, headers=headers)

        if response.status_code == 200:
            data = response.json()
            if data.get("ok"):
                return data.get("result")

        print(f"[ERROR] CryptoBot API error: {response.text}")
        return None

    except Exception as e:
        print(f"[ERROR] Failed to create CryptoBot invoice: {e}")
        return None


def check_cryptobot_invoice(invoice_id):
    """
    Проверяет статус инвойса через CryptoBot API

    Args:
        invoice_id: ID инвойса

    Returns:
        dict с данными инвойса или None
    """
    try:
        api_url = "https://pay.crypt.bot/api/getInvoices"

        headers = {
            "Crypto-Pay-API-Token": CRYPTOBOT_TOKEN
        }

        params = {
            "invoice_ids": invoice_id
        }

        response = requests.get(api_url, params=params, headers=headers)

        if response.status_code == 200:
            data = response.json()
            if data.get("ok"):
                invoices = data.get("result", {}).get("items", [])
                if invoices:
                    return invoices[0]

        return None

    except Exception as e:
        print(f"[ERROR] Failed to check CryptoBot invoice: {e}")
        return None


def format_package_message(package_id):
    """Форматирует сообщение о пакете"""
    package = PACKAGES.get(package_id)
    if not package:
        return "Пакет не найден"

    msg = f"""📦 <b>{package['name']}</b>

💎 <b>Генераций:</b> {package['generations']}
⭐ <b>Цена (Stars):</b> {package['stars']} ⭐
💰 <b>Цена (USDT):</b> ${package['usdt']}

📝 {package['description']}"""

    return msg


def get_all_packages_message():
    """Возвращает сообщение со всеми пакетами"""
    msg = """💎 <b>Пакеты генераций</b>

Выберите подходящий пакет:

"""

    for package_id, package in PACKAGES.items():
        msg += f"""
📦 <b>{package['name']}</b>
   • {package['generations']} генераций
   • ⭐ {package['stars']} Stars | 💰 ${package['usdt']} USDT

"""

    msg += "\n💡 <i>Оплата через Telegram Stars или криптовалюту (USDT)</i>"

    return msg
