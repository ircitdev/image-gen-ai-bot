# ImageGen Bot - Полная документация проекта

## Обзор

**ImageGen Bot** - это мощный Telegram-бот для генерации изображений с использованием искусственного интеллекта. Бот предоставляет доступ к нескольким передовым AI-моделям для создания уникальных изображений по текстовому описанию.

### Основные характеристики

| Параметр | Значение |
|----------|----------|
| **Платформа** | Telegram Bot API |
| **Язык** | Python 3.10+ |
| **Сервер** | Ubuntu 22.04, 31.44.7.144 |
| **Расположение** | `/root/bots/usp/` |
| **Bot Token** | @imagegen_bot (ID: 8537012658) |

---

## Архитектура системы

### Технологический стек

| Компонент | Технология | Версия |
|-----------|------------|--------|
| Runtime | Python | 3.10.12 |
| Bot Framework | python-telegram-bot | 20.x |
| HTTP Client | requests | 2.31+ |
| Image Processing | Pillow | 10.x |
| Environment | python-dotenv | 1.0+ |
| Cloud Storage | Google Cloud Storage | 2.x |
| Logging | Google Sheets API | v4 |
| AI Models | Stability.ai, OpenAI, Google AI | Latest |

### Структура проекта

```
/root/bots/usp/
├── bot.py                    # Главный файл бота (180KB, 4000+ строк)
├── settings.py               # Конфигурация и переменные окружения
├── state.py                  # Управление состоянием пользователей
├── .env                      # Переменные окружения (API ключи)
│
├── # Модули генерации изображений
├── dream_api.py              # Stability.ai SD 3.5 API
├── dalle_api.py              # OpenAI DALL-E API
├── dalle_gen_helper.py       # Хелпер для DALL-E генерации
├── imagen_api.py             # Google Imagen 3 API (Nano Banana 3)
├── imagen_gen_helper.py      # Хелпер для Imagen генерации
│
├── # AI инструменты редактирования
├── ai_tools.py               # Upscale, Remove BG, Inpaint и др.
├── openai_helper.py          # ChatGPT для обработки промптов
├── style_transfer.py         # Перенос стиля
├── style_guide.py            # Генерация по референсу
├── sketch.py                 # Генерация из скетча
│
├── # UI и клавиатуры
├── keyboards.py              # Inline клавиатуры
├── keyboards_addon.py        # Расширенные клавиатуры
│
├── # Бизнес-логика
├── user_limits.py            # Лимиты и подписки
├── payments.py               # Платежная система
├── image_library.py          # Библиотека изображений
├── presets.py                # Пресеты настроек
├── watermark.py              # Водяные знаки
│
├── # Интеграции
├── gcs_helper.py             # Google Cloud Storage
├── gcs_advanced.py           # Расширенные GCS функции
├── gsheets_logger.py         # Логирование в Google Sheets
│
├── # Веб-компоненты
├── webapp_server.py          # Flask сервер для Mini App
├── mask_server.py            # Сервер для Inpaint масок
├── static/                   # Статические файлы
│   └── inpaint_editor.html   # Mini App редактор масок
│
├── # Данные
├── data/                     # Данные пользователей
├── user_limits.json          # Лимиты пользователей
├── user_library.json         # Библиотека пользователей
├── user_presets.json         # Пресеты пользователей
├── image_library.json        # Глобальная библиотека
│
├── # Документация
├── README.md                 # Основной README
├── help.html                 # HTML справка
├── STYLE_COMMANDS.md         # Справка по стилям
├── GCS_SETUP.md              # Настройка GCS
│
└── # Конфигурация
    ├── tgbots-google-cloud.json    # GCS credentials
    ├── tgbots-google-sheets.json   # Sheets credentials
    ├── Dockerfile
    ├── docker-compose.yml
    └── requirements.txt
```

---

## Движки генерации изображений

### 1. Stable Diffusion 3.5 (Stability.ai)

**Основной движок** с максимальными возможностями настройки.

| Модель | Время | Описание |
|--------|-------|----------|
| SD 3.5 Large | ~45 сек | Максимальное качество и детализация |
| SD 3.5 Large Turbo | ~30 сек | Баланс качества и скорости |
| SD 3.5 Medium | ~25 сек | Средний баланс |
| SD 3.5 Flash | ~15 сек | Максимальная скорость |

**Поддерживаемые форматы:**
- 1:1 (квадрат)
- 16:9, 21:9 (горизонтальные)
- 9:16, 9:21 (вертикальные)
- 3:2, 2:3, 5:4, 4:5 (классические)

**18 стилей:**
- Photographic, Cinematic, Anime
- 3D Model, Digital Art, Fantasy Art
- Comic Book, Pixel Art, Line Art
- Neon Punk, Low Poly, Isometric
- Analog Film, Origami, и др.

**Дополнительные параметры:**
- 8 видов съемки (establishing, closeup, wide, etc.)
- 9 ракурсов камеры (low angle, aerial, drone shot, etc.)
- 8 типов освещения (golden hour, studio, dramatic, etc.)
- Negative prompt для исключения элементов

### 2. DALL-E (OpenAI)

**Альтернативный движок** с высоким качеством.

| Модель | Размеры | Качество |
|--------|---------|----------|
| DALL-E 3 | 1024x1024, 1024x1792, 1792x1024 | Standard, HD |
| DALL-E 2 | 256x256, 512x512, 1024x1024 | Standard |

### 3. Nano Banana 3 (Google Imagen 3) - НОВЫЙ!

**Новейший движок** на базе Google AI Studio.

| Характеристика | Значение |
|----------------|----------|
| Модель | imagen-3.0-generate-001 |
| API | Google Generative Language API |
| Форматы | 1:1, 3:4, 4:3, 9:16, 16:9 |
| Цена | ~$0.03/изображение |

---

## Функциональные возможности

### Генерация изображений

#### Команда `/new`
Запускает процесс генерации нового изображения:
1. Выбор движка (SD / DALL-E / Nano Banana 3)
2. Выбор модели/формата
3. Выбор стиля (для SD)
4. Дополнительные параметры (опционально)
5. Negative prompt (опционально)
6. Подтверждение и генерация

#### Поддержка URL
Бот умеет:
- Извлекать контент из URL
- Создавать обложки для статей
- Генерировать изображения по содержимому страниц

### AI-инструменты редактирования

| Инструмент | Описание | API |
|------------|----------|-----|
| **Upscale** | Увеличение разрешения в 2x | Stability.ai |
| **Remove Background** | Удаление фона (PNG) | Stability.ai |
| **Face Restore** | Улучшение деталей лица | Stability.ai |
| **Variations** | Создание вариаций | Stability.ai SD3 i2i |
| **Inpaint** | Редактирование по маске | Stability.ai |
| **Outpaint** | Расширение изображения | Stability.ai |
| **Search & Recolor** | Поиск и перекраска объекта | Stability.ai |
| **Search & Replace** | Поиск и замена объекта | Stability.ai |
| **Erase Object** | Удаление объекта | Stability.ai |

### Inpaint Editor (Mini App)

Telegram Mini App для рисования масок:
- Веб-редактор с кистью
- Регулировка размера кисти
- Предпросмотр маски
- Интеграция с GCS

**URL:** `https://imagegen.tools.uspeshnyy.ru/static/inpaint_editor.html`

### Дополнительные режимы

#### Style Guide
Генерация изображений с использованием референса стиля:
- Загрузка референс-изображения
- Выбор fidelity (0.3 / 0.6 / 1.0)
- Выбор aspect ratio

#### Style Transfer
Перенос стиля с одного изображения на другое.

#### Sketch to Image
Генерация по нарисованному скетчу.

### Команда `/editmy`
Редактирование своего изображения без генерации:
- Загрузка изображения
- Применение AI-инструментов
- Использование как референс

---

## Система пользователей

### Лимиты генераций

| Тип | Лимит | Описание |
|-----|-------|----------|
| Бесплатно | 10 генераций | Для новых пользователей |
| Starter | 50 генераций | Базовый пакет |
| Pro | 150 генераций | Расширенный пакет |
| Premium | 500 генераций | Максимальный пакет |
| Unlimited | Безлимит на месяц | VIP подписка |

### Команды управления

| Команда | Описание |
|---------|----------|
| `/stats` | Статистика генераций |
| `/buy` | Покупка генераций |
| `/presets` | Управление пресетами |
| `/library` | Библиотека изображений |
| `/ref` | Реферальная программа |

### Реферальная система

- Уникальная реферальная ссылка для каждого пользователя
- Бонусные генерации за приглашенных друзей
- Автоматическое начисление наград

---

## Платежная система

### Telegram Stars

Встроенные платежи через Telegram:
- Мгновенная активация
- Безопасные транзакции
- Pre-checkout валидация

### CryptoBot (USDT)

Криптовалютные платежи:
- Поддержка USDT
- Автоматическая проверка оплаты
- Webhook интеграция

### Пакеты

| Пакет | Генерации | Цена (Stars) | Цена (USDT) |
|-------|-----------|--------------|-------------|
| Starter | 50 | 100 | $3 |
| Pro | 150 | 250 | $7 |
| Premium | 500 | 700 | $18 |
| Unlimited | Безлимит/мес | 1500 | $35 |

---

## Интеграции

### Google Cloud Storage

Хранение изображений в облаке:
- Bucket: `tgbots-images`
- Публичные URL для доступа
- Организация по папкам (generations, inpaint, library)

### Google Sheets Logging

Логирование активности:
- Spreadsheet ID: `1TsPo12VGW8u9YmcEhWHcIL-6yWCZ0_svBgku9fTaE0s`
- Запись всех генераций
- Статистика по пользователям
- Аналитика использования

### ChatGPT Integration

Обработка промптов через GPT:
- Перевод на английский
- Улучшение промптов
- Добавление деталей
- Выбор модели (GPT-4o / GPT-5)

---

## API Ключи и конфигурация

### Требуемые переменные окружения

```env
# Telegram
TELEGRAM_BOT_TOKEN=your_bot_token

# Stability.ai (SD 3.5, AI Tools)
STABILITY_API_KEY=sk-xxx

# OpenAI (DALL-E, ChatGPT)
OPENAI_API_KEY=sk-xxx

# Google AI Studio (Imagen 3)
GOOGLE_AI_API_KEY=AIzaxxx

# CryptoBot
CRYPTOBOT_TOKEN=xxx
CRYPTOBOT_CURRENCY=USDT

# Google Cloud Storage
USE_GCS=true
GCS_BUCKET_NAME=tgbots-images
GCS_CREDENTIALS_PATH=tgbots-google-cloud.json

# Google Sheets
GSHEETS_LOGGING=true
GSHEETS_SPREADSHEET_ID=xxx
GSHEETS_CREDENTIALS_PATH=tgbots-google-sheets.json

# Web Server
WEBAPP_URL=https://imagegen.tools.uspeshnyy.ru
```

---

## Пользовательский интерфейс

### Inline клавиатуры

Бот использует интерактивные inline-клавиатуры для:
- Навигации по меню
- Выбора параметров
- Подтверждения действий
- Доступа к функциям

### Inline режим

Использование бота в любом чате:
```
@botname промпт для генерации
```

### Watermark

Автоматическое добавление водяного знака:
- Логотип USP
- Прозрачность
- Позиционирование в углу

---

## Сценарии использования

### 1. Быстрая генерация

```
Пользователь: /new
Пользователь: Космический корабль на орбите Марса
Бот: [Выбор движка] → [Выбор формата] → [Генерация]
Результат: Изображение + меню действий
```

### 2. Профессиональная генерация

```
1. /new
2. Выбор Stable Diffusion 3.5 Large
3. Выбор формата 16:9
4. Выбор стиля "Cinematic"
5. Дополнительные параметры:
   - Вид: wide shot
   - Ракурс: aerial
   - Освещение: golden hour
6. Negative prompt: "blur, low quality"
7. Генерация
```

### 3. Редактирование изображения

```
1. /editmy
2. Загрузка изображения
3. Выбор инструмента:
   - Upscale для увеличения
   - Remove BG для удаления фона
   - Inpaint для дорисовки
```

### 4. Генерация по референсу

```
1. Генерация изображения
2. Кнопка "Использовать как референс"
3. Ввод нового промпта
4. Выбор fidelity (степень схожести)
5. Генерация в стиле референса
```

---

## Целевая аудитория

### Основные группы

1. **Дизайнеры и художники**
   - Поиск референсов
   - Быстрые концепты
   - Эксперименты со стилями

2. **Контент-мейкеры**
   - Обложки для статей/видео
   - Иллюстрации для постов
   - Визуальный контент

3. **Маркетологи**
   - Рекламные материалы
   - Баннеры
   - Социальные сети

4. **Разработчики**
   - Placeholder изображения
   - Mockups
   - Тестовый контент

5. **Обычные пользователи**
   - Творческие эксперименты
   - Аватарки
   - Подарки и открытки

---

## Администрирование

### Admin ID

```python
ADMIN_ID = 65876198
```

### Админ-команды

| Команда | Описание |
|---------|----------|
| `/admin_stats` | Общая статистика |
| `/admin_users` | Список пользователей |
| `/admin_add` | Добавить генерации |
| `/admin_broadcast` | Рассылка |

### Логирование

- Консольный вывод с метками времени
- Файл `bot.log`
- Google Sheets для аналитики

---

## Развертывание

### Запуск

```bash
# Через скрипт
./start_imagegen.sh

# Или вручную
cd /root/bots/usp
nohup python3 -u bot.py > bot.log 2>&1 &
nohup python3 webapp_server.py > webapp_server.log 2>&1 &
nohup python3 mask_server.py > mask_server.log 2>&1 &
```

### Docker

```bash
docker-compose up -d
```

### Мониторинг

```bash
# Логи бота
tail -f /root/bots/usp/bot.log

# Проверка процессов
ps aux | grep 'bots/usp'
```

---

## Обновления

### v2.2.0 (2024-12-21)
- Добавлена интеграция Google Imagen 3 (Nano Banana 3)
- Новый движок генерации с 5 форматами
- Упрощенный поток для Imagen (без стилей)

### v2.1.0 (2024-11-17)
- Advanced Image Library System
- Google Cloud Storage интеграция
- Google Sheets логирование
- Telegram Mini App для Inpaint

### v2.0.0 (2024-11-15)
- Stable Diffusion 3.5 поддержка
- DALL-E интеграция
- Множественные AI инструменты
- Платежная система

---

## Контакты и поддержка

- **Telegram Bot:** @imagegen_bot
- **Разработчик:** @uspeshnyy
- **Сервер:** 31.44.7.144

---

*Документация обновлена: 21 декабря 2024*
