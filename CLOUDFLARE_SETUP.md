# Настройка Cloudflare Worker для генерации изображений

## Шаг 1: Получить Hugging Face API токен

1. Зайдите на https://huggingface.co
2. Зарегистрируйтесь или войдите
3. Перейдите в Settings → Access Tokens: https://huggingface.co/settings/tokens
4. Создайте новый токен (Read access достаточно)
5. Скопируйте ваш токен

## Шаг 2: Развернуть Worker на Cloudflare

### Вариант А: Через веб-интерфейс

1. Зайдите на https://workers.cloudflare.com
2. Войдите или зарегистрируйтесь (бесплатно)
3. Нажмите "Create a Service"
4. Дайте имя worker'у (например: `image-generator`)
5. Нажмите "Quick Edit"
6. Удалите весь код и вставьте содержимое файла `cloudflare-worker.js`
7. Нажмите "Save and Deploy"

### Вариант Б: Через Wrangler CLI

```bash
npm install -g wrangler
wrangler login
wrangler init image-generator
# Скопируйте код из cloudflare-worker.js в src/index.js
wrangler deploy
```

## Шаг 3: Настроить переменные окружения

1. В панели Cloudflare Workers перейдите в Settings → Variables
2. Добавьте переменную окружения:
   - Name: `HUGGINGFACE_TOKEN`
   - Value: `ваш_токен_от_huggingface`
3. Сохраните

## Шаг 4: Получить URL вашего Worker

После деплоя вы получите URL вида:
```
https://image-generator.your-subdomain.workers.dev
```

Скопируйте этот URL.

## Шаг 5: Обновить настройки бота

Откройте файл `settings.py` и добавьте:
```python
CLOUDFLARE_WORKER_URL = "https://your-worker.workers.dev"
```

Замените `https://your-worker.workers.dev` на ваш URL.

## Готово!

Теперь бот будет использовать ваш Cloudflare Worker для генерации изображений через бесплатное API Hugging Face.

## Стоимость

- Cloudflare Workers: 100,000 запросов/день бесплатно
- Hugging Face Inference API: бесплатно (с лимитами)

## Альтернативные модели

Можно заменить модель в worker.js на другую:
- `stabilityai/stable-diffusion-xl-base-1.0` - SDXL
- `runwayml/stable-diffusion-v1-5` - SD 1.5
- `prompthero/openjourney` - Midjourney-style
