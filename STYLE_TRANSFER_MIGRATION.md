# Миграция Style Transfer и Style Guide на Imagen

## Проблема
Stable Diffusion API показывает плохие результаты для style transfer и style guide.

## Решение
Использовать **Nano Banana Pro (Google Imagen 3 Pro Image)** - поддерживает референсные изображения.

## Изменения

### Новые файлы
- `style_transfer_imagen.py` - новые функции на базе Imagen
  - `apply_style_transfer_imagen()` - style transfer через Nano Banana Pro
  - `generate_with_style_guide_imagen()` - style guide через Nano Banana Pro

### Упрощение workflow

#### Style Transfer (было → стало)
**Было (Stability AI):**
1. Загрузить init image
2. Загрузить style image
3. Ввести prompt
4. Ввести negative prompt
5. Ввести style_strength (0.1-1.0)
6. Ввести composition_fidelity (0.1-1.0)
7. Ввести change_strength (0.1-1.0)

**Стало (Imagen):**
1. Загрузить init image
2. Загрузить style image
3. Ввести prompt (опционально)
4. ✅ Готово!

#### Style Guide (было → стало)
**Было (Stability AI):**
1. Загрузить style image
2. Ввести prompt
3. Ввести negative prompt
4. Ввести aspect ratio
5. Ввести fidelity (0.1-1.0)

**Стало (Imagen):**
1. Загрузить style image
2. Ввести prompt
3. ✅ Готово!

## Изменения в bot.py

### Импорты
```python
# Добавить
from style_transfer_imagen import apply_style_transfer_imagen, generate_with_style_guide_imagen
```

### Style Transfer обработчик
Заменить весь блок обработки параметров на:

```python
if st_state["step"] == "prompt":
    text = update.message.text.strip()
    prompt = text if text and text != "-" else ""

    # Переводим промпт на английский если указан
    if prompt:
        await update.message.reply_text("⏳ Перевод промпта...")
        prompt = translate_to_english(prompt, "gpt-4o")

    # Запускаем генерацию через Imagen
    await update.message.reply_text(
        "🍌💎 <b>Применение стиля через Nano Banana Pro...</b>\\n\\n"
        "Это может занять 30-60 секунд...",
        parse_mode="HTML"
    )

    try:
        result = apply_style_transfer_imagen(
            init_image=st_state["init_image"],
            style_image=st_state["style_image"],
            prompt=prompt,
            aspect_ratio="1:1"
        )

        if result and len(result) > 0:
            result[0].seek(0)
            watermarked_image = add_watermark(result[0])
            await context.bot.send_photo(uid, watermarked_image)
            await context.bot.send_message(
                uid,
                "✅ <b>Style Transfer завершен!</b>\\n\\n"
                "🍌💎 Использован Nano Banana Pro",
                parse_mode="HTML"
            )
        else:
            await update.message.reply_text("❌ Не удалось применить стиль")

    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {str(e)}")

    user_state[uid]["style_transfer"] = {"active": False}
    return
```

### Style Guide обработчик
Аналогично упростить - только 2 шага вместо 5.

## Преимущества

1. **Простота** - 3 шага вместо 7 для style transfer
2. **Качество** - Imagen 3 лучше понимает стили
3. **Скорость** - меньше ввода параметров
4. **Надежность** - меньше точек отказа

## Миграционный скрипт

Создать `migrate_style_transfer.py` для автоматической замены логики в bot.py.
