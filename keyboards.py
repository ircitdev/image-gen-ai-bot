from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def model_kb():
    """Клавиатура для выбора модели SD 3.5"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("SD 3.5 Large", callback_data="model_sd3.5-large")],
        [InlineKeyboardButton("SD 3.5 Large Turbo", callback_data="model_sd3.5-large-turbo")],
        [InlineKeyboardButton("SD 3.5 Medium", callback_data="model_sd3.5-medium")],
        [InlineKeyboardButton("SD 3.5 Flash", callback_data="model_sd3.5-flash")]
    ])

def format_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("1:1", callback_data="fmt_1:1"),
         InlineKeyboardButton("21:9", callback_data="fmt_21:9")],
        [InlineKeyboardButton("16:9", callback_data="fmt_16:9"),
         InlineKeyboardButton("3:2", callback_data="fmt_3:2")],
        [InlineKeyboardButton("5:4", callback_data="fmt_5:4"),
         InlineKeyboardButton("4:5", callback_data="fmt_4:5")],
        [InlineKeyboardButton("2:3", callback_data="fmt_2:3"),
         InlineKeyboardButton("9:16", callback_data="fmt_9:16")],
        [InlineKeyboardButton("9:21", callback_data="fmt_9:21")]
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
        ("None", "none"),
        ("3D Model", "3d-model"),
        ("Analog Film", "analog-film"),
        ("Anime", "anime"),
        ("Cinematic", "cinematic"),
        ("Comic Book", "comic-book"),
        ("Digital Art", "digital-art"),
        ("Enhance", "enhance"),
        ("Fantasy Art", "fantasy-art"),
        ("Isometric", "isometric"),
        ("Line Art", "line-art"),
        ("Low Poly", "low-poly"),
        ("Modeling Compound", "modeling-compound"),
        ("Neon Punk", "neon-punk"),
        ("Origami", "origami"),
        ("Photographic", "photographic"),
        ("Pixel Art", "pixel-art"),
        ("Tile Texture", "tile-texture")
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
        [InlineKeyboardButton("✏️ Modify", callback_data="action_modify"),
         InlineKeyboardButton("🖼️ Reference this", callback_data="action_reference")],
        [InlineKeyboardButton("🎨 More like this", callback_data="action_more"),
         InlineKeyboardButton("🔄 Reload", callback_data="action_reload")],
        [InlineKeyboardButton("🔍 Upscale", callback_data="action_upscale"),
         InlineKeyboardButton("🎭 Variations", callback_data="action_variations")],
        [InlineKeyboardButton("🖌️ Remove BG", callback_data="action_remove_bg"),
         InlineKeyboardButton("👤 Face Restore", callback_data="action_face_restore")],
        [InlineKeyboardButton("🎨 Inpaint", callback_data="action_inpaint")],
        [InlineKeyboardButton("💾 Сохранить как пресет", callback_data="action_save_preset")],
        [InlineKeyboardButton("➕ New image", callback_data="action_new")]
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
