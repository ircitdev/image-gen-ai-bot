async def generate_dalle_image(query, uid):
    """Генерирует изображение через DALL-E"""
    from state import user_state
    from user_limits import can_generate, use_generation
    from dalle_api import generate_with_dalle
    from watermark import add_watermark
    from image_library import add_to_history
    from keyboards import actions_kb
    from openai_helper import translate_to_english

    st = user_state[uid]

    # Получаем параметры
    prompt = st.get("prompt", "")
    dalle_model = st.get("dalle_model", "dall-e-3")
    dalle_size = st.get("dalle_size", "1024x1024")
    dalle_quality = st.get("dalle_quality", "standard")

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

    await query.edit_message_text("⏳ Перевод промпта с помощью ChatGPT...")
    english_prompt = translate_to_english(prompt, gpt_model)

    await query.edit_message_text(f"⏳ Генерация изображения через {dalle_model.upper()}...")

    # Генерируем через DALL-E
    result = generate_with_dalle(english_prompt, dalle_model, dalle_size, dalle_quality)

    # Проверяем результат
    if isinstance(result, str):
        # Ошибка
        await query.edit_message_text(f"❌ {result}")
        return

    # Используем генерацию
    remaining = use_generation(uid)

    # Добавляем watermark
    watermarked = add_watermark(result)

    # Отправляем изображение
    await query.message.reply_photo(
        photo=watermarked,
        caption=f"✅ Изображение создано!\n\n"
                f"<b>Промпт:</b> {prompt}\n"
                f"<b>Модель:</b> {dalle_model}\n"
                f"<b>Размер:</b> {dalle_size}\n"
                f"<b>Качество:</b> {dalle_quality}\n\n"
                f"💎 Осталось генераций: {remaining}",
        reply_markup=actions_kb(),
        parse_mode="HTML"
    )

    # Сохраняем в историю
    add_to_history(uid, prompt, dalle_model, "DALL-E")

    # Сохраняем параметры для повторной генерации
    st["saved_params"] = {
        "model": dalle_model,
        "engine": "dalle",
        "size": dalle_size,
        "quality": dalle_quality
    }
    st["images"] = [result]

    await query.edit_message_text("✅ Готово!")
