"""
Google Sheets Logger
Логирование активности пользователей бота в Google Таблицу
"""

import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import os
from typing import Optional, Dict, Any

# Настройки
CREDENTIALS_FILE = os.getenv("GSHEETS_CREDENTIALS_PATH", "tgbots-google-sheets.json")
SPREADSHEET_ID = os.getenv("GSHEETS_SPREADSHEET_ID", "1TsPo12VGW8u9YmcEhWHcIL-6yWCZ0_svBgku9fTaE0s")
ENABLED = os.getenv("GSHEETS_LOGGING", "true").lower() == "true"

# Scopes для Google Sheets API
SCOPES = [
    'https://spreadsheets.google.com/feeds',
    'https://www.googleapis.com/auth/drive'
]

# Глобальный клиент
_client = None
_spreadsheet = None


def get_client():
    """Получить клиент Google Sheets"""
    global _client, _spreadsheet

    if not ENABLED:
        return None

    try:
        if _client is None:
            # Авторизация
            creds = ServiceAccountCredentials.from_json_keyfile_name(
                CREDENTIALS_FILE,
                SCOPES
            )
            _client = gspread.authorize(creds)
            _spreadsheet = _client.open_by_key(SPREADSHEET_ID)
            print(f"[OK] Google Sheets Logger initialized: {_spreadsheet.title}")

        return _spreadsheet
    except Exception as e:
        print(f"[ERROR] Failed to initialize Google Sheets: {e}")
        return None


def init_sheets_structure():
    """Инициализировать структуру вкладок и заголовков"""
    try:
        spreadsheet = get_client()
        if not spreadsheet:
            return False

        # Структура вкладок
        sheets_config = {
            "Users": [
                "User ID", "Username", "First Name", "Last Name", "Language",
                "Registration Date", "Last Active", "Total Generations",
                "Generations Left", "Referrer ID", "Referrals Count", "Status"
            ],
            "Activity": [
                "Timestamp", "User ID", "Username", "Action", "Details", "Success"
            ],
            "Generations": [
                "Timestamp", "User ID", "Username", "Engine", "Model",
                "Prompt (RU)", "Prompt (EN)", "Format", "Style",
                "Additional Params", "Negative Prompt", "Success", "Error"
            ],
            "Referrals": [
                "Timestamp", "Referrer ID", "Referrer Username",
                "Referred ID", "Referred Username", "Reward Given"
            ],
            "Payments": [
                "Timestamp", "User ID", "Username", "Package", "Amount",
                "Currency", "Payment Method", "Status", "Invoice ID", "Generations Added"
            ],
            "Daily_Stats": [
                "Date", "New Users", "Total Generations", "SD Generations",
                "DALL-E Generations", "Total Payments", "Active Users"
            ]
        }

        existing_sheets = {ws.title for ws in spreadsheet.worksheets()}

        for sheet_name, headers in sheets_config.items():
            if sheet_name not in existing_sheets:
                # Создаем новую вкладку
                worksheet = spreadsheet.add_worksheet(
                    title=sheet_name,
                    rows=1000,
                    cols=len(headers)
                )
                print(f"[OK] Created sheet: {sheet_name}")
            else:
                worksheet = spreadsheet.worksheet(sheet_name)

            # Проверяем заголовки
            existing_headers = worksheet.row_values(1)
            if not existing_headers or existing_headers != headers:
                # Устанавливаем заголовки
                worksheet.update('A1', [headers])

                # Форматирование заголовков
                worksheet.format('A1:Z1', {
                    "backgroundColor": {"red": 0.2, "green": 0.2, "blue": 0.8},
                    "textFormat": {
                        "foregroundColor": {"red": 1.0, "green": 1.0, "blue": 1.0},
                        "fontSize": 11,
                        "bold": True
                    },
                    "horizontalAlignment": "CENTER"
                })

                # Замораживаем первую строку
                worksheet.freeze(rows=1)

                print(f"[OK] Set headers for sheet: {sheet_name}")

        print("[OK] Google Sheets structure initialized")
        return True

    except Exception as e:
        print(f"[ERROR] Failed to initialize sheets structure: {e}")
        return False


def log_user(user_id: int, username: str, first_name: str, last_name: str = "",
             language: str = "ru", referrer_id: int = None):
    """
    Логировать нового пользователя или обновить существующего
    """
    if not ENABLED:
        return

    try:
        spreadsheet = get_client()
        if not spreadsheet:
            return

        worksheet = spreadsheet.worksheet("Users")

        # Ищем пользователя
        try:
            cell = worksheet.find(str(user_id), in_column=1)
            # Пользователь существует - обновляем Last Active
            row_num = cell.row
            worksheet.update_cell(row_num, 7, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        except:
            # Новый пользователь - добавляем
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            row = [
                user_id,
                username or "",
                first_name or "",
                last_name or "",
                language,
                now,  # Registration Date
                now,  # Last Active
                0,    # Total Generations
                10,   # Generations Left
                referrer_id or "",
                0,    # Referrals Count
                "Active"
            ]
            worksheet.append_row(row)
            print(f"[GSHEETS] New user logged: {user_id} (@{username})")

    except Exception as e:
        print(f"[ERROR] Failed to log user: {e}")


def log_activity(user_id: int, username: str, action: str, details: str = "", success: bool = True):
    """
    Логировать активность пользователя
    """
    if not ENABLED:
        return

    try:
        spreadsheet = get_client()
        if not spreadsheet:
            return

        worksheet = spreadsheet.worksheet("Activity")

        row = [
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            user_id,
            username or "",
            action,
            details,
            "✅" if success else "❌"
        ]

        worksheet.append_row(row)
        print(f"[GSHEETS] Activity logged: {action} by {user_id}")

    except Exception as e:
        print(f"[ERROR] Failed to log activity: {e}")


def log_generation(user_id: int, username: str, engine: str, model: str,
                   prompt_ru: str, prompt_en: str, format_ratio: str = "",
                   style: str = "", additional_params: Dict = None,
                   negative_prompt: str = "", success: bool = True, error: str = ""):
    """
    Логировать генерацию изображения
    """
    if not ENABLED:
        return

    try:
        spreadsheet = get_client()
        if not spreadsheet:
            return

        worksheet = spreadsheet.worksheet("Generations")

        # Форматируем дополнительные параметры
        params_str = ""
        if additional_params:
            params_list = []
            if additional_params.get("shot"):
                params_list.append(f"Shot: {additional_params['shot']}")
            if additional_params.get("angle"):
                params_list.append(f"Angle: {additional_params['angle']}")
            if additional_params.get("lighting"):
                params_list.append(f"Light: {additional_params['lighting']}")
            params_str = ", ".join(params_list)

        row = [
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            user_id,
            username or "",
            engine,
            model,
            prompt_ru[:500],  # Ограничиваем длину
            prompt_en[:500],
            format_ratio,
            style,
            params_str,
            negative_prompt[:200] if negative_prompt else "",
            "✅" if success else "❌",
            error[:200] if error else ""
        ]

        worksheet.append_row(row)
        print(f"[GSHEETS] Generation logged: {engine}/{model} by {user_id}")

        # Обновляем счетчик генераций у пользователя
        update_user_generations(user_id, increment=1)

    except Exception as e:
        print(f"[ERROR] Failed to log generation: {e}")


def log_referral(referrer_id: int, referrer_username: str,
                referred_id: int, referred_username: str, reward: int = 5):
    """
    Логировать реферальную активность
    """
    if not ENABLED:
        return

    try:
        spreadsheet = get_client()
        if not spreadsheet:
            return

        worksheet = spreadsheet.worksheet("Referrals")

        row = [
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            referrer_id,
            referrer_username or "",
            referred_id,
            referred_username or "",
            reward
        ]

        worksheet.append_row(row)
        print(f"[GSHEETS] Referral logged: {referrer_id} -> {referred_id}")

        # Обновляем счетчик рефералов
        update_user_referrals(referrer_id, increment=1)

    except Exception as e:
        print(f"[ERROR] Failed to log referral: {e}")


def log_payment(user_id: int, username: str, package: str, amount: float,
               currency: str, payment_method: str, status: str,
               invoice_id: str = "", generations_added: int = 0):
    """
    Логировать оплату
    """
    if not ENABLED:
        return

    try:
        spreadsheet = get_client()
        if not spreadsheet:
            return

        worksheet = spreadsheet.worksheet("Payments")

        row = [
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            user_id,
            username or "",
            package,
            amount,
            currency,
            payment_method,
            status,
            invoice_id,
            generations_added
        ]

        worksheet.append_row(row)
        print(f"[GSHEETS] Payment logged: {package} by {user_id} - {status}")

    except Exception as e:
        print(f"[ERROR] Failed to log payment: {e}")


def update_user_generations(user_id: int, increment: int = 1, remaining: int = None):
    """
    Обновить счетчик генераций пользователя
    """
    if not ENABLED:
        return

    try:
        spreadsheet = get_client()
        if not spreadsheet:
            return

        worksheet = spreadsheet.worksheet("Users")

        # Ищем пользователя
        cell = worksheet.find(str(user_id), in_column=1)
        if cell:
            row_num = cell.row

            # Обновляем Total Generations (колонка 8)
            if increment:
                current_total = worksheet.cell(row_num, 8).value or "0"
                new_total = int(current_total) + increment
                worksheet.update_cell(row_num, 8, new_total)

            # Обновляем Generations Left (колонка 9)
            if remaining is not None:
                worksheet.update_cell(row_num, 9, remaining)

    except Exception as e:
        print(f"[ERROR] Failed to update user generations: {e}")


def update_user_referrals(user_id: int, increment: int = 1):
    """
    Обновить счетчик рефералов пользователя
    """
    if not ENABLED:
        return

    try:
        spreadsheet = get_client()
        if not spreadsheet:
            return

        worksheet = spreadsheet.worksheet("Users")

        # Ищем пользователя
        cell = worksheet.find(str(user_id), in_column=1)
        if cell:
            row_num = cell.row

            # Обновляем Referrals Count (колонка 11)
            current_count = worksheet.cell(row_num, 11).value or "0"
            new_count = int(current_count) + increment
            worksheet.update_cell(row_num, 11, new_count)

    except Exception as e:
        print(f"[ERROR] Failed to update user referrals: {e}")


def log_daily_stats(date: str = None, new_users: int = 0, total_gens: int = 0,
                    sd_gens: int = 0, dalle_gens: int = 0, total_payments: float = 0.0,
                    active_users: int = 0):
    """
    Логировать дневную статистику
    """
    if not ENABLED:
        return

    try:
        spreadsheet = get_client()
        if not spreadsheet:
            return

        worksheet = spreadsheet.worksheet("Daily_Stats")

        if not date:
            date = datetime.now().strftime("%Y-%m-%d")

        row = [
            date,
            new_users,
            total_gens,
            sd_gens,
            dalle_gens,
            total_payments,
            active_users
        ]

        worksheet.append_row(row)
        print(f"[GSHEETS] Daily stats logged for {date}")

    except Exception as e:
        print(f"[ERROR] Failed to log daily stats: {e}")


# Инициализация при импорте модуля
if ENABLED:
    try:
        init_sheets_structure()
    except Exception as e:
        print(f"[ERROR] Failed to auto-initialize sheets: {e}")


# Тестовая функция
if __name__ == "__main__":
    print("Testing Google Sheets Logger...")

    # Тест логирования пользователя
    log_user(12345, "test_user", "Test", "User", "en")

    # Тест логирования активности
    log_activity(12345, "test_user", "/start", "Bot started", True)

    # Тест логирования генерации
    log_generation(
        12345, "test_user", "sd", "sd3.5-large",
        "Красивый пейзаж", "Beautiful landscape",
        "16:9", "photographic",
        {"shot": "wide", "lighting": "golden hour"},
        "ugly, bad", True
    )

    print("Test completed!")
