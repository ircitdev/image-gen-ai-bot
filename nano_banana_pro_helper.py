"""
Helper function for generating images with Nano Banana Pro (Gemini 3 Pro Image)
Supports: Text-to-image with optional reference images
"""

async def generate_nano_banana_pro_image(query, uid):
    """Генерирует изображение через Nano Banana Pro с поддержкой референсов"""
    from state import user_state
    from user_limits import can_generate, use_generation
    from nano_banana_pro_api import generate_with_nano_banana_pro
    from watermark import add_watermark
    from image_library import add_to_history
    from keyboards import actions_kb
    from openai_helper import translate_to_english
    import gsheets_logger as gsl

    st = user_state[uid]

    # Получаем параметры
    prompt = st.get("prompt", "")
    imagen_format = st.get("imagen_format", "1:1")
    reference_images = st.get("nbp_reference_images", [])  # Референсы для Nano Banana Pro

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

    if reference_images:
        await query.edit_message_text(
            f"🍌💎 Перевод промпта...\n\n"
            f"Референсов: {len(reference_images)}"
        )
    else:
        await query.edit_message_text("🍌💎 Перевод промпта с помощью ChatGPT...")

    english_prompt = translate_to_english(prompt, gpt_model)

    # Сохраняем английский промпт
    st["last_english_prompt"] = english_prompt

    if reference_images:
        await query.edit_message_text(
            f"🍌💎 Генерация через Nano Banana Pro...\n\n"
            f"Формат: {imagen_format}\n"
            f"С {len(reference_images)} референс(ами)"
        )
    else:
        await query.edit_message_text(
            f"🍌💎 Генерация через Nano Banana Pro...\n\n"
            f"Формат: {imagen_format}"
        )

    try:
        # Генерируем через Nano Banana Pro
        images = generate_with_nano_banana_pro(
            english_prompt,
            reference_images=reference_images if reference_images else None,
            aspect_ratio=imagen_format,
            num_images=1
        )

        if not images:
            await query.edit_message_text("❌ Не удалось сгенерировать изображение. Попробуйте другой промпт.")
            return

        result = images[0]

    except Exception as e:
        error_msg = str(e)
        print(f"[Nano Banana Pro Error] {error_msg}")
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

    # Очищаем референсы после генерации
    st["nbp_reference_images"] = []

    # Формируем caption
    if reference_images:
        caption = (
            f"🍌💎 <b>Nano Banana Pro</b> (с референсом)\n\n"
            f"<b>Промпт:</b> {prompt}\n"
            f"<b>Формат:</b> {imagen_format}\n"
            f"<b>Референсов:</b> {len(reference_images)}\n\n"
            f"💎 Осталось генераций: {remaining}"
        )
    else:
        caption = (
            f"🍌💎 <b>Nano Banana Pro</b>\n\n"
            f"<b>Промпт:</b> {prompt}\n"
            f"<b>Формат:</b> {imagen_format}\n\n"
            f"💎 Осталось генераций: {remaining}"
        )

    # Отправляем изображение
    await query.message.reply_photo(
        photo=watermarked,
        caption=caption,
        reply_markup=actions_kb(),
        parse_mode="HTML"
    )

    # Сохраняем в историю
    add_to_history(uid, prompt, "nano-banana-pro", "Nano Banana Pro")

    # Логируем в Google Sheets
    try:
        gsl.log_generation(uid, prompt, "nano-banana-pro-preview", imagen_format, "Nano Banana Pro")
    except Exception as e:
        print(f"[GSL Error] {e}")

    # Сохраняем параметры для повторной генерации
    st["saved_params"] = {
        "model": "nano-banana-pro-preview",
        "engine": "nano_banana_pro",
        "format": imagen_format
    }

    await query.edit_message_text("🍌💎 Готово!")
