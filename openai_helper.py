"""
Модуль для работы с OpenAI ChatGPT-4o
Используется для:
- Улучшения промптов
- Извлечения и суммаризации текста из URL
- Перевода промптов на английский
"""

from openai import OpenAI
from settings import OPENAI_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY)

def improve_prompt(text: str, model: str = "gpt-4o") -> str:
    """
    Улучшает промпт для генерации изображений с помощью ChatGPT-4o
    """
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an expert in creating detailed prompts for AI image generation. "
                        "Improve the given prompt by adding artistic details, specific style descriptions, "
                        "lighting conditions, and composition suggestions. "
                        "Keep the core idea but make it more detailed and visually descriptive. "
                        "Respond ONLY with the improved prompt, nothing else."
                    )
                },
                {
                    "role": "user",
                    "content": text
                }
            ],
            temperature=0.7,
            max_tokens=500
        )

        improved = response.choices[0].message.content.strip()
        print(f"[OK] Prompt improved by ChatGPT: {improved[:100]}...")
        return improved

    except Exception as e:
        print(f"[ERROR] Improve prompt failed: {e}")
        return text  # Возвращаем оригинал при ошибке


def translate_to_english(text: str, model: str = "gpt-4o") -> str:
    """
    Переводит текст на английский язык
    """
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a professional translator. "
                        "Translate the following text to English. "
                        "If the text is already in English, return it as is. "
                        "Respond ONLY with the translation, nothing else."
                    )
                },
                {
                    "role": "user",
                    "content": text
                }
            ],
            temperature=0.3,
            max_tokens=500
        )

        translated = response.choices[0].message.content.strip()
        print(f"[OK] Translated to English: {translated[:100]}...")
        return translated

    except Exception as e:
        print(f"[ERROR] Translation failed: {e}")
        import traceback
        traceback.print_exc()
        return text  # Возвращаем оригинал при ошибке


def summarize_url_content(url: str, text_content: str) -> str:
    """
    Создает краткое саммари текста со страницы для создания обложки НА РУССКОМ ЯЗЫКЕ
    """
    try:
        print(f"[INFO] Calling ChatGPT to summarize URL content...")
        print(f"[INFO] Text length: {len(text_content)} characters")

        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Ты эксперт по созданию описаний для обложек статей. "
                        "На основе текста статьи создай детальное описание для обложки изображения. "
                        "Сфокусируйся на главной теме, настроении и ключевых визуальных элементах. "
                        "ВАЖНО: Ответ должен быть НА РУССКОМ ЯЗЫКЕ и описывать что должно быть на изображении. "
                        "Отвечай ТОЛЬКО описанием для изображения, ничего больше."
                    )
                },
                {
                    "role": "user",
                    "content": f"URL: {url}\n\nСодержание статьи:\n{text_content[:2000]}"  # Ограничиваем длину
                }
            ],
            temperature=0.7,
            max_tokens=500
        )

        summary = response.choices[0].message.content.strip()
        print(f"[OK] Summary created for URL (in Russian): {summary[:100]}...")
        return summary

    except Exception as e:
        print(f"[ERROR] Summary creation failed: {e}")
        import traceback
        traceback.print_exc()
        return f"Создай обложку для этой статьи"  # Fallback на русском


def build_final_prompt(base_prompt: str, params: dict, model: str = "gpt-4o") -> str:
    """
    Создает финальный промпт для генерации на английском с учетом параметров

    Важно: параметры не противоречат основному тексту, а дополняют его

    Args:
        base_prompt: Основной текст промпта (на русском или английском)
        params: Словарь с параметрами (model, format, style)

    Returns:
        Финальный промпт на английском для Stable Diffusion
    """
    # Переводим ТОЛЬКО основной текст на английский
    print(f"[INFO] Translating base prompt to English...")
    english_prompt = translate_to_english(base_prompt, model)

    # Style передается через API параметры (style_preset)
    # Модель и формат также передаются отдельно
    # Поэтому просто возвращаем переведенный промпт с базовым качеством

    # Добавляем базовое качество для лучших результатов
    components = [english_prompt, "high quality, detailed"]

    # Собираем все вместе
    final_prompt = ', '.join(components)

    print(f"[OK] Final prompt for generation: {final_prompt[:200]}...")
    return final_prompt


def enhance_prompt_for_generation(prompt: str, translate: bool = True) -> str:
    """
    Полный цикл обработки промпта:
    1. Переводит на английский (если нужно)
    2. Улучшает детали

    Args:
        prompt: Исходный промпт
        translate: Переводить ли на английский (по умолчанию True)

    Returns:
        Обработанный промпт готовый для генерации
    """
    # Проверяем, нужен ли перевод
    if translate:
        prompt = translate_to_english(prompt)

    # Улучшаем промпт
    # improved = improve_prompt(prompt)

    return prompt  # Возвращаем переведенный (улучшение можно включить по желанию)
