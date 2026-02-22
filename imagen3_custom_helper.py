"""
Helper function for generating images with Google Imagen 3 Customization (Subject Conditioning)
Supports reference images for persons, animals, and products
"""

async def generate_imagen3_custom_image(query, uid):
    """Генерирует изображение через Google Imagen 3 Customization с референсными фото"""
    from state import user_state
    from user_limits import can_generate, use_generation
    from imagen3_custom_api import generate_with_imagen3_custom
    from watermark import add_watermark
    from image_library import add_to_history
    from keyboards import actions_kb
    from openai_helper import translate_to_english
    import gsheets_logger as gsl

    st = user_state[uid]

    # Получаем параметры
    prompt = st.get("prompt", "")
    reference_images = st.get("reference_images", [])
    subject_type = st.get("subject_type", "person")
    imagen_format = st.get("imagen_format", "1:1")

    # Проверяем наличие референсных изображений
    if not reference_images or len(reference_images) == 0:
        await query.edit_message_text(
            "❌ Сначала загрузите референсное фото!\n\n"
            "Отправьте 1-4 фотографии для использования в генерации.\n\n"
            "💡 <b>Требования к фото:</b>\n"
            "• Лицо/объект по центру\n"
            "• Хорошее освещение\n"
            "• Без сильных поворотов\n"
            "• Без препятствий (очки, маски)",
            parse_mode="HTML"
        )
        return

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

    # Автоматически добавляем маркер [1] в промпт если его нет
    if "[1]" not in prompt:
        # Определяем тип субъекта для промпта
        subject_word = {
            "person": "person [1]",
            "animal": "animal [1]",
            "product": "product [1]",
            "default": "subject [1]"
        }.get(subject_type, "subject [1]")

        # Вставляем маркер в начало промпта
        prompt = f"A photo of {subject_word}, {prompt}"

    # Переводим промпт на английский
    gpt_model = st.get("gpt_model", "gpt-4o")

    await query.edit_message_text("🎨 Перевод промпта с помощью ChatGPT...")
    english_prompt = translate_to_english(prompt, gpt_model)

    # Сохраняем английский промпт
    st["last_english_prompt"] = english_prompt

    await query.edit_message_text(
        f"🎨 Генерация через Imagen 3 Custom...\n\n"
        f"Референсов: {len(reference_images)}\n"
        f"Тип: {subject_type}\n"
        f"Формат: {imagen_format}"
    )

    try:
        # Генерируем через Imagen 3 Customization
        images = generate_with_imagen3_custom(
            english_prompt,
            reference_images,
            imagen_format,
            1,
            subject_type
        )

        if not images:
            await query.edit_message_text("❌ Не удалось сгенерировать изображение. Попробуйте другой промпт или фото.")
            return

        result = images[0]

    except Exception as e:
        error_msg = str(e)
        print(f"[Imagen 3 Custom Error] {error_msg}")
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
    subject_emoji = {
        "person": "👤",
        "animal": "🐾",
        "product": "📦",
        "default": "🎨"
    }.get(subject_type, "🎨")

    await query.message.reply_photo(
        photo=watermarked,
        caption=f"{subject_emoji} <b>Imagen 3 Custom</b>\n\n"
                f"<b>Промпт:</b> {st.get('prompt', '')}\n"
                f"<b>Референсов:</b> {len(reference_images)}\n"
                f"<b>Формат:</b> {imagen_format}\n\n"
                f"💎 Осталось генераций: {remaining}",
        reply_markup=actions_kb(),
        parse_mode="HTML"
    )

    # Сохраняем в историю
    add_to_history(uid, st.get("prompt", ""), "imagen-3.0-custom", "Imagen 3 Custom")

    # Логируем в Google Sheets
    try:
        gsl.log_generation(
            uid,
            st.get("prompt", ""),
            "imagen-3.0-capability-001",
            imagen_format,
            f"Imagen 3 Custom ({subject_type})"
        )
    except Exception as e:
        print(f"[GSL Error] {e}")

    # Сохраняем параметры для повторной генерации
    st["saved_params"] = {
        "model": "imagen-3.0-capability-001",
        "engine": "imagen3_custom",
        "format": imagen_format,
        "subject_type": subject_type,
        "num_references": len(reference_images)
    }

    await query.edit_message_text("🎨 Готово!")
