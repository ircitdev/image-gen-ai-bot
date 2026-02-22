import sys
import os
import fcntl
import atexit

# ===== ЗАЩИТА ОТ ЗАПУСКА НЕСКОЛЬКИХ КОПИЙ =====
LOCK_FILE = "/tmp/imagegen_bot.lock"

def acquire_lock():
    """Получает блокировку для предотвращения запуска нескольких копий бота"""
    global lock_file_handle
    try:
        lock_file_handle = open(LOCK_FILE, 'w')
        fcntl.flock(lock_file_handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        lock_file_handle.write(str(os.getpid()))
        lock_file_handle.flush()
        print(f"[LOCK] Bot lock acquired, PID: {os.getpid()}")
        return True
    except IOError:
        # Читаем PID запущенного процесса
        try:
            with open(LOCK_FILE, 'r') as f:
                existing_pid = f.read().strip()
            print(f"[LOCK ERROR] Bot is already running! PID: {existing_pid}")
        except:
            print("[LOCK ERROR] Bot is already running!")
        return False

def release_lock():
    """Освобождает блокировку при завершении"""
    global lock_file_handle
    try:
        if lock_file_handle:
            fcntl.flock(lock_file_handle, fcntl.LOCK_UN)
            lock_file_handle.close()
        if os.path.exists(LOCK_FILE):
            os.remove(LOCK_FILE)
        print("[LOCK] Bot lock released")
    except:
        pass

# Проверяем блокировку при старте
if not acquire_lock():
    print("Exiting: another instance is running")
    sys.exit(1)

# Регистрируем освобождение блокировки при выходе
atexit.register(release_lock)
# ===== КОНЕЦ ЗАЩИТЫ =====

from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, CallbackQueryHandler, InlineQueryHandler, PreCheckoutQueryHandler, filters
from telegram import BotCommand, BotCommandScopeDefault, BotCommandScopeChat, InlineQueryResultArticle, InputTextMessageContent, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from io import BytesIO
from state import user_state
from utils import extract_text_from_url
from keyboards import gpt_model_kb, image_engine_kb, dalle_model_kb, dalle_size_kb, dalle_quality_kb, model_kb, format_kb, style_kb, confirm_kb, actions_kb, summary_kb, negative_prompt_kb, presets_main_kb, presets_list_kb, preset_actions_kb, packages_kb, payment_method_kb, edit_actions_kb, skip_kb, aspect_ratio_kb, fidelity_kb, style_guide_regenerate_kb, shot_kb, angle_kb, lighting_kb, additional_settings_kb, imagen_format_kb, subject_type_kb, reference_upload_kb
from dream_api import generate_dream
from dalle_api import generate_with_dalle
from dalle_gen_helper import generate_dalle_image
from imagen_api import generate_with_imagen
from imagen_gen_helper import generate_imagen_image
from imagen3_custom_helper import generate_imagen3_custom_image
from openai_helper import build_final_prompt, enhance_prompt_for_generation, translate_to_english
from style_transfer import apply_style_transfer
from style_guide import generate_with_style_guide
from sketch import generate_from_sketch
from user_limits import can_generate, use_generation, get_user_stats, get_all_users, add_generations, register_referral, reward_referrer, get_referral_stats
from image_library import add_to_history, get_user_history, get_favorites, toggle_favorite, search_history, get_history_stats, clear_history
from presets import create_preset, get_user_presets, get_preset, delete_preset
from watermark import add_watermark
from payments import get_all_packages_message, format_package_message, create_cryptobot_invoice, get_package_info, PACKAGES
from ai_tools import upscale_image, remove_background, create_variations, inpaint_image, restore_face, outpaint_image, search_and_recolor, search_and_replace, erase_object
from settings import TELEGRAM_BOT_TOKEN, WEBAPP_URL, USE_GCS
from gcs_helper import upload_image as gcs_upload_image
import gsheets_logger as gsl
import gcs_helper as gcs
import gcs_advanced as gcsa
from keyboards_addon import library_kb_extended, library_filters_kb, image_actions_kb, pagination_kb, export_options_kb, confirm_delete_kb

# ID администратора
ADMIN_ID = 65876198

async def upload_image_to_webapp(context, file_path_or_bytesio, user_id):
    """
    Загружает изображение на веб-сервер для Mini App
    Возвращает URL для открытия Mini App или None при ошибке
    Использует Google Cloud Storage если USE_GCS=True
    """
    import requests
    import base64
    from requests.exceptions import ConnectionError, Timeout

    try:
        # Читаем изображение
        if isinstance(file_path_or_bytesio, str):
            with open(file_path_or_bytesio, 'rb') as f:
                image_bytes = f.read()
        else:
            file_path_or_bytesio.seek(0)
            image_bytes = file_path_or_bytesio.read()

        # Если включен GCS - загружаем напрямую в Google Cloud Storage
        if USE_GCS:
            print(f"[INFO] Uploading image to Google Cloud Storage...")

            # Загружаем в GCS
            gcs_image_url = gcs_upload_image(
                image_bytes,
                folder="inpaint",
                filename=None,  # Автоматическая генерация имени
                content_type="image/png"
            )

            if gcs_image_url:
                # Формируем URL для Mini App с GCS изображением
                webapp_url = f"{WEBAPP_URL}/static/inpaint_editor.html?v=20251203094000&image={gcs_image_url}&user_id={user_id}"
                print(f"[OK] Image uploaded to GCS, webapp URL: {webapp_url}")
                return webapp_url
            else:
                print(f"[ERROR] Failed to upload image to GCS")
                return None

        # Иначе используем старый метод через веб-сервер
        # Конвертируем в base64
        image_b64 = base64.b64encode(image_bytes).decode('utf-8')
        image_data_url = f"data:image/png;base64,{image_b64}"

        print(f"[INFO] Uploading image to webapp: {WEBAPP_URL}")

        # Отправляем на веб-сервер
        response = requests.post(
            f"{WEBAPP_URL}/upload_image",
            json={
                'user_id': str(user_id),
                'image': image_data_url
            },
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()
            token = data['token']
            image_url = f"{WEBAPP_URL}{data['url']}"

            # Формируем URL для Mini App
            webapp_url = f"{WEBAPP_URL}/static/inpaint_editor.html?v=20251203094000&image={image_url}&user_id={user_id}"
            print(f"[OK] Image uploaded successfully, webapp URL: {webapp_url}")
            return webapp_url
        else:
            print(f"[ERROR] Failed to upload image to webapp: {response.status_code}")
            print(f"[ERROR] Response: {response.text}")
            return None

    except ConnectionError as e:
        print(f"[ERROR] Cannot connect to webapp server at {WEBAPP_URL}")
        print(f"[ERROR] Make sure webapp_server.py is running!")
        print(f"[ERROR] Details: {e}")
        return None
    except Timeout as e:
        print(f"[ERROR] Webapp server timeout: {e}")
        return None
    except Exception as e:
        print(f"[ERROR] Exception uploading image to webapp: {e}")
        import traceback
        traceback.print_exc()
        return None

async def setup_commands(application):
    """Настраивает меню команд для обычных пользователей и админа"""

    # Команды для обычных пользователей
    user_commands = [
        BotCommand("start", "Начать работу с ботом"),
        BotCommand("new", "Создать новое изображение"),
        BotCommand("editmy", "Редактировать мое изображение"),
        BotCommand("styletransfer", "Перенос стиля между изображениями"),
        BotCommand("styleguide", "Генерация по стилю референса"),
        BotCommand("sketch", "Генерация из наброска"),
        BotCommand("profile", "Мой профиль и статистика"),
        BotCommand("buy", "Купить генерации"),
        BotCommand("presets", "Управление пресетами параметров"),
        BotCommand("help", "Справка и помощь"),
        BotCommand("lib", "Библиотека изображений"),
    ]

    # Команды для админа (включают все обычные + админские)
    admin_commands = user_commands + [
        BotCommand("admin_users", "📊 Список всех пользователей"),
        BotCommand("admin_add", "➕ Добавить генерации пользователю"),
    ]

    # Устанавливаем команды для обычных пользователей (по умолчанию)
    await application.bot.set_my_commands(user_commands, scope=BotCommandScopeDefault())

    # Устанавливаем команды для админа
    await application.bot.set_my_commands(admin_commands, scope=BotCommandScopeChat(chat_id=ADMIN_ID))

async def start(update, context):
    uid = update.effective_user.id
    user = update.effective_user

    # Логируем пользователя в Google Sheets
    referrer_id = None
    if context.args:
        try:
            referrer_id = int(context.args[0])
        except:
            pass

    gsl.log_user(
        user_id=uid,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name or "",
        language=user.language_code or "ru",
        referrer_id=referrer_id
    )

    # Обработка реферальной ссылки
    if context.args:
        try:
            referrer_id = int(context.args[0])
            if register_referral(uid, referrer_id):
                # Логируем реферала
                gsl.log_referral(
                    referrer_id=referrer_id,
                    referrer_username="",  # Получим позже
                    referred_id=uid,
                    referred_username=user.username or "",
                    reward=0  # Награда будет после первой генерации
                )
                await update.message.reply_text(
                    "🎉 Вы зарегистрированы по реферальной ссылке!\n\n"
                    "Когда вы создадите первое изображение, ваш друг получит +5 бесплатных генераций!"
                )
        except:
            pass  # Невалидный реферальный код

    welcome_msg = """👋 Привет! Я бот для генерации изображений с AI.

🎨 <b>Как пользоваться:</b>
• Отправь текст - создам изображение по описанию
• Отправь ссылку - создам обложку к статье
• Отправь фото - использую как референс

⚡️ <b>Выбери параметры:</b>
1. Модель SD 3.5 (Large, Turbo, Medium, Flash)
2. Формат изображения (1:1, 16:9, 9:16 и др.)

🤖 <b>Используется:</b>
• Stable Diffusion 3.5 для генерации
• ChatGPT-4o для обработки промптов
• Автоматический перевод на английский

💎 <b>Лимит:</b> 10 бесплатных генераций
🎁 <b>Бонус:</b> Приглашай друзей и получай +5 генераций за каждого!

📋 <b>Команды:</b>
/new - Начать новое изображение
/styletransfer - Перенос стиля между изображениями
/styleguide - Генерация по стилю referencer
/sketch - Генерация из наброска
/help - Помощь
/profile - Мой профиль и реферальная ссылка
/lib - Библиотека изображений"""

    await update.message.reply_text(welcome_msg, parse_mode="HTML")

    # Логируем активность
    gsl.log_activity(
        user_id=uid,
        username=user.username or "",
        action="/start",
        details="Bot started",
        success=True
    )

async def new_image(update, context):
    """Команда /new - начать новое изображение"""
    uid = update.effective_user.id
    user_state.pop(uid, None)
    await update.message.reply_text(
        "🆕 Готов к созданию нового изображения!\n\n"
        "Пришли текст, ссылку или фото с описанием.\n\n"
        "<i>Например:</i>\n"
        "<blockquote>Создайте сверхреалистичное групповое селфи, как будто оно было снято фронтальной камерой смартфона. "
        "Мужчина с короткой стрижкой в белом деловом костюме находится в центре, в окружении классических персонажей фильмов ужасов: "
        "Фредди Крюгера, Джейсона Вурхиза, Майкла Майерса, Пеннивайза, Призрачного Лица, Чаки и Самары Морган. "
        "Все персонажи в кадре появляются очень близко друг к другу, некоторые наклоняются вперед, словно на непринужденном селфи.</blockquote>",
        parse_mode="HTML"
    )

async def editmy_command(update, context):
    """Команда /editmy - редактировать загруженное изображение"""
    uid = update.effective_user.id
    user_state[uid] = {"mode": "editmy"}
    await update.message.reply_text(
        "🖼️ <b>Редактирование изображения</b>\n\n"
        "Загрузите изображение, которое хотите отредактировать.\n\n"
        "Доступные операции:\n"
        "• 🔍 Upscale - увеличение разрешения\n"
        "• 🖌️ Remove BG - удаление фона\n"
        "• 👤 Face Restore - улучшение лиц\n"
        "• 🎨 Inpaint - редактирование частей\n"
        "• 🖼️ Outpaint - расширение изображения\n"
        "• 🎨 Search & Recolor - поиск и перекраска\n"
        "• 🔄 Search & Replace - поиск и замена\n"
        "• 🗑️ Erase - удаление объектов",
        parse_mode="HTML"
    )

async def help_command(update, context):
    """Команда /help - открыть полную справку в Mini App"""
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup

    help_msg = """📖 <b>Справка по Image Gen Bot</b>

🎨 Бот для создания изображений с AI
🤖 Работает на Stable Diffusion 3.5 и ChatGPT-4o

<b>Как создать изображение:</b>
1. Отправь текст или ссылку
2. Выбери модель SD 3.5
3. Выбери формат изображения
4. Нажми "Создать"

<b>Команды:</b>
/new - Генерация с параметрами
/styletransfer - Перенос стиля
/styleguide - Генерация в стиле
/sketch - Из наброска в детали
/presets - Управление пресетами
/lib - Библиотека изображений

💎 <b>Лимит:</b> 10 бесплатных генераций

📱 Нажмите кнопку ниже для полной справки с примерами и подробными инструкциями!"""

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(
            "📚 Открыть полную справку",
            web_app={"url": "https://tools.uspeshnyy.ru/imagegenbot/help.html"}
        )]
    ])

    await update.message.reply_text(help_msg, reply_markup=keyboard, parse_mode="HTML")

async def profile_command(update, context):
    """Команда /profile - показать профиль пользователя"""
    uid = update.effective_user.id
    username = update.effective_user.username or "Неизвестно"
    first_name = update.effective_user.first_name or ""

    # Получаем статистику генераций
    stats = get_user_stats(uid)
    used = stats["used"]
    remaining = stats["remaining"]
    first_gen = stats["first_generation"]

    # Получаем статистику рефералов
    ref_stats = get_referral_stats(uid)

    # Получаем имя бота для реферальной ссылки
    bot_username = (await context.bot.get_me()).username
    referral_link = f"https://t.me/{bot_username}?start={uid}"

    profile_msg = f"""👤 <b>Профиль</b>

<b>Имя:</b> {first_name}
<b>Username:</b> @{username}
<b>ID:</b> {uid}

📊 <b>Статистика генераций:</b>
💎 Использовано: {used} из 10
💎 Осталось: {remaining}"""

    if first_gen:
        profile_msg += f"\n📅 Первая генерация: {first_gen}"

    profile_msg += f"""

🎁 <b>Реферальная программа:</b>
👥 Приглашено друзей: {ref_stats['referrals_count']}
✅ Сделали генерацию: {ref_stats['referrals_with_generations']}
💰 Заработано генераций: {ref_stats['referrals_with_generations'] * 5}

🔗 <b>Ваша реферальная ссылка:</b>
{referral_link}

<i>Приглашайте друзей и получайте +5 генераций за каждого, кто создаст хотя бы одно изображение!</i>"""

    profile_msg += "\n\n🎨 <b>Текущий проект:</b>\n"

    # Проверяем, есть ли активный промпт
    if uid in user_state and user_state[uid].get("prompt"):
        st = user_state[uid]
        profile_msg += f"Промпт: {st['prompt'][:50]}..."
    else:
        profile_msg += "Нет активного проекта"

    await update.message.reply_text(profile_msg, parse_mode="HTML")



async def expiry_command(update, context):
    """Показать изображения близкие к удалению (осталось < 7 дней)"""
    uid = update.effective_user.id

    try:
        # Получаем изображения близкие к удалению
        images = gcsa.get_images_near_expiry(uid, days_before=7)

        if not images:
            await update.message.reply_text(
                '✅ <b>Нет изображений близких к удалению</b>\n\nВсе ваши изображения будут храниться ещё долго!\n\n<i>Изображения хранятся 60 дней</i>',
                parse_mode='HTML'
            )
            return

        # Формируем сообщение
        msg = f'⚠️ <b>Изображения близкие к удалению</b>\n\n'
        msg += f'Найдено: {len(images)} изображений\n\n'

        for i, img in enumerate(images[:10], 1):
            name = img['name'][:30]  # Обрезаем длинные имена
            days_left = img.get('days_until_deletion', 'N/A')
            msg += f'{i}. <code>{name}</code>\n'
            msg += f'   ⏰ Осталось: {days_left} дн.\n\n'

        if len(images) > 10:
            msg += f'\n<i>...и ещё {len(images) - 10} изображений</i>\n'

        msg += '\n💡 <b>Совет:</b> Экспортируйте изображения через /lib → 📦 Экспорт'

        await update.message.reply_text(msg, parse_mode='HTML')

    except Exception as e:
        await update.message.reply_text(f'❌ Ошибка: {e}')

async def prompts_command(update, context):
    """Показать историю промптов пользователя"""
    uid = update.effective_user.id

    try:
        # Получаем все изображения пользователя с метаданными
        images = gcsa.get_user_images_filtered(uid, limit=1000)

        # Собираем промпты
        prompts_list = []
        for img in images:
            metadata = img.get('metadata', {})
            if metadata.get('prompt'):
                prompts_list.append({
                    'prompt': metadata['prompt'],
                    'name': img['name'],
                    'time_created': img.get('time_created', '')
                })

        if not prompts_list:
            await update.message.reply_text(
                '📝 <b>История промптов пуста</b>\n\nСоздайте изображения, чтобы увидеть историю промптов',
                parse_mode='HTML'
            )
            return

        # Сортируем по времени создания (новые первые)
        prompts_list.sort(key=lambda x: x['time_created'], reverse=True)

        # Формируем сообщение с последними 20 промптами
        msg = '📝 <b>История промптов</b>\n\n'
        for i, item in enumerate(prompts_list[:20], 1):
            prompt = item['prompt'][:100]  # Обрезаем длинные промпты
            msg += f'{i}. <code>{prompt}</code>\n'
            if len(item['prompt']) > 100:
                msg += f'   <i>...ещё {len(item["prompt"]) - 100} символов</i>\n'
            msg += '\n'

        total = len(prompts_list)
        if total > 20:
            msg += f'\n<i>Показано 20 из {total} промптов</i>'

        await update.message.reply_text(msg, parse_mode='HTML')

    except Exception as e:
        await update.message.reply_text(f'❌ Ошибка: {e}')

async def library_command(update, context):
    """Команда /lib - показать библиотеку изображений из GCS (расширенная версия)"""
    uid = update.effective_user.id

    # Получаем статистику из GCS
    stats = gcs.get_user_stats(uid)

    # Получаем статистику избранного
    try:
        fav_images = gcsa.get_user_images_filtered(uid, category='favorites', limit=1000)
        fav_count = len(fav_images)
    except:
        fav_count = 0

    if stats['total'] == 0 and fav_count == 0:
        lib_msg = '''📚 <b>Библиотека изображений</b>

Ваша библиотека пуста. Создайте первое изображение!

💡 Используйте /new для создания'''
        await update.message.reply_text(lib_msg, parse_mode='HTML')
        return

    lib_msg = f'''📚 <b>Библиотека изображений</b>

📊 <b>Статистика:</b>
🎨 Созданные: {stats['generated']}
📤 Загруженные: {stats['uploaded']}
✏️ Отредактированные: {stats['edited']}
⭐ Избранное: {fav_count}
━━━━━━━━━━━━━━━━━
📁 Всего: {stats['total']} изображений'''

    await update.message.reply_text(
        lib_msg,
        parse_mode='HTML',
        reply_markup=library_kb_extended()
    )

async def library_show_category(update, context, category=None):
    """Показать изображения из категории"""
    from telegram import InputMediaPhoto
    import gcs_helper as gcs
    
    query = update.callback_query
    await query.answer()
    
    uid = query.from_user.id
    
    # Определяем категорию
    if query.data == 'lib_show_generated':
        category = 'generated'
        cat_name = 'Созданные'
    elif query.data == 'lib_show_uploaded':
        category = 'uploaded'
        cat_name = 'Загруженные'
    elif query.data == 'lib_show_edited':
        category = 'edited'
        cat_name = 'Отредактированные'
    else:
        category = None
        cat_name = 'Все'
    
    # Получаем изображения
    images = gcs.get_user_images(uid, category=category, limit=10)
    
    if not images:
        await query.edit_message_text(
            f'📁 <b>{cat_name}</b>\n\nВ этой категории пока нет изображений.',
            parse_mode='HTML'
        )
        return
    
    # Формируем сообщение
    msg = f'📁 <b>{cat_name}</b>\n\nНайдено изображений: {len(images)}\n\nОтправляю последние 10...'
    await query.edit_message_text(msg, parse_mode='HTML')
    
    # Отправляем изображения (по 10 штук в media group)
    media_group = []
    for i, img in enumerate(images[:10]):
        try:
            media_group.append(InputMediaPhoto(media=img['url']))
            
            # Отправляем группами по 10
            if len(media_group) == 10 or i == len(images) - 1:
                await context.bot.send_media_group(
                    chat_id=uid,
                    media=media_group
                )
                media_group = []
        except Exception as e:
            print(f'[ERROR] Failed to send image: {e}')
    
    # Возвращаемся к главному меню библиотеки
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    keyboard = [
        [
            InlineKeyboardButton('🎨 Созданные', callback_data='lib_show_generated'),
            InlineKeyboardButton('📤 Загруженные', callback_data='lib_show_uploaded')
        ],
        [
            InlineKeyboardButton('✏️ Отредактированные', callback_data='lib_show_edited'),
            InlineKeyboardButton('📁 Все', callback_data='lib_show_all')
        ]
    ]
    
    await context.bot.send_message(
        chat_id=uid,
        text='✅ Изображения отправлены!\n\nВыберите другую категорию или вернитесь к главному меню.',
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )

async def presets_command(update, context):
    """Команда /presets - управление пресетами"""
    uid = update.effective_user.id

    user_presets = get_user_presets(uid)
    presets_count = len(user_presets)

    msg = f"""💾 <b>Управление пресетами</b>

Пресеты позволяют сохранять любимые комбинации параметров (модель + формат + стиль + negative prompt) для быстрого использования.

📌 <b>Ваши пресеты:</b> {presets_count}

💡 <b>Как использовать:</b>
• Сохраните текущие настройки
• Загрузите пресет при создании изображения
• Редактируйте и удаляйте пресеты"""

    await update.message.reply_text(
        msg,
        reply_markup=presets_main_kb(),
        parse_mode="HTML"
    )

async def buy_command(update, context):
    """Команда /buy - купить генерации"""
    uid = update.effective_user.id

    # Получаем текущий баланс
    stats = get_user_stats(uid)
    remaining = stats["remaining"]

    msg = f"""💎 <b>Купить генерации</b>

📊 <b>Ваш баланс:</b> {remaining} генераций

{get_all_packages_message()}"""

    await update.message.reply_text(
        msg,
        reply_markup=packages_kb(),
        parse_mode="HTML"
    )

async def admin_users_command(update, context):
    """Команда /admin_users - показать всех пользователей (только для админа)"""
    uid = update.effective_user.id

    if uid != ADMIN_ID:
        await update.message.reply_text("❌ У вас нет прав для использования этой команды.")
        return

    users = get_all_users()

    if not users:
        await update.message.reply_text("📊 Пока нет пользователей с генерациями.")
        return

    # Формируем список пользователей с кнопками
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    from datetime import datetime

    for user in users:
        user_id = int(user['user_id'])

        # Пытаемся получить информацию о пользователе из Telegram
        try:
            user_info = await context.bot.get_chat(user_id)
            username = f"@{user_info.username}" if user_info.username else "Нет username"
            full_name = user_info.full_name if user_info.full_name else "Нет имени"
        except:
            username = "Нет доступа"
            full_name = "Нет доступа"

        # Форматируем дату
        first_gen = user['first_generation']
        if first_gen != "Не было":
            try:
                dt = datetime.fromisoformat(first_gen)
                # Месяцы на русском
                months = ['января', 'февраля', 'марта', 'апреля', 'мая', 'июня',
                         'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря']
                date_str = f"{dt.day} {months[dt.month-1]} {dt.year} 🕑 {dt.hour:02d}:{dt.minute:02d}"
            except:
                date_str = first_gen
        else:
            date_str = "Не было"

        # Формируем сообщение
        msg = f"<b>ID:</b> {user_id} {username}\n"
        msg += f"{full_name}\n"
        msg += f"💎 Использовано: {user['used']} | Осталось: {user['remaining']}\n"
        msg += f"📅 Старт: {date_str}\n"
        msg += f"👥 Приглашено друзей: {user['referrals_count']}"

        # Создаем кнопки
        keyboard = []
        if user['remaining'] == 0:
            keyboard.append([InlineKeyboardButton("➕ 10 генераций", callback_data=f"admin_add10_{user_id}")])

        reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None

        # Отправляем сообщение с кнопками
        await update.message.reply_text(msg, parse_mode="HTML", reply_markup=reply_markup)

async def admin_add_command(update, context):
    """Команда /admin_add - добавить генерации пользователю (только для админа)
    Формат: /admin_add USER_ID AMOUNT
    """
    uid = update.effective_user.id

    if uid != ADMIN_ID:
        await update.message.reply_text("❌ У вас нет прав для использования этой команды.")
        return

    if len(context.args) != 2:
        await update.message.reply_text(
            "❌ Неправильный формат команды\n\n"
            "Используйте: /admin_add USER_ID AMOUNT\n"
            "Пример: /admin_add 123456789 50"
        )
        return

    try:
        target_user_id = int(context.args[0])
        amount = int(context.args[1])

        if amount <= 0:
            await update.message.reply_text("❌ Количество должно быть положительным числом.")
            return

        # Добавляем генерации
        remaining = add_generations(target_user_id, amount)

        await update.message.reply_text(
            f"✅ Пользователю {target_user_id} добавлено {amount} генераций\n"
            f"💎 Теперь доступно: {remaining} генераций"
        )

        # Отправляем уведомление пользователю
        try:
            await context.bot.send_message(
                chat_id=target_user_id,
                text=f"🎁 Админ дарит вам +{amount} бесплатных генераций!"
            )
        except Exception as e:
            print(f"[WARNING] Could not send notification to user {target_user_id}: {e}")

    except ValueError:
        await update.message.reply_text("❌ USER_ID и AMOUNT должны быть числами.")
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {str(e)}")

async def style_transfer_command(update, context):
    """Команда /styletransfer - начать процесс переноса стиля"""
    uid = update.effective_user.id

    # Очищаем состояние и инициализируем процесс style transfer
    user_state[uid]["style_transfer"] = {
        "active": True,
        "step": "init_image"
    }

    await update.message.reply_text(
        "🎨 <b>Style Transfer</b>\n\n"
        "<b>Шаг 1/2:</b> Загрузите исходное изображение, к которому нужно применить стиль.",
        parse_mode="HTML"
    )

async def style_guide_command(update, context):
    """Команда /styleguide - генерация изображения на основе стиля референса"""
    uid = update.effective_user.id

    # Очищаем состояние и инициализируем процесс style guide
    user_state[uid]["style_guide"] = {
        "active": True,
        "step": "style_image"
    }

    await update.message.reply_text(
        "🎨 <b>Style Guide</b>\n\n"
        "Загрузите изображение, стиль которого нужно использовать для генерации.",
        parse_mode="HTML"
    )

async def sketch_command(update, context):
    """Команда /sketch - генерация изображения из наброска"""
    uid = update.effective_user.id

    # Очищаем состояние и инициализируем процесс sketch
    user_state[uid]["sketch"] = {
        "active": True,
        "step": "sketch_image"
    }

    await update.message.reply_text(
        "✏️ <b>Sketch Control</b>\n\n"
        "Загрузите изображение наброска/скетча, который нужно использовать для генерации.",
        parse_mode="HTML"
    )

async def handle_message(update, context):
    uid = update.effective_user.id

    # Проверяем, ожидается ли промпт для inpaint
    if user_state.get(uid, {}).get("waiting_for_inpaint_prompt"):
        user_state[uid]["waiting_for_inpaint_prompt"] = False

        if not update.message.text:
            await update.message.reply_text("❌ Пожалуйста, отправьте текстовое описание")
            user_state[uid]["waiting_for_inpaint_prompt"] = True
            return

        prompt = update.message.text.strip()

        # Проверяем наличие маски и изображения
        if not user_state[uid].get("inpaint_mask") or not user_state[uid].get("edit_image"):
            await update.message.reply_text("❌ Нет маски или изображения для inpainting")
            return

        await update.message.reply_text("⏳ <b>Обработка изображения...</b>\n\nЭто может занять до минуты.", parse_mode="HTML")

        # Выполняем inpaint
        result = inpaint_image(
            user_state[uid]["edit_image"],
            user_state[uid]["inpaint_mask"],
            prompt
        )

        if isinstance(result, str):
            # Ошибка
            await update.message.reply_text(result)
        else:
            # Успех - отправляем отредактированное изображение
            watermarked = add_watermark(result)

        # Сохраняем отредактированное изображение в библиотеку
        if USE_GCS and result:
            try:
                gcs.save_user_image(uid, result, category='edited')
                print(f'[GCS] Edited image saved to library')
            except Exception as e:
                print(f'[ERROR] Failed to save edited image: {e}')
            await context.bot.send_photo(uid, watermarked)
            await context.bot.send_message(
                uid,
                f"✅ <b>Inpainting завершен!</b>\n\n🎨 Промпт: <code>{prompt}</code>",
                parse_mode="HTML",
                reply_markup=actions_kb()
            )

        # Очищаем состояние
        user_state[uid].pop("inpaint_mask", None)
        user_state[uid].pop("waiting_for_inpaint_mask", None)
        return

    # Обработка добавления тегов
    if user_state.get(uid, {}).get("awaiting_tags_for"):
        blob_name = user_state[uid].pop("awaiting_tags_for")

        if not update.message.text:
            await update.message.reply_text("❌ Отправьте текстовые теги")
            return

        tags = update.message.text.strip().split()

        try:
            success = gcsa.add_tags_to_image(uid, blob_name, tags)
            if success:
                tags_str = ', '.join(tags)
                await update.message.reply_text(f"✅ Добавлено тегов: {tags_str}")
            else:
                await update.message.reply_text("❌ Ошибка добавления тегов")
        except Exception as e:
            await update.message.reply_text(f"❌ Ошибка: {e}")
        return

    # Проверяем, используется ли Imagen 3 Custom - обработка загрузки референсных фото
    if user_state.get(uid, {}).get("engine") == "imagen3_custom" and update.message.photo:
        # Скачиваем фото
        photo = update.message.photo[-1]  # Берём самое большое
        file = await photo.get_file()

        # Загружаем в BytesIO
        photo_bytes = await file.download_as_bytearray()
        photo_io = BytesIO(photo_bytes)
        photo_io.seek(0)

        # Добавляем в список референсов
        if "reference_images" not in user_state[uid]:
            user_state[uid]["reference_images"] = []

        user_state[uid]["reference_images"].append(photo_io)

        num_refs = len(user_state[uid]["reference_images"])

        await update.message.reply_text(
            f"✅ Фото {num_refs}/4 загружено!\n\n"
            f"{'📤 Отправьте еще фото (макс 4) или ' if num_refs < 4 else ''}"
            f"💬 Введите промпт для генерации\n\n"
            f"<i>Используйте [1], [2]... в промпте для ссылки на фото</i>",
            reply_markup=reference_upload_kb(),
            parse_mode="HTML"
        )
        return

    # Проверяем режим /editmy
    if user_state.get(uid, {}).get("mode") == "editmy" and update.message.photo:
        # Загружаем фото
        file = await update.message.photo[-1].get_file()
        photo_bytes = await file.download_as_bytearray()
        photo_io = BytesIO(photo_bytes)
        photo_io.seek(0)

        # Сохраняем изображение в состоянии
        user_state[uid]["edit_image"] = photo_io

        # Сохраняем загруженное изображение в библиотеку
        if USE_GCS:
            try:
                photo_io.seek(0)
                gcs.save_user_image(uid, photo_io, category='uploaded')
                print(f'[GCS] Uploaded image saved to library')
            except Exception as e:
                print(f'[ERROR] Failed to save uploaded image: {e}')

        user_state[uid]["mode"] = None

        # Показываем кнопки действий
        await update.message.reply_text(
            "✅ Изображение загружено!\n\n"
            "Выберите операцию для редактирования:",
            reply_markup=edit_actions_kb()
        )
        return

    # Проверяем, активен ли процесс Style Transfer
    if user_state[uid].get("style_transfer", {}).get("active"):
        st_state = user_state[uid]["style_transfer"]

        # Обработка загрузки init_image
        if st_state["step"] == "init_image" and update.message.photo:
            file = await update.message.photo[-1].get_file()
            downloaded_file = await file.download_to_drive()
            st_state["init_image"] = downloaded_file
            st_state["step"] = "style_image"
            await update.message.reply_text(
                "✅ Исходное изображение получено!\n\n"
                "<b>Шаг 2/2:</b> Теперь загрузите изображение, стиль которого нужно скопировать.",
                parse_mode="HTML"
            )
            return

        # Обработка загрузки style_image
        if st_state["step"] == "style_image" and update.message.photo:
            file = await update.message.photo[-1].get_file()
            downloaded_file = await file.download_to_drive()
            st_state["style_image"] = downloaded_file
            st_state["step"] = "prompt"
            await update.message.reply_text(
                "✅ Изображение стиля получено!\n\n"
                "Теперь введите параметры:\n\n"
                "<b>Prompt</b> (текстовое описание, можно оставить пустым):\n"
                "Отправьте текст или '-' для пропуска.",
                parse_mode="HTML"
            )
            return

        # Обработка текстовых параметров
        if st_state["step"] == "prompt":
            text = update.message.text.strip()
            # Если пустой промпт, используем дефолтный
            st_state["prompt"] = text if text and text != "-" else "high quality image"
            st_state["step"] = "negative_prompt"
            await update.message.reply_text(
                "<b>Negative Prompt</b> (что исключить, можно оставить пустым):\n"
                "Отправьте текст или '-' для пропуска.",
                parse_mode="HTML"
            )
            return

        if st_state["step"] == "negative_prompt":
            text = update.message.text.strip()
            st_state["negative_prompt"] = "" if text == "-" else text
            st_state["step"] = "style_strength"
            await update.message.reply_text(
                "<b>Style Strength</b> (сила применения стиля, 0.1-1.0):\n"
                "Пример: 0.8",
                parse_mode="HTML"
            )
            return

        if st_state["step"] == "style_strength":
            try:
                value = float(update.message.text.strip())
                if 0.1 <= value <= 1.0:
                    st_state["style_strength"] = value
                    st_state["step"] = "composition_fidelity"
                    await update.message.reply_text(
                        "<b>Composition Fidelity</b> (точность композиции, 0.1-1.0):\n"
                        "Пример: 0.9",
                        parse_mode="HTML"
                    )
                    return
                else:
                    await update.message.reply_text("❌ Значение должно быть от 0.1 до 1.0")
                    return
            except:
                await update.message.reply_text("❌ Введите число от 0.1 до 1.0")
                return

        if st_state["step"] == "composition_fidelity":
            try:
                value = float(update.message.text.strip())
                if 0.1 <= value <= 1.0:
                    st_state["composition_fidelity"] = value
                    st_state["step"] = "change_strength"
                    await update.message.reply_text(
                        "<b>Change Strength</b> (сила изменений, 0.1-1.0):\n"
                        "Пример: 0.9",
                        parse_mode="HTML"
                    )
                    return
                else:
                    await update.message.reply_text("❌ Значение должно быть от 0.1 до 1.0")
                    return
            except:
                await update.message.reply_text("❌ Введите число от 0.1 до 1.0")
                return

        if st_state["step"] == "change_strength":
            try:
                value = float(update.message.text.strip())
                if 0.1 <= value <= 1.0:
                    st_state["change_strength"] = value

                    # Все параметры собраны, запускаем генерацию
                    await update.message.reply_text("⏳ Применение стиля...")

                    result = apply_style_transfer(
                        init_image_path=st_state["init_image"],
                        style_image_path=st_state["style_image"],
                        prompt=st_state.get("prompt", ""),
                        negative_prompt=st_state.get("negative_prompt", ""),
                        style_strength=st_state.get("style_strength", 1.0),
                        composition_fidelity=st_state.get("composition_fidelity", 0.9),
                        change_strength=st_state.get("change_strength", 0.9)
                    )

                    if isinstance(result, str):
                        # Ошибка
                        await update.message.reply_text(f"❌ {result}")
                    else:
                        # Успех - отправляем изображение с watermark
                        watermarked_image = add_watermark(result)
                        await context.bot.send_photo(uid, watermarked_image)
                        await context.bot.send_message(uid, "✅ Style Transfer завершен!")

                    # Очищаем состояние
                    user_state[uid]["style_transfer"] = {"active": False}
                    return
                else:
                    await update.message.reply_text("❌ Значение должно быть от 0.1 до 1.0")
                    return
            except:
                await update.message.reply_text("❌ Введите число от 0.1 до 1.0")
                return

    # Проверяем, активен ли процесс Style Guide
    if user_state[uid].get("style_guide", {}).get("active"):
        sg_state = user_state[uid]["style_guide"]

        # Обработка загрузки style_image
        if sg_state["step"] == "style_image" and update.message.photo:
            file = await update.message.photo[-1].get_file()
            downloaded_file = await file.download_to_drive()
            sg_state["style_image"] = downloaded_file
            sg_state["step"] = "prompt"
            await update.message.reply_text(
                "✅ Изображение стиля получено!\n\n"
                "Теперь введите <b>Prompt</b> (текстовое описание того, что нужно сгенерировать):",
                parse_mode="HTML"
            )
            return

        # Обработка текстовых параметров
        if sg_state["step"] == "prompt":
            if not update.message.text:
                await update.message.reply_text("❌ Отправьте текстовое сообщение с промптом!")
                return
            text = update.message.text.strip()
            if not text or text == "-":
                await update.message.reply_text("❌ Prompt обязателен для Style Guide!")
                return
            sg_state["prompt"] = text
            sg_state["step"] = "negative_prompt"
            await update.message.reply_text(
                "<b>Negative Prompt</b> (что исключить, можно оставить пустым):",
                parse_mode="HTML",
                reply_markup=skip_kb()
            )
            return

        if sg_state["step"] == "negative_prompt":
            if not update.message.text:
                await update.message.reply_text("❌ Отправьте текстовое сообщение или '-' для пропуска!")
                return
            text = update.message.text.strip()
            sg_state["negative_prompt"] = "" if text == "-" else text
            sg_state["step"] = "aspect_ratio"
            await update.message.reply_text(
                "<b>Aspect Ratio</b> (формат изображения):",
                parse_mode="HTML",
                reply_markup=aspect_ratio_kb()
            )
            return

        if sg_state["step"] == "aspect_ratio":
            if not update.message.text:
                await update.message.reply_text("❌ Отправьте текстовое сообщение с форматом!")
                return
            text = update.message.text.strip()
            valid_ratios = ["1:1", "21:9", "16:9", "3:2", "5:4", "4:5", "2:3", "9:16", "9:21"]
            if text in valid_ratios:
                sg_state["aspect_ratio"] = text
                sg_state["step"] = "fidelity"
                await update.message.reply_text(
                    "<b>Fidelity</b> (точность следования стилю, 0.1-1.0):\n"
                    "Выберите или введите свое значение",
                    parse_mode="HTML",
                    reply_markup=fidelity_kb()
                )
                return
            else:
                await update.message.reply_text(f"❌ Выберите один из: {', '.join(valid_ratios)}")
                return

        if sg_state["step"] == "fidelity":
            if not update.message.text:
                await update.message.reply_text("❌ Отправьте число от 0.1 до 1.0!")
                return
            try:
                value = float(update.message.text.strip())
                if 0.1 <= value <= 1.0:
                    sg_state["fidelity"] = value

                    # Все параметры собраны, запускаем генерацию
                    await update.message.reply_text("⏳ Генерация изображения в стиле референса...")

                    result = generate_with_style_guide(
                        image_path=sg_state["style_image"],
                        prompt=sg_state["prompt"],
                        negative_prompt=sg_state.get("negative_prompt", ""),
                        aspect_ratio=sg_state.get("aspect_ratio", "1:1"),
                        fidelity=sg_state.get("fidelity", 0.5)
                    )

                    if isinstance(result, str):
                        # Ошибка
                        await update.message.reply_text(f"❌ {result}")
                    else:
                        # Успех - отправляем изображение с watermark
                        watermarked_image = add_watermark(result)
                        await context.bot.send_photo(uid, watermarked_image)

                        # Сохраняем параметры для возможности повторной генерации
                        user_state[uid]["last_sg_params"] = {
                            "style_image": sg_state["style_image"],
                            "prompt": sg_state["prompt"],
                            "negative_prompt": sg_state.get("negative_prompt", ""),
                            "aspect_ratio": sg_state.get("aspect_ratio", "1:1"),
                            "fidelity": sg_state.get("fidelity", 0.5)
                        }

                        await context.bot.send_message(
                            uid,
                            "✅ Style Guide генерация завершена!",
                            reply_markup=style_guide_regenerate_kb()
                        )

                    # Очищаем состояние
                    user_state[uid]["style_guide"] = {"active": False}
                    return
                else:
                    await update.message.reply_text("❌ Значение должно быть от 0.1 до 1.0")
                    return
            except:
                await update.message.reply_text("❌ Введите число от 0.1 до 1.0")
                return

    # Проверяем, активен ли процесс Sketch
    if user_state[uid].get("sketch", {}).get("active"):
        sk_state = user_state[uid]["sketch"]

        # Обработка загрузки sketch_image
        if sk_state["step"] == "sketch_image" and update.message.photo:
            file = await update.message.photo[-1].get_file()
            downloaded_file = await file.download_to_drive()
            sk_state["sketch_image"] = downloaded_file
            sk_state["step"] = "prompt"
            await update.message.reply_text(
                "✅ Набросок получен!\n\n"
                "Теперь введите <b>Prompt</b> (описание того, что должно быть на изображении):",
                parse_mode="HTML"
            )
            return

        # Обработка текстовых параметров
        if sk_state["step"] == "prompt":
            if not update.message.text:
                await update.message.reply_text("❌ Отправьте текстовое сообщение с промптом!")
                return
            text = update.message.text.strip()
            if not text or text == "-":
                await update.message.reply_text("❌ Prompt обязателен для Sketch!")
                return
            sk_state["prompt"] = text
            sk_state["step"] = "negative_prompt"
            await update.message.reply_text(
                "<b>Negative Prompt</b> (что исключить, можно оставить пустым):\n"
                "Отправьте текст или '-' для пропуска.",
                parse_mode="HTML"
            )
            return

        if sk_state["step"] == "negative_prompt":
            if not update.message.text:
                await update.message.reply_text("❌ Отправьте текстовое сообщение или '-' для пропуска!")
                return
            text = update.message.text.strip()
            sk_state["negative_prompt"] = "" if text == "-" else text
            sk_state["step"] = "control_strength"
            await update.message.reply_text(
                "<b>Control Strength</b> (сила следования наброску, 0.1-1.0):\n"
                "Пример: 0.5",
                parse_mode="HTML"
            )
            return

        if sk_state["step"] == "control_strength":
            if not update.message.text:
                await update.message.reply_text("❌ Отправьте число от 0.1 до 1.0!")
                return
            try:
                value = float(update.message.text.strip())
                if 0.1 <= value <= 1.0:
                    sk_state["control_strength"] = value

                    # Все параметры собраны, запускаем генерацию
                    await update.message.reply_text("⏳ Генерация изображения из наброска...")

                    result = generate_from_sketch(
                        image_path=sk_state["sketch_image"],
                        prompt=sk_state["prompt"],
                        negative_prompt=sk_state.get("negative_prompt", ""),
                        control_strength=sk_state.get("control_strength", 0.5)
                    )

                    if isinstance(result, str):
                        # Ошибка
                        await update.message.reply_text(f"❌ {result}")
                    else:
                        # Успех - отправляем изображение с watermark
                        watermarked_image = add_watermark(result)
                        await context.bot.send_photo(uid, watermarked_image)
                        await context.bot.send_message(uid, "✅ Генерация из наброска завершена!")

                    # Очищаем состояние
                    user_state[uid]["sketch"] = {"active": False}
                    return
                else:
                    await update.message.reply_text("❌ Значение должно быть от 0.1 до 1.0")
                    return
            except:
                await update.message.reply_text("❌ Введите число от 0.1 до 1.0")
                return

    # Обработка загрузки маски для inpainting
    if update.message.photo and user_state[uid].get("waiting_for_inpaint_mask"):
        # Получаем файл маски
        file = await update.message.photo[-1].get_file()
        mask_bytes = await file.download_as_bytearray()
        mask_io = BytesIO(mask_bytes)

        # Сохраняем маску
        user_state[uid]["inpaint_mask"] = mask_io
        user_state[uid]["waiting_for_inpaint_mask"] = False
        user_state[uid]["waiting_for_inpaint_prompt"] = True

        await update.message.reply_text(
            "✅ <b>Маска получена!</b>\n\n"
            "📝 Теперь отправьте текстовое описание того, что должно быть на месте белых областей маски.\n\n"
            "Пример: <code>красивый цветок</code> или <code>синее небо с облаками</code>",
            parse_mode="HTML"
        )
        return

    # Обработка промпта для inpainting
    if update.message.text and user_state[uid].get("waiting_for_inpaint_prompt"):
        inpaint_prompt = update.message.text.strip()
        user_state[uid]["waiting_for_inpaint_prompt"] = False

        st = user_state[uid]

        if not st.get("last_image") or not st.get("inpaint_mask"):
            await update.message.reply_text("❌ Ошибка: нет изображения или маски")
            return

        await update.message.reply_text("⏳ <b>Inpainting...</b>\n\n🎨 Обрабатываем изображение...", parse_mode="HTML")

        # Выполняем inpainting
        result = inpaint_image(st["last_image"], st["inpaint_mask"], prompt=inpaint_prompt)

        if isinstance(result, str):
            # Ошибка
            await update.message.reply_text(result)
        else:
            # Успех
            watermarked = add_watermark(result)

        # Сохраняем отредактированное изображение в библиотеку
        if USE_GCS and result:
            try:
                gcs.save_user_image(uid, result, category='edited')
                print(f'[GCS] Edited image saved to library')
            except Exception as e:
                print(f'[ERROR] Failed to save edited image: {e}')
            await context.bot.send_photo(uid, watermarked)
            await update.message.reply_text(
                f"✅ <b>Inpainting завершен!</b>\n\n"
                f"🎨 Промпт: <code>{inpaint_prompt}</code>",
                parse_mode="HTML",
                reply_markup=actions_kb()
            )

            # Сохраняем результат для дальнейших операций
            user_state[uid]["last_image"] = result

        # Очищаем маску
        user_state[uid]["inpaint_mask"] = None
        return

    # Обычная обработка для генерации изображений
    if update.message.photo:
        file = await update.message.photo[-1].get_file()
        user_state[uid]["images"].append(file.file_path)
        await update.message.reply_text("Фото добавлено! Теперь пришли текст.")
        return

    text = update.message.text.strip()

    # Проверяем, находится ли пользователь в режиме refinement
    if user_state[uid].get("in_refinement_mode"):
        # Проверяем лимит генераций
        can_gen, remaining_check = can_generate(uid)
        if not can_gen:
            await update.message.reply_text(
                "❌ Вы исчерпали лимит бесплатных генераций (10 шт).\n"
                "Свяжитесь с поддержкой для продления."
            )
            return

        st = user_state[uid]

        # Обновляем оригинальный промпт на русском
        user_state[uid]["prompt"] = text
        user_state[uid]["in_refinement_mode"] = False

        if not st.get("saved_params"):
            await update.message.reply_text("❌ Нет сохраненных параметров. Используйте /new для создания нового изображения.")
            return

        await update.message.reply_text("⏳ Обработка промпта с помощью ChatGPT...")

        # Переводим новый промпт и генерируем
        gpt_model = user_state[uid].get("gpt_model", "gpt-4o")
        final_english_prompt = build_final_prompt(text, st["saved_params"], gpt_model)

        await update.message.reply_text("⏳ Генерация изображения...")

        # Переводим negative prompt на английский если он есть
        english_negative = ""
        if st.get("negative_prompt"):
            english_negative = translate_to_english(st["negative_prompt"], gpt_model)

        images = st["images"]
        output = generate_dream(final_english_prompt, images, format_ratio=st["saved_params"]["format"], model=st["saved_params"]["model"], style=st["saved_params"].get("style"), negative_prompt=english_negative)

        last_generated = None
        for item in output:
            try:
                # Добавляем watermark
                watermarked_image = add_watermark(item)
                await context.bot.send_photo(uid, watermarked_image)
                last_generated = item  # Сохраняем оригинал для AI функций
            except:
                await context.bot.send_message(uid, item)

        # Используем одну генерацию
        remaining = use_generation(uid)

        # Сохраняем в библиотеку
        add_to_history(
            user_id=uid,
            prompt=text,
            english_prompt=final_english_prompt,
            params=st["saved_params"],
            negative_prompt=st.get("negative_prompt", "")
        )

        # Сохраняем новый промпт, последнее изображение и снова включаем режим refinement
        user_state[uid]["last_english_prompt"] = final_english_prompt
        user_state[uid]["last_image"] = last_generated  # Для Upscale, Variations, Remove BG

        # Сохраняем в GCS библиотеку
        if USE_GCS and last_generated:
            try:
                gcs.save_user_image(uid, last_generated, category='generated')
                # Сохраняем метаданные
                try:
                    images = gcsa.get_user_images_filtered(uid, category='generated', limit=1)
                    if images:
                        blob_name = images[0]['blob_name']
                        metadata = {'operation_type': 'generation'}
                        if 'prompt' in locals():
                            metadata['prompt'] = prompt
                        elif 'final_prompt' in locals():
                            metadata['prompt'] = final_prompt
                        gcsa.save_image_metadata(uid, blob_name, metadata)
                except Exception as e:
                    print(f'[ERROR] Failed to save metadata: {e}')
                print(f'[GCS] Image saved to user library')
            except Exception as e:
                print(f'[ERROR] Failed to save to library: {e}')
        user_state[uid]["in_refinement_mode"] = True

        await context.bot.send_message(
            uid,
            f"✅ Изображение готово\n\n<code>{final_english_prompt}</code>\n\n💎 Осталось генераций: {remaining}",
            parse_mode="HTML",
            reply_markup=actions_kb()
        )
        return

    # Проверяем, редактирует ли пользователь промпт после выбора параметров
    if user_state[uid].get("awaiting_edit"):
        user_state[uid]["prompt"] = text
        user_state[uid]["awaiting_edit"] = False

        # Показываем обновленный промпт с кнопками подтверждения
        st = user_state[uid]
        final_prompt = f"""{st['prompt']}

Format: {st['format']}
Shot: {st['shot']}
Camera angle: {st['angle']}
Style: {st['style']}
Lighting: {st['lighting']}
Quality: {st['quality']}"""

        await update.message.reply_text(
            f"📝 Обновленный промпт:\n\n{final_prompt}",
            reply_markup=confirm_kb()
        )
        return

    # Проверяем, редактирует ли пользователь саммари URL
    if user_state[uid].get("awaiting_summary_edit"):
        user_state[uid]["prompt"] = text
        user_state[uid]["awaiting_summary_edit"] = False

        # Показываем обновленное саммари с кнопками
        await update.message.reply_text(
            f"📝 Обновленное описание:\n\n{text}",
            reply_markup=summary_kb()
        )
        return

    # Проверяем, вводит ли пользователь negative prompt
    if user_state[uid].get("awaiting_negative_prompt"):
        user_state[uid]["awaiting_negative_prompt"] = False
        user_state[uid]["negative_prompt"] = text

        # Показываем финальный промпт (через небольшой хак для имитации query)
        from telegram import Update

        # Создаем текстовое сообщение вместо callback query
        await update.message.reply_text("✅ Negative prompt добавлен!")

        st = user_state[uid]
        format_ru = {
            "1:1": "1:1 (квадрат)",
            "21:9": "21:9 (ультра-широкий)",
            "16:9": "16:9 (горизонтально)",
            "3:2": "3:2",
            "5:4": "5:4",
            "4:5": "4:5",
            "2:3": "2:3",
            "9:16": "9:16 (вертикально)",
            "9:21": "9:21 (ультра-вертикально)"
        }

        model_ru = {
            "sd3.5-large": "SD 3.5 Large",
            "sd3.5-large-turbo": "SD 3.5 Large Turbo",
            "sd3.5-medium": "SD 3.5 Medium",
            "sd3.5-flash": "SD 3.5 Flash"
        }

        final_prompt_ru = f"""{st['prompt']}

Модель: {model_ru.get(st['model'], st['model'])}
Формат: {format_ru.get(st['format'], st['format'])}
🚫 Negative: {st['negative_prompt']}"""

        await update.message.reply_text(
            f"📝 Финальный промпт:\n\n{final_prompt_ru}",
            reply_markup=confirm_kb()
        )
        return

    # Обработка Search & Recolor - шаг 1 (search)
    if user_state[uid].get("awaiting_search_recolor_search"):
        user_state[uid]["awaiting_search_recolor_search"] = False
        user_state[uid]["search_recolor_search"] = text
        user_state[uid]["awaiting_search_recolor_color"] = True
        await update.message.reply_text(
            "🎨 <b>Search & Recolor</b>\n\n"
            "Шаг 2/2: Опишите новый цвет/стиль для найденного объекта.\n\n"
            "Например: 'синий', 'золотой металлик', 'радужный'",
            parse_mode="HTML"
        )
        return

    # Обработка Search & Recolor - шаг 2 (color)
    if user_state[uid].get("awaiting_search_recolor_color"):
        user_state[uid]["awaiting_search_recolor_color"] = False
        recolor_prompt = text
        search_prompt = user_state[uid].get("search_recolor_search")

        if not user_state.get(uid, {}).get("edit_image"):
            await update.message.reply_text("❌ Изображение потеряно. Загрузите заново через /editmy")
            return

        await update.message.reply_text(f"⏳ <b>Search & Recolor...</b>\n\n🎨 Ищем '{search_prompt}' и перекрашиваем в '{recolor_prompt}'...", parse_mode="HTML")

        result = search_and_recolor(user_state[uid]["edit_image"], search_prompt, recolor_prompt)

        if isinstance(result, str):
            await update.message.reply_text(result)
        else:
            watermarked = add_watermark(result)

        # Сохраняем отредактированное изображение в библиотеку
        if USE_GCS and result:
            try:
                gcs.save_user_image(uid, result, category='edited')
                print(f'[GCS] Edited image saved to library')
            except Exception as e:
                print(f'[ERROR] Failed to save edited image: {e}')
            await context.bot.send_photo(uid, watermarked, caption="✅ Объект перекрашен!")
        return

    # Обработка Search & Replace - шаг 1 (search)
    if user_state[uid].get("awaiting_search_replace_search"):
        user_state[uid]["awaiting_search_replace_search"] = False
        user_state[uid]["search_replace_search"] = text
        user_state[uid]["awaiting_search_replace_replace"] = True
        await update.message.reply_text(
            "🔄 <b>Search & Replace</b>\n\n"
            "Шаг 2/2: Опишите, чем заменить найденный объект.\n\n"
            "Например: 'собака', 'цветок', 'спортивная машина'",
            parse_mode="HTML"
        )
        return

    # Обработка Search & Replace - шаг 2 (replace)
    if user_state[uid].get("awaiting_search_replace_replace"):
        user_state[uid]["awaiting_search_replace_replace"] = False
        replace_prompt = text
        search_prompt = user_state[uid].get("search_replace_search")

        if not user_state.get(uid, {}).get("edit_image"):
            await update.message.reply_text("❌ Изображение потеряно. Загрузите заново через /editmy")
            return

        await update.message.reply_text(f"⏳ <b>Search & Replace...</b>\n\n🔄 Заменяем '{search_prompt}' на '{replace_prompt}'...", parse_mode="HTML")

        result = search_and_replace(user_state[uid]["edit_image"], search_prompt, replace_prompt)

        if isinstance(result, str):
            await update.message.reply_text(result)
        else:
            watermarked = add_watermark(result)

        # Сохраняем отредактированное изображение в библиотеку
        if USE_GCS and result:
            try:
                gcs.save_user_image(uid, result, category='edited')
                print(f'[GCS] Edited image saved to library')
            except Exception as e:
                print(f'[ERROR] Failed to save edited image: {e}')
            await context.bot.send_photo(uid, watermarked, caption="✅ Объект заменен!")
        return

    # Обработка Erase
    if user_state[uid].get("awaiting_erase_prompt"):
        user_state[uid]["awaiting_erase_prompt"] = False

        if not user_state.get(uid, {}).get("edit_image"):
            await update.message.reply_text("❌ Изображение потеряно. Загрузите заново через /editmy")
            return

        await update.message.reply_text(f"⏳ <b>Erase...</b>\n\n🗑️ Удаляем '{text}'...", parse_mode="HTML")

        result = erase_object(user_state[uid]["edit_image"], text)

        if isinstance(result, str):
            await update.message.reply_text(result)
        else:
            watermarked = add_watermark(result)

        # Сохраняем отредактированное изображение в библиотеку
        if USE_GCS and result:
            try:
                gcs.save_user_image(uid, result, category='edited')
                print(f'[GCS] Edited image saved to library')
            except Exception as e:
                print(f'[ERROR] Failed to save edited image: {e}')
            await context.bot.send_photo(uid, watermarked, caption="✅ Объект удален!")
        return

    # Проверяем, сохраняет ли пользователь пресет
    if user_state[uid].get("awaiting_preset_name"):
        user_state[uid]["awaiting_preset_name"] = False
        preset_name = text.strip()

        if not preset_name:
            await update.message.reply_text("❌ Название не может быть пустым")
            return

        # Получаем saved_params из state
        params = user_state[uid].get("saved_params", {})

        success, message = create_preset(
            user_id=uid,
            preset_name=preset_name,
            model=params.get("model", "sd3.5-large"),
            format_ratio=params.get("format", "1:1"),
            style=params.get("style", "none"),
            negative_prompt=user_state[uid].get("negative_prompt", "")
        )

        if success:
            await update.message.reply_text(
                f"✅ <b>Пресет '{preset_name}' сохранен!</b>\n\n"
                f"Используйте /presets для управления пресетами.",
                parse_mode="HTML"
            )
        else:
            await update.message.reply_text(f"❌ {message}")

        return

    # Проверяем, ищет ли пользователь в библиотеке
    if user_state[uid].get("awaiting_library_search"):
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup

        user_state[uid]["awaiting_library_search"] = False

        results = search_history(uid, text)

        if not results:
            await update.message.reply_text(
                f"🔍 По запросу '<b>{text}</b>' ничего не найдено",
                parse_mode="HTML"
            )
            return

        msg = f"🔍 <b>Результаты поиска: '{text}'</b>\n\n"
        for i, gen in enumerate(results[:10], 1):
            date = gen['date'][:16].replace('T', ' ')
            prompt_preview = gen['prompt'][:50] + "..." if len(gen['prompt']) > 50 else gen['prompt']
            fav_mark = "⭐ " if gen.get('is_favorite', False) else ""
            msg += f"{i}. {fav_mark}<b>{prompt_preview}</b>\n"
            msg += f"   📅 {date} | {gen['model']}\n\n"

        keyboard = [[InlineKeyboardButton("🔙 К библиотеке", callback_data="lib_main")]]

        await update.message.reply_text(
            msg,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )
        return

    # Обработка промпта для Imagen 3 Custom
    if user_state.get(uid, {}).get("engine") == "imagen3_custom":
        if not user_state[uid].get("reference_images"):
            await update.message.reply_text(
                "❌ Сначала загрузите референсные фото!",
                reply_markup=subject_type_kb()
            )
            return

        user_state[uid]["prompt"] = text

        # Спрашиваем формат
        await update.message.reply_text(
            "📐 Выберите формат изображения:",
            reply_markup=imagen_format_kb()
        )
        return

    # Обычный новый запрос
    if text.startswith("http"):
        await update.message.reply_text("🔍 Анализирую страницу с помощью ChatGPT...")
        summary = extract_text_from_url(text)

        # Сохраняем саммари и показываем с кнопками
        user_state[uid]["prompt"] = summary
        await update.message.reply_text(
            f"📄 Summary страницы:\n\n{summary}",
            reply_markup=summary_kb()
        )
        return

    # Обычный текстовый запрос - сразу к выбору модели
    user_state[uid]["prompt"] = text
    await update.message.reply_text("Выбери движок генерации изображений:", reply_markup=image_engine_kb())


async def library_show_category(update, context, category=None):
    """Показать изображения из категории"""
    from telegram import InputMediaPhoto

    query = update.callback_query
    uid = update.effective_user.id

    # Определяем категорию из callback_data если не передана
    if category is None and query:
        data = query.data
        if data == 'lib_show_generated':
            category = 'generated'
        elif data == 'lib_show_uploaded':
            category = 'uploaded'
        elif data == 'lib_show_edited':
            category = 'edited'
        elif data == 'lib_show_all':
            category = None
        elif data == 'lib_show_favorites':
            category = 'favorites'

    try:
        # Получаем изображения (до 10 штук)
        images = gcsa.get_user_images_filtered(uid, category=category, limit=10)

        if not images:
            category_names = {
                'generated': 'созданных',
                'uploaded': 'загруженных',
                'edited': 'отредактированных',
                'favorites': 'избранных',
                None: ''
            }
            cat_text = category_names.get(category, '')
            await query.edit_message_text(
                f'📁 Нет {cat_text} изображений',
                reply_markup=library_kb_extended()
            )
            return

        # Формируем media group
        media_group = []
        for img in images[:10]:
            caption = f"📄 {img['name']}"
            if img.get('metadata', {}).get('prompt'):
                prompt = img['metadata']['prompt'][:100]
                caption += f"\n💬 {prompt}"

            media_group.append(InputMediaPhoto(media=img['url'], caption=caption))

        # Отправляем изображения
        await context.bot.send_media_group(uid, media_group)

        # Показываем кнопки с информацией
        category_emoji = {
            'generated': '🎨',
            'uploaded': '📤',
            'edited': '✏️',
            'favorites': '⭐',
            None: '📁'
        }
        emoji = category_emoji.get(category, '📁')

        total_count = len(gcsa.get_user_images_filtered(uid, category=category, limit=1000))

        msg = f'{emoji} Показано: {len(images)} из {total_count}'

        # Если больше 10, добавляем pagination
        if total_count > 10:
            msg += f'\n\nИспользуйте фильтры для уточнения'

        await query.edit_message_text(msg, reply_markup=library_kb_extended())

    except Exception as e:
        await query.edit_message_text(
            f'❌ Ошибка: {e}',
            reply_markup=library_kb_extended()
        )

async def callbacks(update, context):
    query = update.callback_query
    uid = query.from_user.id
    data = query.data

    # Debug logging
    print(f"[DEBUG] Callback received - User: {uid}, Data: {data}")

    # Обработка кнопки "➕ 10 генераций" (только для админа)
        # Обработка библиотеки изображений
    if data.startswith('lib_show_'):
        await library_show_category(update, context)
        return

    if data.startswith("admin_add10_"):
        if uid != ADMIN_ID:
            await query.answer("❌ У вас нет прав для этого действия.", show_alert=True)
            return

        target_user_id = int(data[12:])  # Убираем "admin_add10_"
        remaining = add_generations(target_user_id, 10)

        await query.answer("✅ Добавлено 10 генераций", show_alert=True)

        # Отправляем уведомление пользователю
        try:
            await context.bot.send_message(
                chat_id=target_user_id,
                text="🎁 Админ дарит вам +10 бесплатных генераций!"
            )
        except Exception as e:
            pass

        return

    # Обработка кнопки "Редактировать" для саммари URL
    if data == "edit_summary":
        user_state[uid]["awaiting_summary_edit"] = True
        await query.edit_message_text(
            "✏️ Отправьте новое описание для изображения.\n\n"
            "Текущее описание будет заменено."
        )
        return

    # Обработка кнопки "Продолжить" для саммари URL
    if data == "continue_summary":
        await query.edit_message_text("Выбери модель:", reply_markup=model_kb())
        return

    # Обработка выбора движка генерации
    if data.startswith("engine_"):
        engine = data[7:]  # Убираем "engine_"
        user_state[uid]["engine"] = engine

        if engine == "sd":
            # Stable Diffusion - показываем выбор GPT модели
            await query.edit_message_text("Выбери GPT модель для обработки промпта:", reply_markup=gpt_model_kb())
        elif engine == "dalle":
            # DALL-E - показываем выбор модели DALL-E
            await query.edit_message_text("Выбери модель DALL-E:", reply_markup=dalle_model_kb())
        elif engine == "imagen":
            # Nano Banana 4 (Google Imagen 4) - показываем выбор формата
            await query.edit_message_text("🍌 Nano Banana 4\n\nВыбери формат изображения:", reply_markup=imagen_format_kb())
        elif engine == "imagen3_custom":
            # Imagen 3 Customization - инициализация и выбор типа субъекта
            user_state[uid]["reference_images"] = []  # Инициализация списка референсов
            await query.edit_message_text(
                "👤 <b>Imagen 3 Customization</b>\n\n"
                "Генерация изображений на основе референсного фото.\n\n"
                "📸 <b>Шаг 1:</b> Выберите тип субъекта",
                reply_markup=subject_type_kb(),
                parse_mode="HTML"
            )
        return

    # Обработка выбора модели DALL-E
    if data.startswith("dallemodel_"):
        dalle_model = data[11:]  # Убираем "dallemodel_"
        user_state[uid]["dalle_model"] = dalle_model
        await query.edit_message_text(f"Выбери размер изображения:", reply_markup=dalle_size_kb(dalle_model))
        return

    # Обработка выбора размера DALL-E
    if data.startswith("dallesize_"):
        dalle_size = data[10:]  # Убираем "dallesize_"
        user_state[uid]["dalle_size"] = dalle_size

        # Если DALL-E 3, показываем выбор качества
        if user_state[uid].get("dalle_model") == "dall-e-3":
            await query.edit_message_text("Выбери качество:", reply_markup=dalle_quality_kb())
        else:
            # Для DALL-E 2 сразу генерируем
            await generate_dalle_image(query, uid)
        return

    # Обработка выбора качества DALL-E 3
    if data.startswith("dallequal_"):
        dalle_quality = data[10:]  # Убираем "dallequal_"
        user_state[uid]["dalle_quality"] = dalle_quality
        await generate_dalle_image(query, uid)
        return

    # Обработка выбора формата Imagen
    if data.startswith("imgfmt_"):
        imagen_format = data[7:]  # Убираем "imgfmt_"
        user_state[uid]["imagen_format"] = imagen_format

        # Проверяем движок
        if user_state[uid].get("engine") == "imagen3_custom":
            await generate_imagen3_custom_image(query, uid)
        else:
            await generate_imagen_image(query, uid)
        return

    # Обработка выбора типа субъекта для Imagen 3 Custom
    if data.startswith("subject_"):
        subject = data.replace("subject_", "")
        user_state[uid]["subject_type"] = subject

        subject_names = {
            "person": "Человек 👤",
            "animal": "Животное 🐾",
            "product": "Продукт 📦",
            "default": "Другое 🎨"
        }

        await query.edit_message_text(
            f"✅ Выбран тип: <b>{subject_names.get(subject, 'Unknown')}</b>\n\n"
            f"📤 <b>Шаг 2:</b> Отправьте 1-4 референсных фото\n\n"
            f"<b>Требования к фото:</b>\n"
            f"• Объект по центру, занимает >50% кадра\n"
            f"• Хорошее освещение\n"
            f"• Фронтальный ракурс\n"
            f"• Без препятствий (очки, маски и т.д.)\n\n"
            f"После загрузки фото введите промпт для генерации.",
            reply_markup=reference_upload_kb(),
            parse_mode="HTML"
        )
        return

    # Обработка кнопок управления референсами
    if data == "ref_clear":
        user_state[uid]["reference_images"] = []
        await query.edit_message_text(
            "🗑 Референсы очищены.\n\n"
            "📤 Отправьте новые фото для генерации.",
            reply_markup=reference_upload_kb(),
            parse_mode="HTML"
        )
        return

    if data == "ref_done":
        if not user_state[uid].get("reference_images"):
            await query.answer("❌ Сначала загрузите хотя бы 1 фото!", show_alert=True)
            return

        await query.edit_message_text(
            f"✅ Загружено фото: {len(user_state[uid].get('reference_images', []))}\n\n"
            f"📝 Теперь отправьте промпт для генерации.\n\n"
            f"<b>Пример:</b>\n"
            f"<i>standing on a beach at sunset</i>\n\n"
            f"Маркер [1] будет добавлен автоматически.",
            parse_mode="HTML"
        )
        return

    # Обработка выбора GPT модели
    if data.startswith("gptmodel_"):
        user_state[uid]["gpt_model"] = data[9:]  # Убираем "gptmodel_"
        await query.edit_message_text("Выбери модель SD 3.5:", reply_markup=model_kb())
        return

    # Обработка выбора модели
    if data.startswith("model_"):
        user_state[uid]["model"] = data[6:]  # Убираем "model_"
        await query.edit_message_text("Выбери формат:", reply_markup=format_kb())
        return

    # Вспомогательная функция для показа финального промпта
    async def show_final_prompt(query, uid):
        st = user_state[uid]

        # Переводим параметры на русский для отображения
        format_ru = {
            "1:1": "1:1 (квадрат)",
            "21:9": "21:9 (ультра-широкий)",
            "16:9": "16:9 (горизонтально)",
            "3:2": "3:2",
            "5:4": "5:4",
            "4:5": "4:5",
            "2:3": "2:3",
            "9:16": "9:16 (вертикально)",
            "9:21": "9:21 (ультра-вертикально)"
        }

        model_ru = {
            "sd3.5-large": "SD 3.5 Large (лучшее качество)",
            "sd3.5-large-turbo": "SD 3.5 Large Turbo (быстро + качество)",
            "sd3.5-medium": "SD 3.5 Medium (баланс)",
            "sd3.5-flash": "SD 3.5 Flash (макс. скорость)"
        }

        style_ru = {
            "none": "Без стиля",
            "3d-model": "3D Model",
            "analog-film": "Analog Film",
            "anime": "Anime",
            "cinematic": "Cinematic",
            "comic-book": "Comic Book",
            "digital-art": "Digital Art",
            "enhance": "Enhance",
            "fantasy-art": "Fantasy Art",
            "isometric": "Isometric",
            "line-art": "Line Art",
            "low-poly": "Low Poly",
            "modeling-compound": "Modeling Compound",
            "neon-punk": "Neon Punk",
            "origami": "Origami",
            "photographic": "Photographic",
            "pixel-art": "Pixel Art",
            "tile-texture": "Tile Texture"
        }

        # Формируем красивый предпросмотр с эмодзи
        final_prompt_ru = f"""📝 <b>Предпросмотр генерации</b>

💬 <b>Промпт:</b>
<i>{st['prompt']}</i>

━━━━━━━━━━━━━━━
⚙️ <b>Параметры:</b>

🎨 <b>Модель:</b> {model_ru.get(st['model'], st['model'])}
📐 <b>Формат:</b> {format_ru.get(st['format'], st['format'])}"""

        # Показываем стиль только если он не "none"
        if st.get("style", "none") != "none":
            final_prompt_ru += f"\n🖌 <b>Стиль:</b> {style_ru.get(st.get('style', 'none'), st.get('style', 'none'))}"

        # Показываем дополнительные параметры (вид, положение камеры, освещение) если они были выбраны
        additional_params = st.get("additional_params", {})

        shot_ru = {
            "establishing": "Обзорный план",
            "pov": "От первого лица",
            "wide": "Широкий",
            "full body": "Во весь рост",
            "medium": "Средний",
            "closeup": "Крупный план",
            "extreme closeup": "Экстремально крупный",
            "over the shoulder": "Через плечо"
        }

        angle_ru = {
            "low angle": "Нижний ракурс",
            "high angle": "Верхний ракурс",
            "ground level": "На уровне земли",
            "overhead": "Сверху",
            "aerial shot": "Аэросъемка",
            "drone shot": "Съемка с дрона",
            "birds eye view": "С высоты птичьего полета",
            "wide angle": "Широкоугольный объектив",
            "fisheye lens": "Рыбий глаз"
        }

        lighting_ru = {
            "colored gel": "Цветные гели",
            "chiaroscuro": "Кьяроскуро",
            "studio lighting": "Студийное освещение",
            "silhouette": "Силуэт",
            "iridescent": "Радужное свечение",
            "golden hour": "Золотой час",
            "long exposure": "Длинная выдержка",
            "dramatic light": "Драматичный свет"
        }

        if additional_params.get("shot"):
            final_prompt_ru += f"\n🎬 <b>Вид:</b> {shot_ru.get(additional_params['shot'], additional_params['shot'])}"

        if additional_params.get("angle"):
            final_prompt_ru += f"\n📐 <b>Ракурс:</b> {angle_ru.get(additional_params['angle'], additional_params['angle'])}"

        if additional_params.get("lighting"):
            final_prompt_ru += f"\n💡 <b>Освещение:</b> {lighting_ru.get(additional_params['lighting'], additional_params['lighting'])}"

        if st.get("negative_prompt"):
            final_prompt_ru += f"\n🚫 <b>Negative Prompt:</b> <code>{st['negative_prompt']}</code>"

        final_prompt_ru += "\n━━━━━━━━━━━━━━━"

        # Показываем финальный промпт на русском с кнопками подтверждения
        await query.edit_message_text(
            final_prompt_ru,
            reply_markup=confirm_kb(),
            parse_mode="HTML"
        )

    if data.startswith("fmt_"):
        user_state[uid]["format"] = data[4:]

        # Показываем выбор стиля
        await query.edit_message_text("🎨 Выбери стиль:", reply_markup=style_kb())
        return

    if data.startswith("style_"):
        user_state[uid]["style"] = data[6:]

        # Инициализируем дополнительные параметры
        user_state[uid]["additional_params"] = {
            "shot": "",
            "angle": "",
            "lighting": ""
        }

        # Предлагаем добавить дополнительные параметры (вид, положение камеры, освещение)
        await query.edit_message_text(
            "💡 <b>Хотите дополнительно указать вид, положение камеры и освещение?</b>",
            reply_markup=additional_settings_kb(),
            parse_mode="HTML"
        )
        return

    # Обработка кнопки "Редактировать"
    if data == "edit_prompt":
        user_state[uid]["awaiting_edit"] = True
        await query.edit_message_text(
            "✏️ Отправьте новый текст промпта.\n\n"
            "Текущий промпт будет заменен, но все выбранные параметры сохранятся."
        )
        return

    # Обработка кнопки "Создать"
    if data == "generate":
        # Проверяем лимит генераций
        can_gen, remaining = can_generate(uid)
        if not can_gen:
            await query.answer(
                "❌ Вы исчерпали лимит бесплатных генераций (10 шт). "
                "Свяжитесь с поддержкой для продления.",
                show_alert=True
            )
            return

        st = user_state[uid]

        await query.edit_message_text("⏳ <b>Шаг 1/3:</b> Обработка промпта с помощью ChatGPT-4o...", parse_mode="HTML")

        # Формируем финальный промпт на английском с учетом всех параметров
        params = {
            'model': st['model'],
            'format': st['format'],
            'style': st['style'],
            'additional_params': st.get('additional_params', {})
        }

        # Сохраняем параметры для кнопок More/Reload
        user_state[uid]["saved_params"] = params.copy()

        # Переводим и формируем промпт для генерации
        gpt_model = user_state[uid].get("gpt_model", "gpt-4o")
        final_english_prompt = build_final_prompt(st['prompt'], params, gpt_model)

        # Определяем примерное время в зависимости от модели
        time_estimates = {
            "sd3.5-large": "~45 сек",
            "sd3.5-large-turbo": "~30 сек",
            "sd3.5-medium": "~25 сек",
            "sd3.5-flash": "~15 сек"
        }

        estimate = time_estimates.get(st['model'], "~30 сек")

        await query.edit_message_text(
            f"⏳ <b>Шаг 2/3:</b> Генерация изображения...\n\n"
            f"🎨 Модель: {st['model']}\n"
            f"⏱ Примерное время: {estimate}",
            parse_mode="HTML"
        )

        images = st["images"]

        # Переводим negative prompt на английский если он есть
        english_negative = ""
        if st.get("negative_prompt"):
            english_negative = translate_to_english(st["negative_prompt"], gpt_model)

        # Передаем формат, модель, стиль и negative prompt для генерации
        output = generate_dream(final_english_prompt, images, format_ratio=st['format'], model=st['model'], style=st.get('style'), negative_prompt=english_negative)

        await query.edit_message_text("⏳ <b>Шаг 3/3:</b> Отправка результата...", parse_mode="HTML")

        last_generated = None
        for item in output:
            try:
                # Добавляем watermark
                watermarked_image = add_watermark(item)
                await context.bot.send_photo(uid, watermarked_image)
                last_generated = item  # Сохраняем оригинал для AI функций
            except:
                await context.bot.send_message(uid, item)

        # Используем одну генерацию
        remaining = use_generation(uid)

        # Сохраняем в библиотеку
        add_to_history(
            user_id=uid,
            prompt=st['prompt'],
            english_prompt=final_english_prompt,
            params=params,
            negative_prompt=st.get('negative_prompt', '')
        )

        # Сохраняем промпт и изображение для возможности refinement и AI функций
        user_state[uid]["last_english_prompt"] = final_english_prompt
        user_state[uid]["last_image"] = last_generated

        # Сохраняем в GCS библиотеку
        if USE_GCS and last_generated:
            try:
                gcs.save_user_image(uid, last_generated, category='generated')
                # Сохраняем метаданные
                try:
                    images = gcsa.get_user_images_filtered(uid, category='generated', limit=1)
                    if images:
                        blob_name = images[0]['blob_name']
                        metadata = {'operation_type': 'generation'}
                        if 'prompt' in locals():
                            metadata['prompt'] = prompt
                        elif 'final_prompt' in locals():
                            metadata['prompt'] = final_prompt
                        gcsa.save_image_metadata(uid, blob_name, metadata)
                except Exception as e:
                    print(f'[ERROR] Failed to save metadata: {e}')
                print(f'[GCS] Image saved to user library')
            except Exception as e:
                print(f'[ERROR] Failed to save to library: {e}')
        user_state[uid]["in_refinement_mode"] = True

        # Логируем генерацию в Google Sheets
        gsl.log_generation(
            user_id=uid,
            username=query.from_user.username or "",
            engine="sd",
            model=st['model'],
            prompt_ru=st['prompt'],
            prompt_en=final_english_prompt,
            format_ratio=st['format'],
            style=st.get('style', ''),
            additional_params=st.get('additional_params', {}),
            negative_prompt=st.get('negative_prompt', ''),
            success=last_generated is not None,
            error="" if last_generated else "Generation failed"
        )

        # Обновляем счетчики пользователя в Google Sheets
        gsl.update_user_generations(uid, increment=1, remaining=remaining)

        # Отправляем сообщение с промптом и кнопками действий
        await context.bot.send_message(
            uid,
            f"✅ Изображение готово\n\n<code>{final_english_prompt}</code>\n\n💎 Осталось генераций: {remaining}",
            parse_mode="HTML",
            reply_markup=actions_kb()
        )
        return

    # Обработка кнопки "Modify" - вернуться к редактированию параметров
    if data == "action_modify":
        user_state[uid]["in_refinement_mode"] = False
        await query.edit_message_text("Выбери модель:", reply_markup=model_kb())
        return

    # Обработка кнопки "Reference this" - сохранить как референс
    if data == "action_reference":
        await query.answer("🖼️ Функция в разработке. Скоро можно будет использовать как референс!")
        return

    # Обработка кнопки "More like this" - генерация похожего
    if data == "action_more":
        # Проверяем лимит генераций
        can_gen, remaining_check = can_generate(uid)
        if not can_gen:
            await query.answer(
                "❌ Вы исчерпали лимит бесплатных генераций (10 шт). "
                "Свяжитесь с поддержкой для продления.",
                show_alert=True
            )
            return

        st = user_state[uid]
        if not st.get("saved_params"):
            await query.answer("❌ Нет сохраненных параметров")
            return

        await query.edit_message_text("⏳ <b>Шаг 1/3:</b> Обработка промпта с помощью ChatGPT-4o...", parse_mode="HTML")

        # Добавляем вариативность к промпту
        varied_prompt = st["prompt"] + ", вариация, другая композиция"

        # Используем сохраненные параметры
        gpt_model = user_state[uid].get("gpt_model", "gpt-4o")
        final_english_prompt = build_final_prompt(varied_prompt, st["saved_params"], gpt_model)

        # Определяем примерное время
        time_estimates = {
            "sd3.5-large": "~45 сек",
            "sd3.5-large-turbo": "~30 сек",
            "sd3.5-medium": "~25 сек",
            "sd3.5-flash": "~15 сек"
        }
        estimate = time_estimates.get(st["saved_params"]["model"], "~30 сек")

        await query.edit_message_text(
            f"⏳ <b>Шаг 2/3:</b> Генерация похожего изображения...\n\n"
            f"🎨 Модель: {st['saved_params']['model']}\n"
            f"⏱ Примерное время: {estimate}",
            parse_mode="HTML"
        )

        # Переводим negative prompt на английский если он есть
        english_negative = ""
        if st.get("negative_prompt"):
            english_negative = translate_to_english(st["negative_prompt"], gpt_model)

        images = st["images"]
        output = generate_dream(final_english_prompt, images, format_ratio=st["saved_params"]["format"], model=st["saved_params"]["model"], style=st["saved_params"].get("style"), negative_prompt=english_negative)

        await query.edit_message_text("⏳ <b>Шаг 3/3:</b> Отправка результата...", parse_mode="HTML")

        last_generated = None
        for item in output:
            try:
                # Добавляем watermark
                watermarked_image = add_watermark(item)
                await context.bot.send_photo(uid, watermarked_image)
                last_generated = item  # Сохраняем оригинал для AI функций
            except:
                await context.bot.send_message(uid, item)

        # Используем одну генерацию
        remaining = use_generation(uid)

        # Сохраняем в библиотеку
        add_to_history(
            user_id=uid,
            prompt=varied_prompt,
            english_prompt=final_english_prompt,
            params=st["saved_params"],
            negative_prompt=st.get("negative_prompt", "")
        )

        # Сохраняем промпт и изображение для возможности refinement и AI функций
        user_state[uid]["last_english_prompt"] = final_english_prompt
        user_state[uid]["last_image"] = last_generated

        # Сохраняем в GCS библиотеку
        if USE_GCS and last_generated:
            try:
                gcs.save_user_image(uid, last_generated, category='generated')
                # Сохраняем метаданные
                try:
                    images = gcsa.get_user_images_filtered(uid, category='generated', limit=1)
                    if images:
                        blob_name = images[0]['blob_name']
                        metadata = {'operation_type': 'generation'}
                        if 'prompt' in locals():
                            metadata['prompt'] = prompt
                        elif 'final_prompt' in locals():
                            metadata['prompt'] = final_prompt
                        gcsa.save_image_metadata(uid, blob_name, metadata)
                except Exception as e:
                    print(f'[ERROR] Failed to save metadata: {e}')
                print(f'[GCS] Image saved to user library')
            except Exception as e:
                print(f'[ERROR] Failed to save to library: {e}')
        user_state[uid]["in_refinement_mode"] = True

        await context.bot.send_message(
            uid,
            f"✅ Изображение готово\n\n<code>{final_english_prompt}</code>\n\n💎 Осталось генераций: {remaining}",
            parse_mode="HTML",
            reply_markup=actions_kb()
        )
        return

    # Обработка кнопки "Reload" - повторная генерация с теми же параметрами
    if data == "action_reload":
        # Проверяем лимит генераций
        can_gen, remaining_check = can_generate(uid)
        if not can_gen:
            await query.answer(
                "❌ Вы исчерпали лимит бесплатных генераций (10 шт). "
                "Свяжитесь с поддержкой для продления.",
                show_alert=True
            )
            return

        st = user_state[uid]
        if not st.get("saved_params"):
            await query.answer("❌ Нет сохраненных параметров")
            return

        await query.edit_message_text("⏳ <b>Шаг 1/3:</b> Обработка промпта с помощью ChatGPT-4o...", parse_mode="HTML")

        # Используем те же параметры
        gpt_model = user_state[uid].get("gpt_model", "gpt-4o")
        final_english_prompt = build_final_prompt(st["prompt"], st["saved_params"], gpt_model)

        # Определяем примерное время
        time_estimates = {
            "sd3.5-large": "~45 сек",
            "sd3.5-large-turbo": "~30 сек",
            "sd3.5-medium": "~25 сек",
            "sd3.5-flash": "~15 сек"
        }
        estimate = time_estimates.get(st["saved_params"]["model"], "~30 сек")

        await query.edit_message_text(
            f"⏳ <b>Шаг 2/3:</b> Повторная генерация...\n\n"
            f"🎨 Модель: {st['saved_params']['model']}\n"
            f"⏱ Примерное время: {estimate}",
            parse_mode="HTML"
        )

        # Переводим negative prompt на английский если он есть
        english_negative = ""
        if st.get("negative_prompt"):
            english_negative = translate_to_english(st["negative_prompt"], gpt_model)

        images = st["images"]
        output = generate_dream(final_english_prompt, images, format_ratio=st["saved_params"]["format"], model=st["saved_params"]["model"], style=st["saved_params"].get("style"), negative_prompt=english_negative)

        await query.edit_message_text("⏳ <b>Шаг 3/3:</b> Отправка результата...", parse_mode="HTML")

        last_generated = None
        for item in output:
            try:
                # Добавляем watermark
                watermarked_image = add_watermark(item)
                await context.bot.send_photo(uid, watermarked_image)
                last_generated = item  # Сохраняем оригинал для AI функций
            except:
                await context.bot.send_message(uid, item)

        # Используем одну генерацию
        remaining = use_generation(uid)

        # Сохраняем в библиотеку
        add_to_history(
            user_id=uid,
            prompt=st["prompt"],
            english_prompt=final_english_prompt,
            params=st["saved_params"],
            negative_prompt=st.get("negative_prompt", "")
        )

        # Сохраняем промпт и изображение для возможности refinement и AI функций
        user_state[uid]["last_english_prompt"] = final_english_prompt
        user_state[uid]["last_image"] = last_generated

        # Сохраняем в GCS библиотеку
        if USE_GCS and last_generated:
            try:
                gcs.save_user_image(uid, last_generated, category='generated')
                # Сохраняем метаданные
                try:
                    images = gcsa.get_user_images_filtered(uid, category='generated', limit=1)
                    if images:
                        blob_name = images[0]['blob_name']
                        metadata = {'operation_type': 'generation'}
                        if 'prompt' in locals():
                            metadata['prompt'] = prompt
                        elif 'final_prompt' in locals():
                            metadata['prompt'] = final_prompt
                        gcsa.save_image_metadata(uid, blob_name, metadata)
                except Exception as e:
                    print(f'[ERROR] Failed to save metadata: {e}')
                print(f'[GCS] Image saved to user library')
            except Exception as e:
                print(f'[ERROR] Failed to save to library: {e}')
        user_state[uid]["in_refinement_mode"] = True

        await context.bot.send_message(
            uid,
            f"✅ Изображение готово\n\n<code>{final_english_prompt}</code>\n\n💎 Осталось генераций: {remaining}",
            parse_mode="HTML",
            reply_markup=actions_kb()
        )
        return

    # Обработка кнопки "Upscale"
    if data == "action_upscale":
        st = user_state[uid]
        if not st.get("last_image"):
            await query.answer("❌ Нет изображения для upscale")
            return

        await query.edit_message_text("⏳ <b>Upscaling изображения...</b>\n\n🔍 Увеличиваем разрешение...", parse_mode="HTML")

        # Upscale последнего изображения
        result = upscale_image(st["last_image"])

        if isinstance(result, str):
            # Ошибка
            await query.edit_message_text(result)
        else:
            # Успех - отправляем upscaled изображение
            watermarked = add_watermark(result)

        # Сохраняем отредактированное изображение в библиотеку
        if USE_GCS and result:
            try:
                gcs.save_user_image(uid, result, category='edited')
                print(f'[GCS] Edited image saved to library')
            except Exception as e:
                print(f'[ERROR] Failed to save edited image: {e}')
            await context.bot.send_photo(uid, watermarked)
            await context.bot.send_message(
                uid,
                "✅ <b>Upscale завершен!</b>\n\n🔍 Разрешение увеличено",
                parse_mode="HTML",
                reply_markup=actions_kb()
            )
        return

    # Обработка кнопки "Variations"
    if data == "action_variations":
        st = user_state[uid]
        if not st.get("last_image"):
            await query.answer("❌ Нет изображения для создания вариаций")
            return

        # Проверяем лимит
        can_gen, remaining_check = can_generate(uid)
        if not can_gen:
            await query.answer(
                "❌ Вы исчерпали лимит бесплатных генераций (10 шт). "
                "Свяжитесь с поддержкой для продления.",
                show_alert=True
            )
            return

        await query.edit_message_text("⏳ <b>Создание вариации...</b>\n\n🎭 Генерируем похожее изображение...", parse_mode="HTML")

        # Создаем вариацию
        result = create_variations(st["last_image"], prompt=st.get("prompt", ""))

        if isinstance(result, str):
            # Ошибка
            await query.edit_message_text(result)
        else:
            # Успех
            for item in result:
                watermarked = add_watermark(item)

                # Сохраняем отредактированное изображение в библиотеку
                if USE_GCS and watermarked:
                    try:
                        gcs.save_user_image(uid, watermarked, category='edited')
                        print(f'[GCS] Edited image (variation) saved to library')
                    except Exception as e:
                        print(f'[ERROR] Failed to save edited image: {e}')

                await context.bot.send_photo(uid, watermarked)

            # Используем одну генерацию
            remaining = use_generation(uid)

            await context.bot.send_message(
                uid,
                f"✅ <b>Вариация создана!</b>\n\n💎 Осталось генераций: {remaining}",
                parse_mode="HTML",
                reply_markup=actions_kb()
            )
        return

    # Обработка кнопки "Remove Background"
    if data == "action_remove_bg":
        st = user_state[uid]
        if not st.get("last_image"):
            await query.answer("❌ Нет изображения для удаления фона")
            return

        await query.edit_message_text("⏳ <b>Удаление фона...</b>\n\n🖌️ Обрабатываем изображение...", parse_mode="HTML")

        # Удаляем фон
        result = remove_background(st["last_image"])

        if isinstance(result, str):
            # Ошибка
            await query.edit_message_text(result)
        else:
            # Успех - отправляем изображение без фона
            # Для PNG с прозрачностью не добавляем watermark, чтобы не портить прозрачность

            # Сохраняем отредактированное изображение в библиотеку
            if USE_GCS and result:
                try:
                    gcs.save_user_image(uid, result, category='edited')
                    print(f'[GCS] Edited image (remove_bg) saved to library')
                except Exception as e:
                    print(f'[ERROR] Failed to save edited image: {e}')

            await context.bot.send_document(uid, result, filename="no_bg.png")
            await context.bot.send_message(
                uid,
                "✅ <b>Фон удален!</b>\n\n🖌️ Изображение с прозрачным фоном готово",
                parse_mode="HTML",
                reply_markup=actions_kb()
            )
        return

    # Обработка кнопки "Face Restore"
    if data == "action_face_restore":
        st = user_state[uid]
        if not st.get("last_image"):
            await query.answer("❌ Нет изображения для восстановления лица")
            return

        await query.edit_message_text("⏳ <b>Восстановление лица...</b>\n\n👤 Улучшаем детали лица...", parse_mode="HTML")

        # Восстанавливаем лицо
        result = restore_face(st["last_image"])

        if isinstance(result, str):
            # Ошибка
            await query.edit_message_text(result)
        else:
            # Успех - отправляем улучшенное изображение
            watermarked = add_watermark(result)

        # Сохраняем отредактированное изображение в библиотеку
        if USE_GCS and result:
            try:
                gcs.save_user_image(uid, result, category='edited')
                print(f'[GCS] Edited image saved to library')
            except Exception as e:
                print(f'[ERROR] Failed to save edited image: {e}')
            await context.bot.send_photo(uid, watermarked)
            await context.bot.send_message(
                uid,
                "✅ <b>Лицо восстановлено!</b>\n\n👤 Детали лица улучшены",
                parse_mode="HTML",
                reply_markup=actions_kb()
            )
        return

    # Обработка кнопки "Inpaint"
    if data == "edit_inpaint":
        print(f"[DEBUG] edit_inpaint called for user {uid}")
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo

        st = user_state[uid]
        print(f"[DEBUG] User state keys: {list(st.keys())}")
        print(f"[DEBUG] last_image exists: {st.get('last_image') is not None}")
        print(f"[DEBUG] edit_image exists: {st.get('edit_image') is not None}")
        # Проверяем наличие изображения (может быть в last_image или edit_image)
        image_source = st.get("last_image") or st.get("edit_image")
        print(f"[DEBUG] image_source found: {image_source is not None}")
        if not image_source:
            await query.answer("❌ Нет изображения для inpainting")
            return

        await query.edit_message_text("⏳ <b>Загрузка редактора маски...</b>", parse_mode="HTML")

        # Загружаем изображение на веб-сервер
        webapp_url = await upload_image_to_webapp(context, image_source, uid)

        if not webapp_url:
            # Веб-сервер недоступен - показываем инструкцию
            await query.edit_message_text(
                "❌ <b>Редактор маски недоступен</b>\n\n"
                "Веб-сервер для Mini App не запущен.\n\n"
                "<b>Альтернативный метод:</b>\n"
                "1. Откройте изображение в графическом редакторе\n"
                "2. Закрасьте БЕЛЫМ цветом область для изменения\n"
                "3. Остальное закрасьте ЧЕРНЫМ\n"
                "4. Сохраните как маску и отправьте боту\n\n"
                "<b>Для администратора:</b>\n"
                "Запустите <code>python webapp_server.py</code> для использования интерактивного редактора.",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("◀️ Назад", callback_data="action_new")]
                ])
            )
            return

        # Сохраняем изображение для обработки
        user_state[uid]["edit_image"] = image_source
        user_state[uid]["waiting_for_inpaint_mask"] = True

        # Создаем кнопку для открытия Mini App
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🎨 Открыть редактор", web_app=WebAppInfo(url=webapp_url))],
            [InlineKeyboardButton("✅ Завершить", callback_data="inpaint_complete")],
            [InlineKeyboardButton("❌ Отмена", callback_data="action_new")]
        ])

        await query.edit_message_text(
            "🎨 <b>Редактор маски готов!</b>\n\n"
            "Нажмите кнопку ниже, чтобы открыть интерактивный редактор.\n\n"
            "В редакторе:\n"
            "• Закрасьте область, которую нужно изменить\n"
            "• Используйте ползунок для изменения размера кисти\n"
            "• Нажмите ✅ Готово когда закончите\n\n"
            "После создания маски отправьте описание того, что должно появиться на закрашенной области.",
            parse_mode="HTML",
            reply_markup=keyboard
        )
        return

    if data == "action_inpaint":
        print(f"[DEBUG] action_inpaint called for user {uid}")
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo

        st = user_state[uid]
        print(f"[DEBUG] User state keys: {list(st.keys())}")
        print(f"[DEBUG] last_image exists: {st.get('last_image') is not None}")
        print(f"[DEBUG] edit_image exists: {st.get('edit_image') is not None}")
        # Проверяем наличие изображения (может быть в last_image или edit_image)
        image_source = st.get("last_image") or st.get("edit_image")
        print(f"[DEBUG] image_source found: {image_source is not None}")
        if not image_source:
            await query.answer("❌ Нет изображения для inpainting")
            return

        await query.edit_message_text("⏳ <b>Загрузка редактора маски...</b>", parse_mode="HTML")

        # Загружаем изображение на веб-сервер
        webapp_url = await upload_image_to_webapp(context, image_source, uid)

        if not webapp_url:
            # Веб-сервер недоступен - показываем инструкцию
            await query.edit_message_text(
                "❌ <b>Редактор маски недоступен</b>\n\n"
                "Веб-сервер для Mini App не запущен.\n\n"
                "<b>Альтернативный метод:</b>\n"
                "1. Откройте изображение в графическом редакторе\n"
                "2. Закрасьте БЕЛЫМ цветом область для изменения\n"
                "3. Остальное закрасьте ЧЕРНЫМ\n"
                "4. Сохраните как маску и отправьте боту\n\n"
                "<b>Для администратора:</b>\n"
                "Запустите <code>python webapp_server.py</code> для использования интерактивного редактора.",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("◀️ Назад", callback_data="action_new")]
                ])
            )
            return

        # Сохраняем last_image в edit_image для обработки
        user_state[uid]["edit_image"] = image_source
        user_state[uid]["waiting_for_inpaint_mask"] = True

        # Создаем кнопку для открытия Mini App
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🎨 Открыть редактор", web_app=WebAppInfo(url=webapp_url))],
            [InlineKeyboardButton("✅ Завершить", callback_data="inpaint_complete")],
            [InlineKeyboardButton("❌ Отмена", callback_data="action_new")]
        ])

        await query.edit_message_text(
            "🎨 <b>Inpainting - редактирование части изображения</b>\n\n"
            "Нажмите кнопку ниже, чтобы открыть редактор маски.\n\n"
            "В редакторе:\n"
            "• Закрасьте кисточкой область, которую хотите изменить\n"
            "• Используйте ползунок для изменения размера кисти\n"
            "• Нажмите 'Готово' когда закончите\n\n"
            "После этого вам нужно будет описать, что должно быть на закрашенной области.",
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        return

    # Обработка кнопки "Сохранить как пресет"
    # Обработка кнопки "✅ Завершить" для inpaint
    if data == "inpaint_complete":
        import requests
        
        # Получаем pending mask с сервера
        try:
            response = requests.get(f'https://imagegen.tools.uspeshnyy.ru/get_pending_mask/{uid}', timeout=10)
            if response.status_code == 200:
                mask_data = response.json()
                mask_id = mask_data.get('mask_id')
                
                if not mask_id:
                    await query.answer("Маска не найдена. Нажмите 'Готово' в редакторе.", show_alert=True)
                    return
                
                # Получаем саму маску
                mask_response = requests.get(f'https://imagegen.tools.uspeshnyy.ru/get_mask/{mask_id}', timeout=10)
                if mask_response.status_code != 200:
                    await query.answer("Не удалось получить маску", show_alert=True)
                    return
                
                mask_full_data = mask_response.json()
                mask_data_url = mask_full_data.get('mask')
                original_width = mask_full_data.get('original_width')
                original_height = mask_full_data.get('original_height')
                
                # Декодируем
                import base64
                from io import BytesIO
                mask_b64 = mask_data_url.split(',')[1]
                mask_bytes = base64.b64decode(mask_b64)
                mask_image = BytesIO(mask_bytes)
                mask_image.seek(0)
                
                # Масштабируем обратно если нужно
                if original_width and original_height:
                    from PIL import Image
                    img = Image.open(mask_image)
                    img_resized = img.resize((original_width, original_height), Image.Resampling.LANCZOS)
                    mask_image = BytesIO()
                    img_resized.save(mask_image, format='PNG')
                    mask_image.seek(0)
                
                # Сохраняем в user_state
                user_state[uid]["inpaint_mask"] = mask_image
                user_state[uid]["waiting_for_inpaint_prompt"] = True
                
                await query.edit_message_text(
                    "✅ Маска получена!\n\nТеперь опишите, что должно быть на закрашенной области.",
                    parse_mode='HTML'
                )
            else:
                await query.answer("Маска не найдена. Сначала нажмите 'Готово' в редакторе.", show_alert=True)
        except Exception as e:
            await query.answer(f"Ошибка: {e}", show_alert=True)
            import traceback
            traceback.print_exc()
        return

    if data == "action_save_preset":
        st = user_state[uid]
        if not st.get("saved_params"):
            await query.answer("❌ Нет сохраненных параметров")
            return

        user_state[uid]["awaiting_preset_name"] = True
        await query.edit_message_text(
            "💾 <b>Сохранить пресет</b>\n\n"
            "Введите название для пресета (например: 'Портрет 4K', 'Пейзаж cinematic'):",
            parse_mode="HTML"
        )
        return

    # Обработка кнопки "New image" - начать сначала
    if data == "action_new":
        user_state.pop(uid, None)  # Это автоматически очищает in_refinement_mode
        await query.edit_message_text("🆕 Готов к новому изображению!\n\nПришли текст, ссылку или фото с описанием.")
        return

    # Обработка кнопок дополнительных параметров (вид, положение камеры, освещение)
    if data == "want_additional":
        # Показываем диалог выбора вида (shots)
        await query.edit_message_text(
            "🎬 <b>Вид</b>\n\nВыберите вид съемки:",
            reply_markup=shot_kb(),
            parse_mode="HTML"
        )
        return

    if data == "skip_additional":
        # Пропускаем дополнительные параметры и переходим к negative prompt
        await query.edit_message_text(
            "🚫 <b>Negative Prompt</b>\n\n"
            "Хотите указать, что НЕ должно быть на изображении?\n\n"
            "<i>Например:</i>\n"
            "<blockquote>Не используйте искажения, мультяшные эффекты, размытие или водяные знаки.</blockquote>",
            reply_markup=negative_prompt_kb(),
            parse_mode="HTML"
        )
        return

    # Обработка выбора вида (shots)
    if data.startswith("shot_"):
        user_state[uid]["additional_params"]["shot"] = data[5:]
        # Показываем диалог выбора положения камеры
        await query.edit_message_text(
            "📐 <b>Положение камеры</b>\n\nВыберите ракурс:",
            reply_markup=angle_kb(),
            parse_mode="HTML"
        )
        return

    if data == "skip_shot":
        user_state[uid]["additional_params"]["shot"] = ""
        # Показываем диалог выбора положения камеры
        await query.edit_message_text(
            "📐 <b>Положение камеры</b>\n\nВыберите ракурс:",
            reply_markup=angle_kb(),
            parse_mode="HTML"
        )
        return

    # Обработка выбора положения камеры
    if data.startswith("angle_"):
        user_state[uid]["additional_params"]["angle"] = data[6:]
        # Показываем диалог выбора освещения
        await query.edit_message_text(
            "💡 <b>Освещение</b>\n\nВыберите тип освещения:",
            reply_markup=lighting_kb(),
            parse_mode="HTML"
        )
        return

    if data == "skip_angle":
        user_state[uid]["additional_params"]["angle"] = ""
        # Показываем диалог выбора освещения
        await query.edit_message_text(
            "💡 <b>Освещение</b>\n\nВыберите тип освещения:",
            reply_markup=lighting_kb(),
            parse_mode="HTML"
        )
        return

    # Обработка выбора освещения
    if data.startswith("light_"):
        user_state[uid]["additional_params"]["lighting"] = data[6:]
        # Переходим к negative prompt
        await query.edit_message_text(
            "🚫 <b>Negative Prompt</b>\n\n"
            "Хотите указать, что НЕ должно быть на изображении?\n\n"
            "<i>Например:</i>\n"
            "<blockquote>Не используйте искажения, мультяшные эффекты, размытие или водяные знаки.</blockquote>",
            reply_markup=negative_prompt_kb(),
            parse_mode="HTML"
        )
        return

    if data == "skip_lighting":
        user_state[uid]["additional_params"]["lighting"] = ""
        # Переходим к negative prompt
        await query.edit_message_text(
            "🚫 <b>Negative Prompt</b>\n\n"
            "Хотите указать, что НЕ должно быть на изображении?\n\n"
            "<i>Например:</i>\n"
            "<blockquote>Не используйте искажения, мультяшные эффекты, размытие или водяные знаки.</blockquote>",
            reply_markup=negative_prompt_kb(),
            parse_mode="HTML"
        )
        return

    # Обработка кнопок negative prompt
    if data == "add_negative":
        user_state[uid]["awaiting_negative_prompt"] = True
        await query.edit_message_text(
            "🚫 <b>Введите Negative Prompt</b>\n\n"
            "Напишите, что НЕ должно быть на изображении.\n\n"
            "<i>Примеры: blurry, low quality, distorted, ugly, bad anatomy</i>",
            parse_mode="HTML"
        )
        return

    if data == "skip_negative":
        user_state[uid]["negative_prompt"] = ""
        await show_final_prompt(query, uid)
        return

    # Обработка кнопок пресетов
    if data == "presets_list":
        user_presets = get_user_presets(uid)

        msg = "💾 <b>Мои пресеты</b>\n\n"
        if user_presets:
            msg += "Выберите пресет для просмотра:\n\n"
        else:
            msg += "У вас пока нет сохраненных пресетов.\n\nСоздайте пресет, сохранив текущие настройки генерации!"

        await query.edit_message_text(
            msg,
            reply_markup=presets_list_kb(user_presets),
            parse_mode="HTML"
        )
        return

    if data == "presets_save_current":
        # Проверяем, есть ли сохраненные параметры в state
        if "saved_params" in user_state[uid]:
            user_state[uid]["awaiting_preset_name"] = True
            await query.edit_message_text(
                "💾 <b>Сохранить пресет</b>\n\n"
                "Введите название для пресета (например: 'Портрет 4K', 'Пейзаж cinematic'):",
                parse_mode="HTML"
            )
        else:
            await query.answer(
                "❌ Нет параметров для сохранения. Сначала создайте изображение!",
                show_alert=True
            )
        return

    if data == "presets_back":
        await query.message.delete()
        # Вызываем команду presets заново
        await presets_command(update, context)
        return

    if data.startswith("preset_load_"):
        preset_name = data[12:]  # Убираем "preset_load_"
        preset_data = get_preset(uid, preset_name)

        if not preset_data:
            await query.answer("Пресет не найден", show_alert=True)
            return

        # Форматируем данные для отображения
        model_ru = {
            "sd3.5-large": "SD 3.5 Large",
            "sd3.5-large-turbo": "SD 3.5 Large Turbo",
            "sd3.5-medium": "SD 3.5 Medium",
            "sd3.5-flash": "SD 3.5 Flash"
        }

        format_ru = {
            "1:1": "1:1 (квадрат)",
            "21:9": "21:9 (ультра-широкий)",
            "16:9": "16:9 (горизонтально)",
            "3:2": "3:2",
            "5:4": "5:4",
            "4:5": "4:5",
            "2:3": "2:3",
            "9:16": "9:16 (вертикально)",
            "9:21": "9:21 (ультра-вертикально)"
        }

        msg = f"""📌 <b>Пресет: {preset_name}</b>

🎨 Модель: {model_ru.get(preset_data['model'], preset_data['model'])}
📐 Формат: {format_ru.get(preset_data['format'], preset_data['format'])}
🖌 Стиль: {preset_data.get('style', 'none')}"""

        if preset_data.get('negative_prompt'):
            msg += f"\n🚫 Negative: {preset_data['negative_prompt']}"

        await query.edit_message_text(
            msg,
            reply_markup=preset_actions_kb(preset_name),
            parse_mode="HTML"
        )
        return

    if data.startswith("preset_apply_"):
        preset_name = data[13:]  # Убираем "preset_apply_"
        preset_data = get_preset(uid, preset_name)

        if not preset_data:
            await query.answer("Пресет не найден", show_alert=True)
            return

        # Применяем пресет к текущему state
        user_state[uid]["model"] = preset_data["model"]
        user_state[uid]["format"] = preset_data["format"]
        user_state[uid]["style"] = preset_data.get("style", "none")
        user_state[uid]["negative_prompt"] = preset_data.get("negative_prompt", "")

        await query.answer(f"✅ Пресет '{preset_name}' применен!", show_alert=True)
        await query.edit_message_text(
            f"✅ <b>Пресет применен!</b>\n\n"
            f"Теперь используйте /new для создания изображения с этими параметрами.",
            parse_mode="HTML"
        )
        return

    if data.startswith("preset_delete_"):
        preset_name = data[14:]  # Убираем "preset_delete_"

        success = delete_preset(uid, preset_name)

        if success:
            await query.answer(f"✅ Пресет '{preset_name}' удален", show_alert=True)
            # Возвращаемся к списку пресетов
            user_presets = get_user_presets(uid)
            msg = "💾 <b>Мои пресеты</b>\n\n"
            if user_presets:
                msg += "Выберите пресет для просмотра:\n\n"
            else:
                msg += "У вас больше нет сохраненных пресетов."

            await query.edit_message_text(
                msg,
                reply_markup=presets_list_kb(user_presets),
                parse_mode="HTML"
            )
        else:
            await query.answer("❌ Ошибка при удалении пресета", show_alert=True)
        return

    if data == "preset_none":
        # Заглушка для кнопки "Нет пресетов"
        await query.answer("Создайте первый пресет!", show_alert=True)
        return

    # Обработка кнопок покупки генераций
    if data.startswith("package_"):
        package_id = data[8:]  # Убираем "package_"
        package = get_package_info(package_id)

        if not package:
            await query.answer("❌ Пакет не найден", show_alert=True)
            return

        msg = f"""{format_package_message(package_id)}

Выберите способ оплаты:"""

        await query.edit_message_text(
            msg,
            reply_markup=payment_method_kb(package_id),
            parse_mode="HTML"
        )
        return

    if data.startswith("pay_stars_"):
        package_id = data[10:]  # Убираем "pay_stars_"
        package = get_package_info(package_id)

        if not package:
            await query.answer("❌ Пакет не найден", show_alert=True)
            return

        # Создаем invoice для Telegram Stars
        from telegram import LabeledPrice

        title = f"{package['name']} - {package['description']}"
        description = f"Пакет {package['generations']} генераций"
        payload = f"{uid}:{package_id}"
        currency = "XTR"  # Telegram Stars
        prices = [LabeledPrice("Генерации", package["stars"])]

        await context.bot.send_invoice(
            chat_id=uid,
            title=title,
            description=description,
            payload=payload,
            provider_token="",  # Пусто для Stars
            currency=currency,
            prices=prices
        )

        await query.answer("✅ Инвойс создан! Проверьте чат", show_alert=True)
        return

    if data.startswith("pay_crypto_"):
        package_id = data[11:]  # Убираем "pay_crypto_"
        package = get_package_info(package_id)

        if not package:
            await query.answer("❌ Пакет не найден", show_alert=True)
            return

        # Создаем invoice через CryptoBot
        invoice = create_cryptobot_invoice(uid, package_id)

        if not invoice:
            await query.edit_message_text(
                "❌ <b>Ошибка создания инвойса</b>\n\n"
                "Попробуйте позже или выберите Telegram Stars.",
                parse_mode="HTML"
            )
            return

        # Получаем ссылку на оплату
        pay_url = invoice.get("pay_url") or invoice.get("bot_invoice_url")

        from telegram import InlineKeyboardButton, InlineKeyboardMarkup

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("💰 Оплатить", url=pay_url)],
            [InlineKeyboardButton("◀️ Назад", callback_data="buy_packages")]
        ])

        msg = f"""💰 <b>Оплата через CryptoBot</b>

📦 Пакет: {package['name']}
💎 Генераций: {package['generations']}
💵 Цена: ${package['usdt']} USDT

Нажмите кнопку ниже для оплаты.
После оплаты генерации будут добавлены автоматически."""

        await query.edit_message_text(
            msg,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        return

    if data == "buy_packages":
        # Возврат к списку пакетов
        stats = get_user_stats(uid)
        remaining = stats["remaining"]

        msg = f"""💎 <b>Купить генерации</b>

📊 <b>Ваш баланс:</b> {remaining} генераций

{get_all_packages_message()}"""

        await query.edit_message_text(
            msg,
            reply_markup=packages_kb(),
            parse_mode="HTML"
        )
        return

    if data == "buy_back":
        # Закрыть меню покупки
        await query.message.delete()
        return

    # Обработка кнопок библиотеки
    if data.startswith("lib_history_"):
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup

        offset = int(data.split("_")[-1])
        history = get_user_history(uid, limit=5, offset=offset)

        if not history:
            await query.answer("История пуста")
            return

        msg = "📜 <b>История генераций:</b>\n\nНажмите на запись для деталей:"

        # Кнопки для каждого элемента истории
        keyboard = []
        for i, gen in enumerate(history):
            date = gen['date'][:10]  # Только дата
            prompt_preview = gen['prompt'][:35] + "..." if len(gen['prompt']) > 35 else gen['prompt']
            fav_mark = "⭐ " if gen.get('is_favorite', False) else ""
            button_text = f"{fav_mark}{prompt_preview} ({date})"
            keyboard.append([InlineKeyboardButton(button_text, callback_data=f"lib_view_{gen['id']}")])

        # Кнопки навигации
        nav_buttons = []
        if offset > 0:
            nav_buttons.append(InlineKeyboardButton("⬅️ Назад", callback_data=f"lib_history_{offset-5}"))
        if len(history) == 5:  # Возможно есть еще
            nav_buttons.append(InlineKeyboardButton("Вперед ➡️", callback_data=f"lib_history_{offset+5}"))
        if nav_buttons:
            keyboard.append(nav_buttons)

        keyboard.append([InlineKeyboardButton("🔙 К библиотеке", callback_data="lib_main")])

        await query.edit_message_text(
            msg,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )
        return

    # Просмотр деталей элемента истории
    if data.startswith("lib_view_"):
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup

        gen_id = float(data[9:])  # ID генерации (timestamp)
        history = get_user_history(uid, limit=100)  # Получаем всю историю

        # Находим нужный элемент
        gen = next((g for g in history if g['id'] == gen_id), None)

        if not gen:
            await query.answer("Запись не найдена", show_alert=True)
            return

        date = gen['date'][:16].replace('T', ' ')
        fav_mark = "⭐ " if gen.get('is_favorite', False) else ""

        msg = f"""📝 <b>Детали генерации</b> {fav_mark}

💬 <b>Промпт:</b>
<i>{gen['prompt']}</i>

🌐 <b>English:</b>
<code>{gen['english_prompt']}</code>

━━━━━━━━━━━━━━━
⚙️ <b>Параметры:</b>

🎨 <b>Модель:</b> {gen['model']}
📐 <b>Формат:</b> {gen['format']}"""

        if gen.get('style') and gen['style'] != 'none':
            msg += f"\n🖌 <b>Стиль:</b> {gen['style']}"

        if gen.get('negative_prompt'):
            msg += f"\n🚫 <b>Negative:</b> <code>{gen['negative_prompt']}</code>"

        msg += f"\n\n📅 <b>Дата:</b> {date}"

        keyboard = [
            [InlineKeyboardButton("🔄 Использовать снова", callback_data=f"lib_reuse_{gen_id}")],
            [InlineKeyboardButton("🔙 К истории", callback_data="lib_history_0")]
        ]

        await query.edit_message_text(
            msg,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )
        return

    # Повторное использование промпта из истории
    if data.startswith("lib_reuse_"):
        gen_id = float(data[10:])  # ID генерации
        history = get_user_history(uid, limit=100)

        gen = next((g for g in history if g['id'] == gen_id), None)

        if not gen:
            await query.answer("Запись не найдена", show_alert=True)
            return

        # Загружаем параметры в state
        user_state[uid]["prompt"] = gen['prompt']
        user_state[uid]["model"] = gen['model']
        user_state[uid]["format"] = gen['format']
        user_state[uid]["style"] = gen.get('style', 'none')
        user_state[uid]["negative_prompt"] = gen.get('negative_prompt', '')

        await query.answer("✅ Параметры загружены!", show_alert=True)

        # Показываем предпросмотр
        await show_final_prompt(query, uid)
        return

    if data == "lib_favorites":
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup

        favorites = get_favorites(uid)

        if not favorites:
            await query.answer("У вас нет избранных генераций", show_alert=True)
            return

        msg = "⭐ <b>Избранное:</b>\n\n"
        for i, gen in enumerate(favorites[:10], 1):
            date = gen['date'][:16].replace('T', ' ')
            prompt_preview = gen['prompt'][:50] + "..." if len(gen['prompt']) > 50 else gen['prompt']
            msg += f"{i}. <b>{prompt_preview}</b>\n"
            msg += f"   📅 {date} | {gen['model']}\n"
            msg += f"   <code>{gen['english_prompt'][:60]}...</code>\n\n"

        keyboard = [[InlineKeyboardButton("🔙 К библиотеке", callback_data="lib_main")]]

        await query.edit_message_text(
            msg,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )
        return

    if data == "lib_search":
        user_state[uid]["awaiting_library_search"] = True
        await query.edit_message_text(
            "🔍 <b>Поиск по истории</b>\n\n"
            "Отправьте текст для поиска по промптам:",
            parse_mode="HTML"
        )
        return

    if data == "lib_clear":
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup

        keyboard = [
            [
                InlineKeyboardButton("✅ Да, очистить", callback_data="lib_clear_confirm"),
                InlineKeyboardButton("❌ Отмена", callback_data="lib_main")
            ]
        ]

        await query.edit_message_text(
            "⚠️ <b>Очистка истории</b>\n\n"
            "Удалить всю историю генераций (кроме избранного)?\n\n"
            "Это действие нельзя отменить!",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )
        return

    if data == "lib_clear_confirm":
        clear_history(uid)
        await query.edit_message_text(
            "✅ История очищена!\n\n"
            "Избранные генерации сохранены."
        )
        return

    if data == "lib_main":
        # Возврат к главному экрану библиотеки
        await query.message.delete()
        await library_command(update, context)
        return

    # Обработчики для /editmy кнопок
    if data == "edit_reference":
        if not user_state.get(uid, {}).get("edit_image"):
            await query.answer("❌ Нет загруженного изображения", show_alert=True)
            return

        # Сохраняем как референс для следующей генерации
        user_state[uid]["images"] = [user_state[uid]["edit_image"]]
        await query.answer("✅ Изображение сохранено как референс!")
        await query.edit_message_text("✅ Изображение сохранено как референс для следующей генерации!")
        return

    if data == "edit_upscale":
        if not user_state.get(uid, {}).get("edit_image"):
            await query.answer("❌ Нет загруженного изображения", show_alert=True)
            return

        await query.edit_message_text("⏳ <b>Upscale...</b>\n\n🔍 Увеличиваем разрешение изображения...", parse_mode="HTML")

        result = upscale_image(user_state[uid]["edit_image"])

        if isinstance(result, str):
            await query.edit_message_text(result)
        else:
            watermarked = add_watermark(result)

        # Сохраняем отредактированное изображение в библиотеку
        if USE_GCS and result:
            try:
                gcs.save_user_image(uid, result, category='edited')
                print(f'[GCS] Edited image saved to library')
            except Exception as e:
                print(f'[ERROR] Failed to save edited image: {e}')
            await context.bot.send_photo(uid, watermarked, caption="✅ Upscale завершен!")
            await query.message.delete()
        return

    if data == "edit_remove_bg":
        if not user_state.get(uid, {}).get("edit_image"):
            await query.answer("❌ Нет загруженного изображения", show_alert=True)
            return

        await query.edit_message_text("⏳ <b>Remove Background...</b>\n\n🖌️ Удаляем фон...", parse_mode="HTML")

        result = remove_background(user_state[uid]["edit_image"])

        if isinstance(result, str):
            await query.edit_message_text(result)
        else:

            # Сохраняем отредактированное изображение в библиотеку
            if USE_GCS and result:
                try:
                    gcs.save_user_image(uid, result, category='edited')
                    print(f'[GCS] Edited image (remove_bg) saved to library')
                except Exception as e:
                    print(f'[ERROR] Failed to save edited image: {e}')

            await context.bot.send_photo(uid, result, caption="✅ Фон удален!")
            await query.message.delete()
        return

    if data == "edit_face_restore":
        if not user_state.get(uid, {}).get("edit_image"):
            await query.answer("❌ Нет загруженного изображения", show_alert=True)
            return

        await query.edit_message_text("⏳ <b>Face Restore...</b>\n\n👤 Улучшаем качество лиц...", parse_mode="HTML")

        result = restore_face(user_state[uid]["edit_image"])

        if isinstance(result, str):
            await query.edit_message_text(result)
        else:
            watermarked = add_watermark(result)

        # Сохраняем отредактированное изображение в библиотеку
        if USE_GCS and result:
            try:
                gcs.save_user_image(uid, result, category='edited')
                print(f'[GCS] Edited image saved to library')
            except Exception as e:
                print(f'[ERROR] Failed to save edited image: {e}')
            await context.bot.send_photo(uid, watermarked, caption="✅ Лица улучшены!")
            await query.message.delete()
        return

    if data == "edit_inpaint":
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo

        if not user_state.get(uid, {}).get("edit_image"):
            await query.answer("❌ Нет загруженного изображения", show_alert=True)
            return

        await query.edit_message_text("⏳ <b>Загрузка редактора маски...</b>", parse_mode="HTML")

        # Загружаем изображение на веб-сервер
        webapp_url = await upload_image_to_webapp(context, user_state[uid]["edit_image"], uid)

        if not webapp_url:
            # Веб-сервер недоступен - показываем инструкцию
            await query.edit_message_text(
                "❌ <b>Редактор маски недоступен</b>\n\n"
                "Веб-сервер для Mini App не запущен.\n\n"
                "<b>Альтернативный метод:</b>\n"
                "1. Откройте изображение в графическом редакторе\n"
                "2. Закрасьте БЕЛЫМ цветом область для изменения\n"
                "3. Остальное закрасьте ЧЕРНЫМ\n"
                "4. Сохраните как маску и отправьте боту\n\n"
                "<b>Для администратора:</b>\n"
                "Запустите <code>python webapp_server.py</code> для использования интерактивного редактора.",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("◀️ Назад", callback_data="action_new")]
                ])
            )
            return

        # Устанавливаем флаг ожидания маски от Mini App
        user_state[uid]["waiting_for_inpaint_mask"] = True

        # Создаем кнопку для открытия Mini App
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🎨 Открыть редактор", web_app=WebAppInfo(url=webapp_url))],
            [InlineKeyboardButton("✅ Завершить", callback_data="inpaint_complete")],
            [InlineKeyboardButton("❌ Отмена", callback_data="action_new")]
        ])

        await query.edit_message_text(
            "🎨 <b>Inpainting - редактирование части изображения</b>\n\n"
            "Нажмите кнопку ниже, чтобы открыть редактор маски.\n\n"
            "В редакторе:\n"
            "• Закрасьте кисточкой область, которую хотите изменить\n"
            "• Используйте ползунок для изменения размера кисти\n"
            "• Нажмите 'Готово' когда закончите\n\n"
            "После этого вам нужно будет описать, что должно быть на закрашенной области.",
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        return

    if data == "edit_outpaint":
        if not user_state.get(uid, {}).get("edit_image"):
            await query.answer("❌ Нет загруженного изображения", show_alert=True)
            return

        await query.edit_message_text("⏳ <b>Outpaint...</b>\n\n🖼️ Расширяем изображение (200px во все стороны)...", parse_mode="HTML")

        result = outpaint_image(user_state[uid]["edit_image"], left=200, right=200, up=200, down=200)

        if isinstance(result, str):
            await query.edit_message_text(result)
        else:
            watermarked = add_watermark(result)

        # Сохраняем отредактированное изображение в библиотеку
        if USE_GCS and result:
            try:
                gcs.save_user_image(uid, result, category='edited')
                print(f'[GCS] Edited image saved to library')
            except Exception as e:
                print(f'[ERROR] Failed to save edited image: {e}')
            await context.bot.send_photo(uid, watermarked, caption="✅ Изображение расширено!")
            await query.message.delete()
        return

    if data == "edit_search_recolor":
        user_state[uid]["awaiting_search_recolor_search"] = True
        await query.edit_message_text(
            "🎨 <b>Search & Recolor</b>\n\n"
            "Шаг 1/2: Опишите объект, который нужно найти и перекрасить.\n\n"
            "Например: 'красное платье', 'синяя машина', 'зеленое дерево'",
            parse_mode="HTML"
        )
        return

    if data == "edit_search_replace":
        user_state[uid]["awaiting_search_replace_search"] = True
        await query.edit_message_text(
            "🔄 <b>Search & Replace</b>\n\n"
            "Шаг 1/2: Опишите объект, который нужно найти и заменить.\n\n"
            "Например: 'кошка', 'дерево', 'машина'",
            parse_mode="HTML"
        )
        return

    if data == "edit_erase":
        user_state[uid]["awaiting_erase_prompt"] = True
        await query.edit_message_text(
            "🗑️ <b>Erase Object</b>\n\n"
            "Опишите объект, который нужно удалить с изображения.\n\n"
            "Например: 'человек слева', 'провода', 'мусор на земле'",
            parse_mode="HTML"
        )
        return

    # Обработка кнопки "Пропустить" для negative prompt в style guide
    if data == "skip":
        if user_state[uid].get("style_guide", {}).get("active"):
            sg_state = user_state[uid]["style_guide"]
            if sg_state["step"] == "negative_prompt":
                sg_state["negative_prompt"] = ""
                sg_state["step"] = "aspect_ratio"
                await query.edit_message_text(
                    "<b>Aspect Ratio</b> (формат изображения):",
                    parse_mode="HTML",
                    reply_markup=aspect_ratio_kb()
                )
        return

    # Обработка выбора aspect ratio
    if data.startswith("ar_"):
        if user_state[uid].get("style_guide", {}).get("active"):
            sg_state = user_state[uid]["style_guide"]
            sg_state["aspect_ratio"] = data[3:]  # Убираем "ar_"
            sg_state["step"] = "fidelity"
            await query.edit_message_text(
                "<b>Fidelity</b> (точность следования стилю, 0.1-1.0):\n"
                "Выберите или введите свое значение",
                parse_mode="HTML",
                reply_markup=fidelity_kb()
            )
        return

    # Обработка выбора fidelity
    if data.startswith("fid_"):
        if user_state[uid].get("style_guide", {}).get("active"):
            sg_state = user_state[uid]["style_guide"]
            fidelity_value = float(data[4:])  # Убираем "fid_"
            sg_state["fidelity"] = fidelity_value

            # Все параметры собраны, запускаем генерацию
            await query.edit_message_text("⏳ Генерация изображения в стиле референса...")

            result = generate_with_style_guide(
                image_path=sg_state["style_image"],
                prompt=sg_state["prompt"],
                negative_prompt=sg_state.get("negative_prompt", ""),
                aspect_ratio=sg_state.get("aspect_ratio", "1:1"),
                fidelity=fidelity_value
            )

            if isinstance(result, str):
                # Ошибка
                await context.bot.send_message(uid, f"❌ {result}")
            else:
                # Успех - отправляем изображение с watermark
                watermarked_image = add_watermark(result)
                await context.bot.send_photo(uid, watermarked_image)

                # Сохраняем параметры для возможности повторной генерации
                user_state[uid]["last_sg_params"] = {
                    "style_image": sg_state["style_image"],
                    "prompt": sg_state["prompt"],
                    "negative_prompt": sg_state.get("negative_prompt", ""),
                    "aspect_ratio": sg_state.get("aspect_ratio", "1:1"),
                    "fidelity": fidelity_value
                }

                await context.bot.send_message(
                    uid,
                    "✅ Style Guide генерация завершена!",
                    reply_markup=style_guide_regenerate_kb()
                )

            # Очищаем состояние
            user_state[uid]["style_guide"] = {"active": False}
        return

    # Обработка кнопки "Новая генерация в этом стиле"
    if data == "sg_regenerate":
        if "last_sg_params" in user_state[uid]:
            params = user_state[uid]["last_sg_params"]
            await query.edit_message_text("⏳ Генерация нового изображения в этом стиле...")

            result = generate_with_style_guide(
                image_path=params["style_image"],
                prompt=params["prompt"],
                negative_prompt=params.get("negative_prompt", ""),
                aspect_ratio=params.get("aspect_ratio", "1:1"),
                fidelity=params.get("fidelity", 0.5)
            )

            if isinstance(result, str):
                # Ошибка
                await context.bot.send_message(uid, f"❌ {result}")
            else:
                # Успех - отправляем изображение с watermark
                watermarked_image = add_watermark(result)
                await context.bot.send_photo(uid, watermarked_image)
                await context.bot.send_message(
                    uid,
                    "✅ Style Guide генерация завершена!",
                    reply_markup=style_guide_regenerate_kb()
                )
        return


    # ==================== РАСШИРЕННЫЕ ОБРАБОТЧИКИ БИБЛИОТЕКИ ====================

    # Показ избранного
    if data == 'lib_show_favorites':
        try:
            images = gcsa.get_user_images_filtered(uid, category='favorites', limit=10)
            if not images:
                await query.edit_message_text('⭐ Избранное пусто\n\nДобавьте изображения в избранное!', reply_markup=library_kb_extended())
                return

            # Отправляем изображения
            media_group = []
            for img in images:
                media_group.append({'type': 'photo', 'media': img['url'], 'caption': f"⭐ {img['name']}"})

            if media_group:
                from telegram import InputMediaPhoto
                await context.bot.send_media_group(uid, [InputMediaPhoto(media=m['media'], caption=m.get('caption', '')) for m in media_group[:10]])

            await query.edit_message_text(f'⭐ Избранное ({len(images)} изображений)', reply_markup=library_kb_extended())
        except Exception as e:
            await query.edit_message_text(f'❌ Ошибка: {e}', reply_markup=library_kb_extended())
        return

    # Меню фильтров
    if data == 'lib_filters':
        await query.edit_message_text(
            '🔍 <b>Фильтры по дате</b>\n\nВыберите период:',
            parse_mode='HTML',
            reply_markup=library_filters_kb()
        )
        return

    # Фильтры по дате
    if data.startswith('lib_filter_'):
        days_map = {'1': 1, '7': 7, '30': 30, 'all': None}
        filter_key = data.replace('lib_filter_', '')
        days = days_map.get(filter_key)

        try:
            images = gcsa.get_user_images_filtered(uid, days=days, limit=10)
            period_text = {1: 'за сегодня', 7: 'за неделю', 30: 'за месяц', None: 'за всё время'}

            if not images:
                await query.edit_message_text(
                    f'📅 Изображений {period_text[days]} не найдено',
                    reply_markup=library_filters_kb()
                )
                return

            # Отправляем изображения
            from telegram import InputMediaPhoto
            media_group = [InputMediaPhoto(media=img['url'], caption=f"{img['name']}") for img in images[:10]]
            await context.bot.send_media_group(uid, media_group)

            await query.edit_message_text(
                f'📅 Найдено {len(images)} изображений {period_text[days]}',
                reply_markup=library_filters_kb()
            )
        except Exception as e:
            await query.edit_message_text(f'❌ Ошибка: {e}', reply_markup=library_filters_kb())
        return

    # Возврат к библиотеке
    if data == 'lib_back':
        stats = gcs.get_user_stats(uid)
        try:
            fav_images = gcsa.get_user_images_filtered(uid, category='favorites', limit=1000)
            fav_count = len(fav_images)
        except:
            fav_count = 0

        lib_msg = f'''📚 <b>Библиотека изображений</b>

📊 <b>Статистика:</b>
🎨 Созданные: {stats['generated']}
📤 Загруженные: {stats['uploaded']}
✏️ Отредактированные: {stats['edited']}
⭐ Избранное: {fav_count}
━━━━━━━━━━━━━━━━━
📁 Всего: {stats['total']} изображений'''

        await query.edit_message_text(lib_msg, parse_mode='HTML', reply_markup=library_kb_extended())
        return

    # Pagination обработчик
    if data.startswith('lib_page_'):
        parts = data.split('_')
        if len(parts) >= 4:
            category = parts[2]
            page = int(parts[3])

            try:
                offset = page * 10
                images = gcsa.get_user_images_filtered(
                    uid,
                    category=category if category != 'all' else None,
                    limit=10,
                    offset=offset
                )

                if images:
                    from telegram import InputMediaPhoto
                    media_group = [InputMediaPhoto(media=img['url'], caption=img['name']) for img in images]
                    await context.bot.send_media_group(uid, media_group)

                    total_count = len(gcsa.get_user_images_filtered(uid, category=category if category != 'all' else None, limit=1000))
                    total_pages = (total_count + 9) // 10

                    await query.edit_message_text(
                        f'Страница {page + 1}/{total_pages}',
                        reply_markup=pagination_kb(page, total_pages, category)
                    )
                else:
                    await query.answer('Больше нет изображений')
            except Exception as e:
                await query.answer(f'Ошибка: {e}', show_alert=True)
        return


    # Поиск по тегам
    if data == 'lib_tags':
        user_state[uid]['awaiting_tag_search'] = True
        await query.edit_message_text(
            '🏷️ <b>Поиск по тегам</b>\n\nВведите теги через пробел для поиска',
            parse_mode='HTML'
        )
        return
    # Статистика операций
    if data == 'lib_stats':
        try:
            op_stats = gcsa.get_operation_stats(uid, days=30)

            stats_text = '📊 <b>Статистика операций (30 дней)</b>\n\n'
            if op_stats:
                for op, count in sorted(op_stats.items(), key=lambda x: x[1], reverse=True):
                    stats_text += f'• {op}: {count}\n'
            else:
                stats_text += 'Нет данных'

            await query.edit_message_text(stats_text, parse_mode='HTML', reply_markup=library_kb_extended())
        except Exception as e:
            await query.edit_message_text(f'❌ Ошибка: {e}', reply_markup=library_kb_extended())
        return

    # Меню экспорта
    if data == 'lib_export':
        await query.edit_message_text(
            '📦 <b>Экспорт изображений</b>\n\nВыберите что экспортировать:',
            parse_mode='HTML',
            reply_markup=export_options_kb()
        )
        return

    # Экспорт изображений
    if data.startswith('export_'):
        category_map = {
            'export_all': None,
            'export_generated': 'generated',
            'export_edited': 'edited',
            'export_favorites': 'favorites'
        }
        category = category_map.get(data)

        await query.edit_message_text('⏳ Создаю архив...')

        try:
            zip_buffer = gcsa.export_user_images(uid, category=category)
            if zip_buffer:
                category_name = category or 'all'
                await context.bot.send_document(
                    uid,
                    zip_buffer,
                    filename=f'images_{category_name}_{uid}.zip',
                    caption='📦 Архив готов!'
                )
                await query.message.delete()
            else:
                await query.edit_message_text('❌ Не удалось создать архив', reply_markup=export_options_kb())
        except Exception as e:
            await query.edit_message_text(f'❌ Ошибка: {e}', reply_markup=export_options_kb())
        return

    # Toggle избранного
    if data.startswith('img_fav_') or data.startswith('img_unfav_'):
        blob_name = data.replace('img_fav_', '').replace('img_unfav_', '')

        try:
            success = gcsa.toggle_favorite(uid, blob_name)
            if success:
                action = 'добавлено в' if 'fav_' in data else 'удалено из'
                await query.answer(f'✅ Изображение {action} избранное!')
            else:
                await query.answer('❌ Ошибка', show_alert=True)
        except Exception as e:
            await query.answer(f'❌ {e}', show_alert=True)
        return

    # Поделиться ссылкой
    if data.startswith('img_share_'):
        blob_name = data.replace('img_share_', '')
        public_url = gcs.get_public_url(blob_name)
        await query.answer()
        await context.bot.send_message(
            uid,
            f'🔗 <b>Публичная ссылка:</b>\n\n<code>{public_url}</code>\n\nСкопируйте и отправьте кому угодно!',
            parse_mode='HTML'
        )
        return

    # Удаление изображения
    if data.startswith('img_delete_') and not data.startswith('img_delete_confirm_'):
        blob_name = data.replace('img_delete_', '')
        await query.edit_message_text(
            '🗑️ <b>Удалить изображение?</b>\n\nЭто действие необратимо!',
            parse_mode='HTML',
            reply_markup=confirm_delete_kb(blob_name)
        )
        return

    # Подтверждение удаления
    if data.startswith('img_delete_confirm_'):
        blob_name = data.replace('img_delete_confirm_', '')

        try:
            success = gcs.delete_user_image(uid, blob_name)
            if success:
                await query.edit_message_text('✅ Изображение удалено', reply_markup=library_kb_extended())
            else:
                await query.edit_message_text('❌ Ошибка удаления', reply_markup=library_kb_extended())
        except Exception as e:
            await query.edit_message_text(f'❌ {e}', reply_markup=library_kb_extended())
        return

    # Добавление тегов
    if data.startswith('img_tags_'):
        blob_name = data.replace('img_tags_', '')
        user_state[uid]['awaiting_tags_for'] = blob_name
        await query.edit_message_text(
            '🏷️ <b>Добавить теги</b>\n\nОтправьте теги через пробел\nНапример: пейзаж горы закат'
        , parse_mode='HTML')
        return
async def precheckout_callback(update, context):
    """Обработка pre-checkout для Telegram Stars"""
    query = update.pre_checkout_query
    # Всегда подтверждаем платеж
    await query.answer(ok=True)

async def successful_payment(update, context):
    """Обработка успешного платежа через Telegram Stars"""
    payment = update.message.successful_payment
    payload = payment.invoice_payload

    try:
        # Парсим payload (format: user_id:package_id)
        user_id, package_id = payload.split(":")
        user_id = int(user_id)

        package = get_package_info(package_id)
        if not package:
            await update.message.reply_text("❌ Ошибка обработки платежа. Свяжитесь с поддержкой.")
            return

        # Добавляем генерации пользователю
        new_balance = add_generations(user_id, package["generations"])

        await update.message.reply_text(
            f"""✅ <b>Платеж успешно обработан!</b>

📦 Пакет: {package['name']}
💎 Добавлено генераций: {package['generations']}
📊 Новый баланс: {new_balance}

Спасибо за покупку! Приятного использования 🎨""",
            parse_mode="HTML"
        )

        print(f"[INFO] Payment processed: User {user_id} bought {package_id} package")

    except Exception as e:
        print(f"[ERROR] Payment processing error: {e}")
        await update.message.reply_text(
            "❌ Ошибка обработки платежа. Свяжитесь с поддержкой."
        )

async def inline_query(update, context):
    """Обработка inline queries - быстрый доступ к пресетам и истории"""
    query = update.inline_query.query
    uid = update.inline_query.from_user.id

    results = []

    # Получаем пресеты пользователя
    user_presets = get_user_presets(uid)

    # Добавляем пресеты в результаты
    for preset_name, preset_data in user_presets.items():
        title = f"🎨 Пресет: {preset_name}"
        description = f"{preset_data['model']} | {preset_data['format']}"
        if preset_data.get('style') and preset_data['style'] != 'none':
            description += f" | {preset_data['style']}"

        message_text = f"Использую пресет '{preset_name}'\n\nНапишите /new чтобы начать генерацию с этими параметрами"

        results.append(
            InlineQueryResultArticle(
                id=f"preset_{preset_name}",
                title=title,
                description=description,
                input_message_content=InputTextMessageContent(message_text),
                thumbnail_url="https://tools.uspeshnyy.ru/imagegenbot/preset-icon.png"
            )
        )

    # Получаем последние промпты из истории
    history = get_user_history(uid, limit=5)

    for i, gen in enumerate(history):
        prompt_preview = gen['prompt'][:50] + "..." if len(gen['prompt']) > 50 else gen['prompt']
        title = f"📜 {prompt_preview}"
        description = f"{gen['model']} | {gen['format']}"
        date = gen['date'][:10]

        message_text = f"Повторяю промпт: {gen['prompt']}\n\nНапишите /new для генерации"

        results.append(
            InlineQueryResultArticle(
                id=f"history_{gen['id']}",
                title=title,
                description=f"{description} ({date})",
                input_message_content=InputTextMessageContent(message_text),
                thumbnail_url="https://tools.uspeshnyy.ru/imagegenbot/history-icon.png"
            )
        )

    # Если запрос пустой и нет результатов
    if not results:
        results.append(
            InlineQueryResultArticle(
                id="empty",
                title="📝 Нет сохраненных пресетов или истории",
                description="Создайте изображение в боте для сохранения истории",
                input_message_content=InputTextMessageContent(
                    "Напишите /start для начала работы с ботом"
                )
            )
        )

    await update.inline_query.answer(results, cache_time=10)

async def handle_web_app_data(update, context):
    import json
    print("[DEBUG] handle_web_app_data called!")
    import base64
    import requests

    uid = update.effective_user.id

    try:
        data = json.loads(update.effective_message.web_app_data.data)
        user_id_from_app = data.get('user_id')
        mask_id = data.get('mask_id')

        if not mask_id:
            await update.message.reply_text("Не получен ID маски от редактора")
            return

        try:
            response = requests.get(f'https://imagegen.tools.uspeshnyy.ru/get_mask/{mask_id}', timeout=10)
            if response.status_code != 200:
                await update.message.reply_text("Не удалось получить маску с сервера")
                return
            
            mask_data = response.json()
            mask_data_url = mask_data.get('mask')
            original_width = mask_data.get('original_width')
            original_height = mask_data.get('original_height')
            
        except Exception as e:
            await update.message.reply_text(f"Ошибка получения маски: {e}")
            return

        if not mask_data_url:
            await update.message.reply_text("Не получена маска от редактора")
            return

        mask_b64 = mask_data_url.split(',')[1]
        mask_bytes = base64.b64decode(mask_b64)
        mask_image = BytesIO(mask_bytes)
        mask_image.seek(0)

        if original_width and original_height:
            from PIL import Image
            img = Image.open(mask_image)
            img_resized = img.resize((original_width, original_height), Image.Resampling.LANCZOS)
            mask_image = BytesIO()
            img_resized.save(mask_image, format='PNG')
            mask_image.seek(0)

        user_state[uid]["inpaint_mask"] = mask_image
        user_state[uid]["waiting_for_inpaint_prompt"] = True

        await update.message.reply_text(
            "Маска получена! Теперь опишите, что должно быть на закрашенной области.",
            parse_mode='HTML'
        )

    except Exception as e:
        await update.message.reply_text(f"Ошибка обработки маски: {e}")
        import traceback
        traceback.print_exc()


async def post_init(application):
    """Вызывается после инициализации приложения"""
    await setup_commands(application)
    print("Menu commands set successfully")

def main():
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).post_init(post_init).build()

    # Регистрируем обработчики команд
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("new", new_image))
    app.add_handler(CommandHandler("editmy", editmy_command))
    app.add_handler(CommandHandler("styletransfer", style_transfer_command))
    app.add_handler(CommandHandler("styleguide", style_guide_command))
    app.add_handler(CommandHandler("sketch", sketch_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("profile", profile_command))
    app.add_handler(CommandHandler("lib", library_command))
    app.add_handler(CommandHandler("prompts", prompts_command))
    app.add_handler(CommandHandler("expiry", expiry_command))
    app.add_handler(CommandHandler("presets", presets_command))
    app.add_handler(CommandHandler("buy", buy_command))

    # Админские команды
    app.add_handler(CommandHandler("admin_users", admin_users_command))
    app.add_handler(CommandHandler("admin_add", admin_add_command))

    # Обработчики сообщений и callback
    app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, handle_web_app_data))
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(callbacks))
    app.add_handler(InlineQueryHandler(inline_query))

    # Обработчики платежей
    app.add_handler(PreCheckoutQueryHandler(precheckout_callback))
    app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment))

    print("Bot started successfully...")
    print("Inline mode enabled - users can use @botname in any chat")
    print("Payment system enabled - Telegram Stars + CryptoBot")

    # Запуск с обработкой конфликта Telegram API
    import time
    from telegram.error import Conflict

    max_retries = 5
    retry_delay = 10  # секунд

    for attempt in range(max_retries):
        try:
            app.run_polling(drop_pending_updates=True)
            break
        except Conflict as e:
            if attempt < max_retries - 1:
                print(f"[CONFLICT] Telegram API conflict detected. Retry {attempt + 1}/{max_retries} in {retry_delay} seconds...")
                time.sleep(retry_delay)
                retry_delay *= 2  # Увеличиваем задержку при каждой попытке
            else:
                print(f"[CONFLICT] Failed after {max_retries} attempts. Exiting.")
                raise

if __name__ == "__main__":
    main()
