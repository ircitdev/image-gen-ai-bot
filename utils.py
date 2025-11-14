import requests
from bs4 import BeautifulSoup
from openai_helper import summarize_url_content

def extract_text_from_url(url):
    """
    Извлекает текст со страницы и создает саммари с помощью ChatGPT-4o
    """
    try:
        # Добавляем User-Agent чтобы сайт не блокировал запросы
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        r = requests.get(url, headers=headers, timeout=10)
        r.raise_for_status()  # Проверяем статус код
        soup = BeautifulSoup(r.text, "html.parser")

        # Удаляем скрипты и стили
        for script in soup(["script", "style"]):
            script.decompose()

        # Получаем чистый текст
        text = soup.get_text()

        # Очищаем от лишних пробелов
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)

        # Используем ChatGPT для создания промпта на основе контента
        summary = summarize_url_content(url, text)
        return summary

    except Exception as e:
        print(f"Ошибка при обработке URL: {e}")
        return "create a cover image for an article"
