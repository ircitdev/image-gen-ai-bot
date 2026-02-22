#!/bin/bash
# Скрипт управления USP ImageGen Bot с защитой от дублей

LOCK_FILE="/tmp/imagegen_bot.lock"
BOT_DIR="/root/bots/usp"
LOG_FILE="$BOT_DIR/bot.log"
SERVICE_NAME="imagegen-bot"

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

function check_running() {
    # Проверяем, запущен ли бот
    if systemctl is-active --quiet $SERVICE_NAME; then
        return 0
    else
        return 1
    fi
}

function get_pid() {
    # Получаем PID из lock файла или из процесса
    if [ -f "$LOCK_FILE" ]; then
        cat "$LOCK_FILE"
    else
        pgrep -f "python3.*$BOT_DIR/bot.py" | head -1
    fi
}

function status() {
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "📊 Статус USP ImageGen Bot"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    if check_running; then
        PID=$(get_pid)
        echo -e "${GREEN}✅ Бот работает${NC}"
        echo "   PID: $PID"
        echo "   Lock file: $LOCK_FILE"

        # Показываем использование ресурсов
        if [ -n "$PID" ] && ps -p "$PID" > /dev/null 2>&1; then
            echo ""
            ps -p "$PID" -o pid,ppid,%cpu,%mem,etime,cmd --no-headers
        fi
    else
        echo -e "${RED}❌ Бот не запущен${NC}"

        # Проверяем зависшие процессы
        ZOMBIE_PIDS=$(pgrep -f "python3.*$BOT_DIR/bot.py")
        if [ -n "$ZOMBIE_PIDS" ]; then
            echo -e "${YELLOW}⚠️  Обнаружены зависшие процессы: $ZOMBIE_PIDS${NC}"
        fi

        # Проверяем lock file
        if [ -f "$LOCK_FILE" ]; then
            echo -e "${YELLOW}⚠️  Lock file существует (возможно, бот упал)${NC}"
        fi
    fi

    echo ""
    echo "Systemd service:"
    systemctl status $SERVICE_NAME --no-pager -l | head -15
}

function start_bot() {
    echo "🚀 Запуск бота..."

    if check_running; then
        echo -e "${YELLOW}⚠️  Бот уже запущен!${NC}"
        status
        return 1
    fi

    # Убиваем зависшие процессы
    ZOMBIE_PIDS=$(pgrep -f "python3.*$BOT_DIR/bot.py")
    if [ -n "$ZOMBIE_PIDS" ]; then
        echo "🔪 Убиваем зависшие процессы: $ZOMBIE_PIDS"
        pkill -9 -f "python3.*$BOT_DIR/bot.py"
        sleep 2
    fi

    # Удаляем lock file
    rm -f "$LOCK_FILE"

    # Запускаем через systemd
    systemctl start $SERVICE_NAME

    echo "⏳ Ждём запуска..."
    sleep 5

    if check_running; then
        echo -e "${GREEN}✅ Бот успешно запущен!${NC}"
        status
    else
        echo -e "${RED}❌ Ошибка запуска!${NC}"
        echo "Последние 30 строк лога:"
        tail -30 "$LOG_FILE"
        return 1
    fi
}

function stop_bot() {
    echo "🛑 Остановка бота..."

    if ! check_running; then
        echo -e "${YELLOW}⚠️  Бот не запущен${NC}"

        # Проверяем зависшие процессы
        ZOMBIE_PIDS=$(pgrep -f "python3.*$BOT_DIR/bot.py")
        if [ -n "$ZOMBIE_PIDS" ]; then
            echo "🔪 Убиваем зависшие процессы: $ZOMBIE_PIDS"
            pkill -9 -f "python3.*$BOT_DIR/bot.py"
            rm -f "$LOCK_FILE"
        fi
        return 0
    fi

    # Останавливаем через systemd
    systemctl stop $SERVICE_NAME

    echo "⏳ Ждём остановки..."
    sleep 3

    # Проверяем, что процесс завершён
    if check_running; then
        echo -e "${YELLOW}⚠️  Бот не остановился, принудительное завершение...${NC}"
        pkill -9 -f "python3.*$BOT_DIR/bot.py"
        sleep 2
    fi

    # Удаляем lock file
    rm -f "$LOCK_FILE"

    if ! check_running; then
        echo -e "${GREEN}✅ Бот остановлен${NC}"
    else
        echo -e "${RED}❌ Не удалось остановить бота!${NC}"
        return 1
    fi
}

function restart_bot() {
    echo "🔄 Перезапуск бота..."
    stop_bot
    sleep 2
    start_bot
}

function logs() {
    echo "📋 Логи бота (последние 50 строк):"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    tail -50 "$LOG_FILE"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "Для просмотра в реальном времени: tail -f $LOG_FILE"
}

function cleanup() {
    echo "🧹 Очистка зависших процессов и lock файлов..."

    # Убиваем все процессы
    pkill -9 -f "python3.*$BOT_DIR/bot.py" 2>/dev/null || echo "Нет процессов для остановки"

    # Удаляем lock file
    rm -f "$LOCK_FILE"

    # Останавливаем сервис
    systemctl stop $SERVICE_NAME 2>/dev/null || true

    echo -e "${GREEN}✅ Очистка завершена${NC}"
}

# Главное меню
case "$1" in
    status)
        status
        ;;
    start)
        start_bot
        ;;
    stop)
        stop_bot
        ;;
    restart)
        restart_bot
        ;;
    logs)
        logs
        ;;
    cleanup)
        cleanup
        ;;
    *)
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "🤖 USP ImageGen Bot - Управление"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo ""
        echo "Использование: $0 {status|start|stop|restart|logs|cleanup}"
        echo ""
        echo "Команды:"
        echo "  status   - показать статус бота"
        echo "  start    - запустить бота"
        echo "  stop     - остановить бота"
        echo "  restart  - перезапустить бота"
        echo "  logs     - показать последние логи"
        echo "  cleanup  - очистить зависшие процессы"
        echo ""
        exit 1
        ;;
esac

exit 0
