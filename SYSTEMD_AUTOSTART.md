# Автозапуск USP ImageGen Bot через systemd

## Преимущества systemd

1. **Автозапуск при старте сервера** - бот запустится автоматически после перезагрузки
2. **Автоматический перезапуск при падении** - если бот упадёт, systemd перезапустит его
3. **Защита от дублей** - systemd гарантирует, что запущена только одна копия
4. **Централизованное управление** - стандартные команды `systemctl`
5. **Логирование** - интеграция с journald

## Установка

### 1. Загрузить файлы на сервер

```bash
# С локальной машины
scp imagegen-bot.service setup_autostart.sh bot_control.sh root@31.44.7.144:/root/bots/usp/
```

### 2. Запустить установку

```bash
ssh root@31.44.7.144
cd /root/bots/usp
chmod +x setup_autostart.sh bot_control.sh
./setup_autostart.sh
```

Скрипт автоматически:
- Остановит все старые копии бота
- Установит systemd service
- Включит автозапуск
- Запустит бота
- Покажет статус

## Управление ботом

### Стандартные команды systemd

```bash
# Статус бота
systemctl status imagegen-bot

# Запустить бота
systemctl start imagegen-bot

# Остановить бота
systemctl stop imagegen-bot

# Перезапустить бота
systemctl restart imagegen-bot

# Включить автозапуск
systemctl enable imagegen-bot

# Отключить автозапуск
systemctl disable imagegen-bot

# Логи в реальном времени
journalctl -u imagegen-bot -f

# Последние 100 строк логов
journalctl -u imagegen-bot -n 100
```

### Удобный скрипт управления

```bash
# Статус (детальный)
./bot_control.sh status

# Запустить
./bot_control.sh start

# Остановить
./bot_control.sh stop

# Перезапустить
./bot_control.sh restart

# Показать логи
./bot_control.sh logs

# Очистить зависшие процессы
./bot_control.sh cleanup
```

## Защита от дублей

### 1. Уровень systemd

`Type=simple` в service файле гарантирует, что systemd не запустит второй экземпляр.

```ini
[Service]
Type=simple
```

### 2. Уровень приложения (в bot.py)

Lock file механизм с fcntl:

```python
LOCK_FILE = "/tmp/imagegen_bot.lock"

def acquire_lock():
    global lock_file_handle
    try:
        lock_file_handle = open(LOCK_FILE, 'w')
        fcntl.flock(lock_file_handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        lock_file_handle.write(str(os.getpid()))
        lock_file_handle.flush()
        return True
    except IOError:
        return False
```

### 3. Очистка при перезапуске

```ini
ExecStartPre=/bin/rm -f /tmp/imagegen_bot.lock
```

## Логирование

### Два источника логов

1. **Файл бота** - `/root/bots/usp/bot.log`
   ```bash
   tail -f /root/bots/usp/bot.log
   ```

2. **Systemd журнал** - journalctl
   ```bash
   journalctl -u imagegen-bot -f
   ```

## Обновление бота

### Способ 1: Через systemd (рекомендуется)

```bash
# 1. Остановить бота
systemctl stop imagegen-bot

# 2. Загрузить новые файлы
scp bot.py imagen_api.py keyboards.py root@31.44.7.144:/root/bots/usp/

# 3. Запустить бота
systemctl start imagegen-bot

# 4. Проверить статус
systemctl status imagegen-bot
```

### Способ 2: Через bot_control.sh

```bash
# 1. Загрузить файлы
scp *.py root@31.44.7.144:/root/bots/usp/

# 2. Перезапустить
ssh root@31.44.7.144 'cd /root/bots/usp && ./bot_control.sh restart'
```

### Способ 3: Автоматический (одна команда)

```bash
scp bot.py imagen_api.py keyboards.py root@31.44.7.144:/root/bots/usp/ && \
ssh root@31.44.7.144 'systemctl restart imagegen-bot && sleep 3 && systemctl status imagegen-bot'
```

## Проверка работы

### После установки

```bash
# 1. Проверить статус
systemctl status imagegen-bot

# Вывод должен быть:
# ● imagegen-bot.service - USP ImageGen Telegram Bot
#    Loaded: loaded (/etc/systemd/system/imagegen-bot.service; enabled)
#    Active: active (running) since ...
#    ...

# 2. Проверить PID
ps aux | grep 'python3 bot.py' | grep '/root/bots/usp'

# 3. Проверить lock file
cat /tmp/imagegen_bot.lock

# 4. Проверить логи
tail -20 /root/bots/usp/bot.log
```

### После перезагрузки сервера

```bash
# Перезагрузить сервер
reboot

# Через 2-3 минуты проверить
ssh root@31.44.7.144 'systemctl status imagegen-bot'

# Бот должен быть запущен автоматически!
```

## Устранение проблем

### Бот не запускается

```bash
# 1. Проверить логи systemd
journalctl -u imagegen-bot -n 50

# 2. Проверить файловый лог
tail -50 /root/bots/usp/bot.log

# 3. Проверить права
ls -la /root/bots/usp/bot.py
# Должно быть: -rw-r--r-- 1 root root

# 4. Попробовать запустить вручную
cd /root/bots/usp
python3 bot.py
```

### Зависшие процессы

```bash
# 1. Проверить все процессы
ps aux | grep python3 | grep bot.py

# 2. Убить зависшие процессы
./bot_control.sh cleanup

# 3. Перезапустить
systemctl start imagegen-bot
```

### Множественные копии

```bash
# 1. Остановить сервис
systemctl stop imagegen-bot

# 2. Убить все процессы
pkill -9 -f "python3.*bot.py"

# 3. Удалить lock file
rm -f /tmp/imagegen_bot.lock

# 4. Запустить заново
systemctl start imagegen-bot
```

## Удаление автозапуска

Если нужно вернуться к ручному запуску:

```bash
# 1. Остановить и отключить сервис
systemctl stop imagegen-bot
systemctl disable imagegen-bot

# 2. Удалить service файл
rm /etc/systemd/system/imagegen-bot.service

# 3. Перезагрузить systemd
systemctl daemon-reload
```

## Мониторинг

### Создать алиас для быстрой проверки

Добавить в `~/.bashrc`:

```bash
alias bot-status='systemctl status imagegen-bot --no-pager'
alias bot-logs='journalctl -u imagegen-bot -f'
alias bot-restart='systemctl restart imagegen-bot'
```

Применить:
```bash
source ~/.bashrc
```

Теперь можно использовать:
```bash
bot-status
bot-logs
bot-restart
```

## Заключение

После установки systemd service:

✅ Бот запускается автоматически при старте сервера
✅ Автоматический перезапуск при падении (через 10 секунд)
✅ Защита от запуска двух копий одновременно
✅ Централизованное управление через `systemctl`
✅ Интеграция с системным логированием

**Рекомендация:** Использовать `systemctl` для управления в продакшене.
