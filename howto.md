# Развертывание AI Image Generation Bot на сервере

## Выполненные задачи:

1. **Локальный бот остановлен** ✅
   - Процесс Python (PID 22564) остановлен

2. **Проект загружен на сервер** ✅
   - Сервер: root@31.44.7.144
   - Путь: ~/bots/usp/
   - Все файлы загружены

3. **Токены настроены** ✅
   - .env файл создан с токенами из локального git
   - TELEGRAM_BOT_TOKEN: 8537012658:AAHf...
   - STABILITY_API_KEY: sk-EJwo...
   - OPENAI_API_KEY: sk-proj-mkPl...
   - CRYPTOBOT_TOKEN: 481838:AAvw...

4. **Docker контейнер запущен** ✅
   - Образ собран: usp-telegram-bot
   - Контейнер: image-gen-ai-bot
   - Статус: **Up and Running**

## Логи бота:
```
Bot started successfully...
Inline mode enabled - users can use @botname in any chat
Payment system enabled - Telegram Stars + CryptoBot
Menu commands set successfully
```

Бот работает на сервере в Docker контейнере с автоперезапуском (restart: unless-stopped).

## Полезные команды на сервере:

```bash
# Подключиться к серверу
ssh root@31.44.7.144

# Перейти в папку проекта
cd ~/bots/usp/

# Смотреть логи в реальном времени
docker compose logs -f

# Смотреть последние 100 строк логов
docker compose logs --tail=100

# Перезапустить бот
docker compose restart

# Остановить бот
docker compose down

# Запустить бот
docker compose up -d

# Пересобрать и запустить бот (после изменений кода)
docker compose up -d --build

# Проверить статус контейнера
docker compose ps

# Проверить использование ресурсов
docker stats image-gen-ai-bot
```

## Обновление кода на сервере:

```bash
# На локальной машине: создать архив
cd K:\scripts\usp\imagegen
tar -czf ../project.tar.gz --exclude='.git' --exclude='__pycache__' --exclude='*.pyc' --exclude='.env' --exclude='user_limits.json' --exclude='user_library.json' --exclude='user_presets.json' --exclude='.vscode' --exclude='.idea' --exclude='examples' --exclude='.claude' .

# Загрузить на сервер
scp ../project.tar.gz root@31.44.7.144:~/bots/usp/

# На сервере: распаковать и перезапустить
ssh root@31.44.7.144 "cd ~/bots/usp/ && tar -xzf project.tar.gz && rm project.tar.gz && docker compose up -d --build"
```

## Структура на сервере:

```
~/bots/usp/
├── bot.py                    # Основной файл бота
├── ai_tools.py               # AI инструменты (Upscale, Variations, etc.)
├── payments.py               # Система платежей
├── user_limits.py            # Лимиты и рефералы
├── settings.py               # Настройки (использует .env)
├── .env                      # Токены и ключи API
├── docker-compose.yml        # Docker Compose конфигурация
├── Dockerfile                # Docker образ
├── requirements.txt          # Python зависимости
├── data/                     # Папка для данных (volume)
├── user_limits.json          # База лимитов пользователей
├── user_library.json         # Библиотека изображений
└── user_presets.json         # Пресеты пользователей
```

## Редактирование .env на сервере:

```bash
# Редактировать .env файл
ssh root@31.44.7.144 "nano ~/bots/usp/.env"

# После изменений - перезапустить
ssh root@31.44.7.144 "cd ~/bots/usp/ && docker compose restart"
```

## Мониторинг:

```bash
# Проверить, работает ли бот
ssh root@31.44.7.144 "docker ps | grep image-gen"

# Посмотреть ошибки в логах
ssh root@31.44.7.144 "cd ~/bots/usp/ && docker compose logs | grep -i error"

# Проверить использование диска
ssh root@31.44.7.144 "df -h ~/bots/usp/"
```

## Бэкап данных:

```bash
# Скачать базы данных пользователей
scp root@31.44.7.144:~/bots/usp/user_limits.json ./backup/
scp root@31.44.7.144:~/bots/usp/user_library.json ./backup/
scp root@31.44.7.144:~/bots/usp/user_presets.json ./backup/
```

## Troubleshooting:

### Бот не отвечает:
```bash
# Проверить логи
docker compose logs --tail=100

# Перезапустить
docker compose restart
```

### Ошибка "Out of memory":
```bash
# Проверить использование памяти
docker stats

# Увеличить лимит памяти в docker-compose.yml
```

### Проблемы с API:
```bash
# Проверить .env файл
cat .env

# Проверить, что токены загружены
docker compose exec telegram-bot env | grep API
```
