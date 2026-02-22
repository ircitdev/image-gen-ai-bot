# Интеграция Imagen 3 Customization в bot.py

## Обзор

Imagen 3 Customization позволяет генерировать изображения на основе референсных фото (людей, животных, продуктов).

**Созданные файлы:**
- `imagen3_custom_api.py` - API интеграция
- `imagen3_custom_helper.py` - Helper для бота
- `keyboards.py` - добавлены `subject_type_kb()` и `reference_upload_kb()`

---

## Шаги интеграции в bot.py

### 1. Добавить импорты

Найдите секцию импортов в начале bot.py и добавьте:

```python
from imagen3_custom_helper import generate_imagen3_custom_image
from keyboards import ..., subject_type_kb, reference_upload_kb
```

### 2. Добавить новую опцию в image_engine_kb()

В файле `keyboards.py`, функция `image_engine_kb()` (строка ~10):

```python
def image_engine_kb():
    """Клавиатура для выбора движка генерации изображений"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎨 Stable Diffusion 3.5", callback_data="engine_sd")],
        [InlineKeyboardButton("🤖 DALL-E (ChatGPT)", callback_data="engine_dalle")],
        [InlineKeyboardButton("🍌 Nano Banana 4", callback_data="engine_imagen")],
        [InlineKeyboardButton("👤 Imagen 3 Custom (с референсом)", callback_data="engine_imagen3_custom")]  # НОВОЕ
    ])
```

### 3. Добавить обработчик выбора движка

Найдите обработчик `engine_*` callbacks и добавьте:

```python
# Обработчик выбора движка Imagen 3 Custom
elif data.startswith("engine_imagen3_custom"):
    st["engine"] = "imagen3_custom"
    st["reference_images"] = []  # Инициализация списка референсов

    await query.edit_message_text(
        "👤 <b>Imagen 3 Customization</b>\n\n"
        "Генерация изображений на основе референсного фото.\n\n"
        "📸 <b>Шаг 1:</b> Выберите тип субъекта",
        reply_markup=subject_type_kb(),
        parse_mode="HTML"
    )
```

### 4. Добавить обработчик выбора типа субъекта

```python
# Обработчик выбора типа субъекта
elif data.startswith("subject_"):
    subject = data.replace("subject_", "")
    st["subject_type"] = subject

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
```

### 5. Добавить обработчик фото (photo handler)

В существующий photo handler добавьте логику для сохранения референсных изображений:

```python
async def photo_handler(update, context):
    uid = update.effective_user.id
    st = user_state[uid]

    # Проверяем, используется ли Imagen 3 Custom
    if st.get("engine") == "imagen3_custom":
        # Скачиваем фото
        photo = update.message.photo[-1]  # Берём самое большое
        file = await context.bot.get_file(photo.file_id)

        # Загружаем в BytesIO
        from io import BytesIO
        photo_bytes = BytesIO()
        await file.download_to_memory(photo_bytes)
        photo_bytes.seek(0)

        # Добавляем в список референсов
        if "reference_images" not in st:
            st["reference_images"] = []

        st["reference_images"].append(photo_bytes)

        num_refs = len(st["reference_images"])

        await update.message.reply_text(
            f"✅ Фото {num_refs}/4 загружено!\n\n"
            f"{'📤 Отправьте еще фото или ' if num_refs < 4 else ''}"
            f"💬 Введите промпт для генерации\n\n"
            f"<i>Используйте [1], [2]... в промпте для ссылки на фото</i>",
            reply_markup=reference_upload_kb(),
            parse_mode="HTML"
        )
        return

    # Существующая логика для других движков...
```

### 6. Добавить обработчик кнопок управления референсами

```python
# Очистить референсы
elif data == "ref_clear":
    st["reference_images"] = []
    await query.edit_message_text(
        "🗑 Референсы очищены.\n\n"
        "📤 Отправьте новые фото для генерации.",
        reply_markup=reference_upload_kb(),
        parse_mode="HTML"
    )

# Начать генерацию
elif data == "ref_done":
    if not st.get("reference_images"):
        await query.answer("❌ Сначала загрузите хотя бы 1 фото!", show_alert=True)
        return

    await query.edit_message_text(
        f"✅ Загружено фото: {len(st.get('reference_images', []))}\n\n"
        f"📝 Теперь отправьте промпт для генерации.\n\n"
        f"<b>Пример:</b>\n"
        f"<i>standing on a beach at sunset</i>\n\n"
        f"Маркер [1] будет добавлен автоматически.",
        parse_mode="HTML"
    )
```

### 7. Обновить text_handler для Imagen 3 Custom

В обработчике текстовых сообщений добавьте:

```python
async def text_handler(update, context):
    uid = update.effective_user.id
    st = user_state[uid]

    text = update.message.text.strip()

    # Обработка промпта для Imagen 3 Custom
    if st.get("engine") == "imagen3_custom":
        if not st.get("reference_images"):
            await update.message.reply_text(
                "❌ Сначала загрузите референсные фото!",
                reply_markup=subject_type_kb()
            )
            return

        st["prompt"] = text

        # Спрашиваем формат
        await update.message.reply_text(
            "📐 Выберите формат изображения:",
            reply_markup=imagen_format_kb()
        )
        return

    # Существующая логика...
```

### 8. Добавить вызов генерации

В обработчике выбора формата (`imgfmt_*`):

```python
elif data.startswith("imgfmt_"):
    formato = data.replace("imgfmt_", "")
    st["imagen_format"] = formato

    # Проверяем движок
    if st.get("engine") == "imagen3_custom":
        await generate_imagen3_custom_image(query, uid)
    elif st.get("engine") == "imagen":
        await generate_imagen_image(query, uid)
    # и т.д...
```

---

## Полный flow для пользователя

1. `/start` → Выбор движка → "👤 Imagen 3 Custom"
2. Выбор типа субъекта: Человек/Животное/Продукт/Другое
3. Загрузка 1-4 референсных фото
4. Ввод промпта (например: "standing on a beach at sunset")
5. Выбор формата изображения
6. Генерация и получение результата

---

## Пример использования в боте

**Пользователь:**
1. Нажимает `/start`
2. Выбирает "👤 Imagen 3 Custom (с референсом)"
3. Выбирает "👤 Человек"
4. Отправляет фото своего лица
5. Вводит: "wearing a spacesuit on Mars"
6. Выбирает формат: "16:9"
7. Получает изображение себя в скафандре на Марсе!

---

## Важные заметки

### Требования к референсным фото
- **Лицо/объект по центру** - должно занимать >50% кадра
- **Хорошее освещение** - без теней
- **Фронтальный ракурс** - без сильных поворотов
- **Без препятствий** - очки, маски, руки и т.д.

### Ограничения API
- Максимум 4 референсных фото
- Timeout: 180 секунд (3 минуты)
- Поддерживаемые форматы: 1:1, 3:4, 4:3, 9:16, 16:9

### Автоматическая вставка маркеров
Helper автоматически добавляет `[1]` в промпт, если пользователь не указал.

Пример:
- Пользователь вводит: "on a beach"
- Промпт преобразуется в: "A photo of person [1], on a beach"

---

## Тестирование

После интеграции протестируйте:

```bash
# Локально
cd d:/DevTools/Database/UspImagegen
python test_imagen3_custom.py  # Создайте тестовый скрипт

# На сервере
ssh root@31.44.7.144
cd /root/bots/usp
# Загрузите новые файлы
# Перезапустите бота
```

---

## Файлы для загрузки на сервер

```bash
scp imagen3_custom_api.py root@31.44.7.144:/root/bots/usp/
scp imagen3_custom_helper.py root@31.44.7.144:/root/bots/usp/
scp keyboards.py root@31.44.7.144:/root/bots/usp/
```

---

**Статус:** Готово к интеграции
**Дата:** 2026-02-22
