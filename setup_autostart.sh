#!/bin/bash
# Скрипт установки автозапуска для USP ImageGen Bot

set -e

echo "🔧 Настройка автозапуска USP ImageGen Bot..."

# 1. Останавливаем все запущенные копии бота
echo "📛 Останавливаем все копии бота..."
pkill -9 -f "python3.*bot.py" 2>/dev/null || echo "Нет запущенных процессов"
rm -f /tmp/imagegen_bot.lock

# 2. Копируем service файл в systemd
echo "📝 Копируем service файл..."
cp imagegen-bot.service /etc/systemd/system/

# 3. Перезагружаем systemd
echo "🔄 Перезагружаем systemd..."
systemctl daemon-reload

# 4. Включаем автозапуск
echo "✅ Включаем автозапуск..."
systemctl enable imagegen-bot.service

# 5. Запускаем сервис
echo "🚀 Запускаем бота..."
systemctl start imagegen-bot.service

# 6. Ждём 5 секунд и проверяем статус
echo "⏳ Ждём запуска..."
sleep 5

# 7. Показываем статус
echo ""
echo "📊 Статус сервиса:"
systemctl status imagegen-bot.service --no-pager

echo ""
echo "✅ Готово! Бот запущен и добавлен в автозагрузку."
echo ""
echo "Полезные команды:"
echo "  systemctl status imagegen-bot   - статус бота"
echo "  systemctl start imagegen-bot    - запустить бота"
echo "  systemctl stop imagegen-bot     - остановить бота"
echo "  systemctl restart imagegen-bot  - перезапустить бота"
echo "  journalctl -u imagegen-bot -f   - смотреть логи в реальном времени"
echo "  tail -f /root/bots/usp/bot.log  - смотреть логи файла"
