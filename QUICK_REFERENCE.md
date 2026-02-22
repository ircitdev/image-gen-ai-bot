# Быстрая справка - USP ImageGen Bot

## 🚀 Управление ботом

### Через systemctl (рекомендуется)

```bash
# Статус
systemctl status imagegen-bot

# Запустить
systemctl start imagegen-bot

# Остановить
systemctl stop imagegen-bot

# Перезапустить
systemctl restart imagegen-bot

# Логи реального времени
journalctl -u imagegen-bot -f
```

### Через bot_control.sh

```bash
cd /root/bots/usp

# Детальный статус
./bot_control.sh status

# Запустить
./bot_control.sh start

# Остановить
./bot_control.sh stop

# Перезапустить
./bot_control.sh restart

# Логи (50 строк)
./bot_control.sh logs

# Убить зависшие процессы
./bot_control.sh cleanup
```

## 📝 Обновление бота

### Быстрое обновление (одна команда с локальной машины)

```bash
# 1. Загрузить файлы и перезапустить
scp bot.py imagen_api.py imagen3_custom_api.py keyboards.py root@31.44.7.144:/root/bots/usp/ && \
ssh root@31.44.7.144 'systemctl restart imagegen-bot && sleep 5 && systemctl status imagegen-bot --no-pager'
```

### Пошаговое обновление

```bash
# 1. Загрузить новые файлы
scp *.py root@31.44.7.144:/root/bots/usp/

# 2. Перезапустить бота
ssh root@31.44.7.144 'systemctl restart imagegen-bot'

# 3. Проверить статус
ssh root@31.44.7.144 'systemctl status imagegen-bot'
```

## 🔍 Проверка работы

```bash
# Проверить процесс
ssh root@31.44.7.144 'ps aux | grep "python3 bot.py" | grep usp'

# Проверить lock file
ssh root@31.44.7.144 'cat /tmp/imagegen_bot.lock'

# Проверить логи (последние 30 строк)
ssh root@31.44.7.144 'tail -30 /root/bots/usp/bot.log'

# Проверить автозапуск
ssh root@31.44.7.144 'systemctl is-enabled imagegen-bot'
```

## ⚠️ Устранение проблем

### Бот не отвечает

```bash
# 1. Проверить статус
ssh root@31.44.7.144 'systemctl status imagegen-bot'

# 2. Перезапустить
ssh root@31.44.7.144 'systemctl restart imagegen-bot'

# 3. Проверить логи
ssh root@31.44.7.144 'journalctl -u imagegen-bot -n 50'
```

### Зависшие процессы

```bash
# Полная очистка и перезапуск
ssh root@31.44.7.144 'cd /root/bots/usp && ./bot_control.sh cleanup && ./bot_control.sh start'
```

### "Bot is already running" при ручном запуске

Это нормально! Защита от дублей работает. Используйте systemctl:

```bash
ssh root@31.44.7.144 'systemctl restart imagegen-bot'
```

## 🔒 Защита от дублей

Бот защищён от запуска нескольких копий:

1. **Systemd** - не даст запустить второй service
2. **Lock file** - `/tmp/imagegen_bot.lock` блокируется через fcntl
3. **Проверка при старте** - бот сам проверяет, не запущен ли он уже

## 📊 Мониторинг

### Создать алиасы для быстрого доступа

На сервере добавить в `~/.bashrc`:

```bash
alias bot-status='systemctl status imagegen-bot --no-pager'
alias bot-restart='systemctl restart imagegen-bot'
alias bot-logs='journalctl -u imagegen-bot -f'
alias bot-file-logs='tail -f /root/bots/usp/bot.log'
```

Применить:
```bash
source ~/.bashrc
```

Использование:
```bash
bot-status
bot-restart
bot-logs
bot-file-logs
```

## 📁 Важные файлы и пути

| Файл/Путь | Описание |
|-----------|----------|
| `/root/bots/usp/bot.py` | Основной файл бота |
| `/root/bots/usp/bot.log` | Логи бота |
| `/tmp/imagegen_bot.lock` | Lock file (PID) |
| `/etc/systemd/system/imagegen-bot.service` | Systemd service |
| `/root/bots/usp/bot_control.sh` | Скрипт управления |
| `/root/bots/usp/.env` | Переменные окружения (API ключи) |

## 🆘 Экстренные команды

```bash
# Принудительная остановка всех копий
ssh root@31.44.7.144 'pkill -9 -f "python3.*bot.py"; rm -f /tmp/imagegen_bot.lock; systemctl stop imagegen-bot'

# Полная переустановка автозапуска
ssh root@31.44.7.144 'cd /root/bots/usp && ./setup_autostart.sh'

# Отключить автозапуск
ssh root@31.44.7.144 'systemctl disable imagegen-bot'

# Включить автозапуск
ssh root@31.44.7.144 'systemctl enable imagegen-bot'
```

## 📚 Полная документация

- [SYSTEMD_AUTOSTART.md](SYSTEMD_AUTOSTART.md) - Детальная документация systemd
- [CLAUDE.md](CLAUDE.md) - Инструкции для Claude AI
- [INTEGRATION_COMPLETE.md](INTEGRATION_COMPLETE.md) - История интеграций
- [README.md](README.md) - Общая документация проекта

## ✅ Чеклист после обновления

- [ ] Файлы загружены: `scp *.py root@31.44.7.144:/root/bots/usp/`
- [ ] Бот перезапущен: `systemctl restart imagegen-bot`
- [ ] Статус OK: `systemctl status imagegen-bot`
- [ ] Логи чистые: `tail -30 /root/bots/usp/bot.log`
- [ ] Бот отвечает в Telegram
- [ ] Git commit создан
- [ ] Git push выполнен (если нужно)

---

**Версия:** 2.3.1
**Последнее обновление:** 2026-02-22
**Статус:** ✅ Production Ready
