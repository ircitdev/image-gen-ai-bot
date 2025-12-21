"""
Helper function for generating images with Google Imagen 3 (Nano Banana 3)
"""

async def generate_imagen_image(query, uid):
    """Генерирует изображение через Google Imagen 3 (Nano Banana 3)"""
    from state import user_state
    from user_limits import can_generate, use_generation
    from imagen_api import generate_with_imagen
    from watermark import add_watermark
    from image_library import add_to_history
    from keyboards import actions_kb
    from openai_helper import translate_to_english
    import gsheets_logger as gsl

    st = user_state[uid]

    # Получаем параметры
    prompt = st.get("prompt", "")
    imagen_format = st.get("imagen_format", "1:1")

    # Проверяем лимит
    can_gen, remaining = can_generate(uid)
    if not can_gen:
        await query.edit_message_text(
            f"❌ Лимит бесплатных генераций исчерпан!\n\n"
            f"💎 Осталось: {remaining} генераций\n\n"
            f"Используйте /buy для покупки дополнительных генераций.",
            parse_mode="HTML"
        )
        return

    # Переводим промпт на английский
    gpt_model = st.get("gpt_model", "gpt-4o")

    await query.edit_message_text("🍌 Перевод промпта с помощью ChatGPT...")
    english_prompt = translate_to_english(prompt, gpt_model)

    # Сохраняем английский промпт
    st["last_english_prompt"] = english_prompt

    await query.edit_message_text(f"🍌 Генерация через Nano Banana 3...\n\nФормат: {imagen_format}")

    try:
        # Генерируем через Imagen 3
        images = generate_with_imagen(english_prompt, imagen_format, 1)

        if not images:
            await query.edit_message_text("❌ Не удалось сгенерировать изображение. Попробуйте другой промпт.")
            return

        result = images[0]

    except Exception as e:
        error_msg = str(e)
        print(f"[Imagen Error] {error_msg}")
        await query.edit_message_text(f"❌ Ошибка генерации: {error_msg}")
        return

    # Используем генерацию
    remaining = use_generation(uid)

    # Добавляем watermark
    result.seek(0)
    watermarked = add_watermark(result)

    # Сохраняем последнее изображение
    result.seek(0)
    st["last_image"] = result
    st["images"] = [result]

    # Отправляем изображение
    await query.message.reply_photo(
        photo=watermarked,
        caption=f"🍌 <b>Nano Banana 3</b>\n\n"
                f"<b>Промпт:</b> {prompt}\n"
                f"<b>Формат:</b> {imagen_format}\n\n"
                f"💎 Осталось генераций: {remaining}",
        reply_markup=actions_kb(),
        parse_mode="HTML"
    )

    # Сохраняем в историю
    add_to_history(uid, prompt, "imagen-3.0", "Nano Banana 3")

    # Логируем в Google Sheets
    try:
        gsl.log_generation(uid, prompt, "imagen-3.0-generate-001", imagen_format, "Nano Banana 3")
    except Exception as e:
        print(f"[GSL Error] {e}")

    # Сохраняем параметры для повторной генерации
    st["saved_params"] = {
        "model": "imagen-3.0-generate-001",
        "engine": "imagen",
        "format": imagen_format
    }

    await query.edit_message_text("🍌 Готово!")
