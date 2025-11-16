from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def gpt_model_kb():
    """Клавиатура для выбора GPT модели"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("GPT-4o (Быстрее ⚡)", callback_data="gptmodel_gpt-4o")],
        [InlineKeyboardButton("GPT-5 (Умнее 🧠)", callback_data="gptmodel_gpt-5")]
    ])

def image_engine_kb():
    """Клавиатура для выбора движка генерации изображений"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎨 Stable Diffusion 3.5", callback_data="engine_sd")],
        [InlineKeyboardButton("🤖 DALL-E (ChatGPT)", callback_data="engine_dalle")]
    ])

def dalle_model_kb():
    """Клавиатура для выбора модели DALL-E"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("DALL-E 3 (Лучшее качество)", callback_data="dallemodel_dall-e-3")],
        [InlineKeyboardButton("DALL-E 2 (Быстрее)", callback_data="dallemodel_dall-e-2")]
    ])

def dalle_size_kb(model="dall-e-3"):
    """Клавиатура для выбора размера DALL-E изображения"""
    if model == "dall-e-3":
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("Квадрат 1024x1024", callback_data="dallesize_1024x1024")],
            [InlineKeyboardButton("Портрет 1024x1792", callback_data="dallesize_1024x1792")],
            [InlineKeyboardButton("Пейзаж 1792x1024", callback_data="dallesize_1792x1024")]
        ])
    else:  # dall-e-2
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("Маленький 256x256", callback_data="dallesize_256x256")],
            [InlineKeyboardButton("Средний 512x512", callback_data="dallesize_512x512")],
            [InlineKeyboardButton("Большой 1024x1024", callback_data="dallesize_1024x1024")]
        ])

def dalle_quality_kb():
    """Клавиатура для выбора качества DALL-E 3"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Standard (Быстрее)", callback_data="dallequal_standard")],
        [InlineKeyboardButton("HD (Лучше)", callback_data="dallequal_hd")]
    ])

def model_kb():
    """Клавиатура для выбора модели SD 3.5"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("SD 3.5 Large (Макс качество и детализация)", callback_data="model_sd3.5-large")],
        [InlineKeyboardButton("SD 3.5 Large Turbo (Быстрая генерация)", callback_data="model_sd3.5-large-turbo")],
        [InlineKeyboardButton("SD 3.5 Medium (Баланс качества и скорости)", callback_data="model_sd3.5-medium")],
        [InlineKeyboardButton("SD 3.5 Flash (Самая быстрая генерация)", callback_data="model_sd3.5-flash")]
    ])

def format_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("1:1 Квадрат", callback_data="fmt_1:1"),
         InlineKeyboardButton("21:9 Ультра-широкий", callback_data="fmt_21:9")],
        [InlineKeyboardButton("16:9 Широкоэкранный", callback_data="fmt_16:9"),
         InlineKeyboardButton("3:2 Классический", callback_data="fmt_3:2")],
        [InlineKeyboardButton("5:4 Почти квадрат", callback_data="fmt_5:4"),
         InlineKeyboardButton("4:5 Портрет", callback_data="fmt_4:5")],
        [InlineKeyboardButton("2:3 Классический портрет", callback_data="fmt_2:3"),
         InlineKeyboardButton("9:16 Вертикальный", callback_data="fmt_9:16")],
        [InlineKeyboardButton("9:21 Ультра-вертикальный", callback_data="fmt_9:21")]
    ])

def shot_kb():
    shots = [
        "establishing","pov","wide","full body","medium",
        "closeup","extreme closeup","over the shoulder"
    ]
    rows = [[InlineKeyboardButton(s, callback_data=f"shot_{s}")] for s in shots]
    return InlineKeyboardMarkup(rows)

def angle_kb():
    angles = [
        "low angle","high angle","ground level","overhead",
        "aerial shot","drone shot","birds eye view",
        "wide angle","fisheye lens"
    ]
    rows = [[InlineKeyboardButton(a, callback_data=f"angle_{a}")] for a in angles]
    return InlineKeyboardMarkup(rows)

def style_kb():
    styles = [
        ("Без стиля", "none"),
        ("3D модель", "3d-model"),
        ("Аналоговая пленка", "analog-film"),
        ("Аниме", "anime"),
        ("Кинематографичное", "cinematic"),
        ("Комикс", "comic-book"),
        ("Цифровое искусство", "digital-art"),
        ("Улучшенное", "enhance"),
        ("Фэнтези арт", "fantasy-art"),
        ("Изометрия", "isometric"),
        ("Линейная графика", "line-art"),
        ("Низкополигональное", "low-poly"),
        ("Пластилин", "modeling-compound"),
        ("Неон-панк", "neon-punk"),
        ("Оригами", "origami"),
        ("Фотореалистичное", "photographic"),
        ("Пиксель арт", "pixel-art"),
        ("Текстура плитки", "tile-texture")
    ]
    rows = [[InlineKeyboardButton(display, callback_data=f"style_{value}")] for display, value in styles]
    return InlineKeyboardMarkup(rows)

def lighting_kb():
    lights = [
        "colored gel","chiaroscuro","studio lighting",
        "silhouette","iridescent","golden hour",
        "long exposure","dramatic lighting","motion blur"
    ]
    rows = [[InlineKeyboardButton(l, callback_data=f"light_{l}")] for l in lights]
    return InlineKeyboardMarkup(rows)

def quality_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("HD", callback_data="q_HD"),
         InlineKeyboardButton("FullHD", callback_data="q_FullHD"),
         InlineKeyboardButton("4K", callback_data="q_4K")]
    ])

def negative_prompt_kb():
    """Клавиатура для выбора - добавить negative prompt или пропустить"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Добавить Negative Prompt", callback_data="add_negative")],
        [InlineKeyboardButton("▶️ Пропустить", callback_data="skip_negative")]
    ])

def confirm_kb():
    """Клавиатура для подтверждения/редактирования промпта"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✏️ Редактировать", callback_data="edit_prompt"),
         InlineKeyboardButton("✅ Создать", callback_data="generate")]
    ])

def actions_kb():
    """Клавиатура действий после генерации изображения"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✏️ Изменить", callback_data="action_modify"),
         InlineKeyboardButton("🖼️ Использовать как референс", callback_data="action_reference")],
        [InlineKeyboardButton("🎨 Еще похожие", callback_data="action_more"),
         InlineKeyboardButton("🔄 Перегенерировать", callback_data="action_reload")],
        [InlineKeyboardButton("🔍 Увеличить", callback_data="action_upscale"),
         InlineKeyboardButton("🎭 Вариации", callback_data="action_variations")],
        [InlineKeyboardButton("🖌️ Убрать фон", callback_data="action_remove_bg"),
         InlineKeyboardButton("👤 Восстановить лицо", callback_data="action_face_restore")],
        [InlineKeyboardButton("🎨 Дорисовать", callback_data="action_inpaint")],
        [InlineKeyboardButton("💾 Сохранить как пресет", callback_data="action_save_preset")],
        [InlineKeyboardButton("➕ Новое изображение", callback_data="action_new")]
    ])

def summary_kb():
    """Клавиатура для просмотра саммари URL"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✏️ Редактировать", callback_data="edit_summary"),
         InlineKeyboardButton("▶️ Продолжить", callback_data="continue_summary")]
    ])

def presets_main_kb():
    """Главная клавиатура управления пресетами"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📋 Мои пресеты", callback_data="presets_list")],
        [InlineKeyboardButton("💾 Сохранить текущие настройки", callback_data="presets_save_current")],
        [InlineKeyboardButton("◀️ Назад", callback_data="presets_back")]
    ])

def presets_list_kb(user_presets):
    """Клавиатура со списком пресетов пользователя"""
    buttons = []

    for preset_name in user_presets.keys():
        buttons.append([InlineKeyboardButton(f"📌 {preset_name}", callback_data=f"preset_load_{preset_name}")])

    if not buttons:
        buttons.append([InlineKeyboardButton("Нет сохраненных пресетов", callback_data="preset_none")])

    buttons.append([InlineKeyboardButton("◀️ Назад", callback_data="presets_back")])

    return InlineKeyboardMarkup(buttons)

def preset_actions_kb(preset_name):
    """Клавиатура действий с конкретным пресетом"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Применить", callback_data=f"preset_apply_{preset_name}")],
        [InlineKeyboardButton("🗑️ Удалить", callback_data=f"preset_delete_{preset_name}")],
        [InlineKeyboardButton("◀️ Назад к списку", callback_data="presets_list")]
    ])

def packages_kb():
    """Клавиатура выбора пакета генераций"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📦 Starter (50 gen)", callback_data="package_small")],
        [InlineKeyboardButton("📦 Pro (150 gen)", callback_data="package_medium")],
        [InlineKeyboardButton("📦 Premium (500 gen)", callback_data="package_large")],
        [InlineKeyboardButton("📦 Unlimited (месяц)", callback_data="package_unlimited")],
        [InlineKeyboardButton("◀️ Назад", callback_data="buy_back")]
    ])

def payment_method_kb(package_id):
    """Клавиатура выбора метода оплаты"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⭐ Telegram Stars", callback_data=f"pay_stars_{package_id}")],
        [InlineKeyboardButton("💰 Криптовалюта (USDT)", callback_data=f"pay_crypto_{package_id}")],
        [InlineKeyboardButton("◀️ Назад к пакетам", callback_data="buy_packages")]
    ])

def edit_actions_kb():
    """Клавиатура действий для редактирования загруженного изображения (/editmy)"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🖼️ Использовать как референс", callback_data="edit_reference")],
        [InlineKeyboardButton("🔍 Увеличить", callback_data="edit_upscale"),
         InlineKeyboardButton("🖌️ Убрать фон", callback_data="edit_remove_bg")],
        [InlineKeyboardButton("👤 Восстановить лицо", callback_data="edit_face_restore"),
         InlineKeyboardButton("🎨 Дорисовать", callback_data="edit_inpaint")],
        [InlineKeyboardButton("🖼️ Расширить", callback_data="edit_outpaint"),
         InlineKeyboardButton("🎨 Найти и перекрасить", callback_data="edit_search_recolor")],
        [InlineKeyboardButton("🔄 Найти и заменить", callback_data="edit_search_replace"),
         InlineKeyboardButton("🗑️ Стереть объект", callback_data="edit_erase")],
        [InlineKeyboardButton("➕ Новое изображение", callback_data="action_new")]
    ])

def skip_kb():
    """Кнопка Пропустить"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⏩ Пропустить", callback_data="skip")]
    ])

def aspect_ratio_kb():
    """Клавиатура выбора aspect ratio для style guide"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("1:1", callback_data="ar_1:1"),
         InlineKeyboardButton("16:9", callback_data="ar_16:9"),
         InlineKeyboardButton("9:16", callback_data="ar_9:16")],
        [InlineKeyboardButton("21:9", callback_data="ar_21:9"),
         InlineKeyboardButton("9:21", callback_data="ar_9:21"),
         InlineKeyboardButton("3:2", callback_data="ar_3:2")],
        [InlineKeyboardButton("2:3", callback_data="ar_2:3"),
         InlineKeyboardButton("5:4", callback_data="ar_5:4"),
         InlineKeyboardButton("4:5", callback_data="ar_4:5")]
    ])

def fidelity_kb():
    """Клавиатура выбора fidelity для style guide"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔹 Слабо (0.3)", callback_data="fid_0.3"),
         InlineKeyboardButton("🔸 Средне (0.6)", callback_data="fid_0.6"),
         InlineKeyboardButton("🔺 Максимально (1.0)", callback_data="fid_1.0")]
    ])

def style_guide_regenerate_kb():
    """Кнопка для новой генерации в том же стиле"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 Новая генерация в этом стиле", callback_data="sg_regenerate")]
    ])
