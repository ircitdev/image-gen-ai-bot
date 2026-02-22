# ⚠️ Imagen 3 Custom - Временно недоступен

## Дата: 2026-02-22

## Проблема

Google изменил API для Imagen 3 Customization. Модель **`imagen-3.0-capability-001`** больше не доступна через predict endpoint.

### Ошибка API:
```json
{
  "error": {
    "code": 404,
    "message": "models/imagen-3.0-capability-001 is not found for API version v1beta, or is not supported for predict. Call ListModels to see the list of available models and their supported methods.",
    "status": "NOT_FOUND"
  }
}
```

### Endpoint (не работает):
```
https://generativelanguage.googleapis.com/v1beta/models/imagen-3.0-capability-001:predict
```

## Что сделано

### 1. Временно отключена функция
- ✅ Убрана кнопка "👤 Imagen 3 Custom (с фото)" из меню
- ✅ Добавлено информативное сообщение об ошибке
- ✅ Пользователям предлагаются альтернативы

### 2. Изменённые файлы
- `imagen3_custom_api.py` - добавлено сообщение об ошибке в начале функции
- `keyboards.py` - закомментирована кнопка Imagen 3 Custom

### 3. Код отключения
```python
# imagen3_custom_api.py
def generate_with_imagen3_custom(...):
    # ВРЕМЕННОЕ ОТКЛЮЧЕНИЕ
    raise Exception(
        "⚠️ Imagen 3 Custom временно недоступен\n\n"
        "Google изменил API, модель imagen-3.0-capability-001 больше не поддерживается.\n"
        "Пожалуйста, используйте другие движки:\n"
        "• 🍌 Nano Banana 4 (Imagen 4) - text-to-image\n"
        "• 🤖 DALL-E 3 - text-to-image\n"
        "• 🎨 Stable Diffusion 3.5 - text-to-image"
    )
```

## Возможные решения

### Вариант 1: Использовать Imagen 2
```python
IMAGEN3_CUSTOM_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/imagen-2.0-generate-001:predict"
```

**Проблема:** Imagen 2 может не поддерживать subject customization с референсами.

### Вариант 2: Использовать Imagen 4
```python
IMAGEN3_CUSTOM_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/imagen-4.0-generate-001:predict"
```

**Проблема:** Imagen 4 тоже может не поддерживать `referenceType: "SUBJECT"`.

### Вариант 3: Найти актуальный endpoint
Нужно проверить официальную документацию Google AI Studio для:
- Актуального списка моделей
- Правильного endpoint для customization
- Поддерживаемых параметров

### Вариант 4: Использовать другой API
Возможно, функция перенесена в:
- Google Cloud Vertex AI
- Другой продукт Google

## Проверочный код

Для проверки доступных моделей:
```bash
curl "https://generativelanguage.googleapis.com/v1beta/models?key=YOUR_API_KEY"
```

Или через Python:
```python
import requests

url = f"https://generativelanguage.googleapis.com/v1beta/models?key={GOOGLE_AI_API_KEY}"
response = requests.get(url)
models = response.json()

# Ищем Imagen модели
for model in models.get('models', []):
    if 'imagen' in model.get('name', '').lower():
        print(model['name'])
        print(model.get('supportedGenerationMethods', []))
        print('---')
```

## Текущий статус

| Функция | Статус | Примечание |
|---------|--------|------------|
| Imagen 4 (text-to-image) | ✅ Работает | imagen-4.0-generate-001 |
| Imagen 3 Custom | ❌ Отключено | API недоступен |
| DALL-E 3 | ✅ Работает | |
| Stable Diffusion 3.5 | ✅ Работает | |

## Действия пользователей

Если пользователь попытается использовать Imagen 3 Custom (через старую ссылку или callback):
1. Получит сообщение: "⚠️ Imagen 3 Custom временно недоступен"
2. Увидит рекомендации использовать другие движки
3. Функция не появляется в меню (кнопка скрыта)

## TODO для разработчика

- [ ] Проверить список доступных моделей через API
- [ ] Найти актуальную документацию Google
- [ ] Определить правильный endpoint для customization
- [ ] Протестировать альтернативные модели
- [ ] Обновить код при нахождении решения
- [ ] Вернуть кнопку в меню после исправления

## Ссылки

- Google AI Studio: https://ai.google.dev/
- API Docs: https://ai.google.dev/api
- Gemini API (возможно, там Imagen): https://ai.google.dev/gemini-api/docs

## Версия

- **Bot version:** 2.3.1
- **Issue date:** 2026-02-22
- **Status:** 🔴 DISABLED
- **Priority:** Medium (есть альтернативы)

---

**Note:** Функция будет восстановлена, как только Google предоставит актуальный API endpoint для Imagen customization с референсными изображениями.
