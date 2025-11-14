import os
from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла
load_dotenv()

# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")

# Replicate API (deprecated, not used in current version)
REPLICATE_API_TOKEN = os.getenv("REPLICATE_API_TOKEN", "")

# Cloudflare Worker URL для генерации изображений (deprecated)
CLOUDFLARE_WORKER_URL = os.getenv("CLOUDFLARE_WORKER_URL", "https://imagegenbot.ircitru.workers.dev")

# OpenAI API токен для ChatGPT-4o
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# Stability.ai API токен для генерации изображений
STABILITY_API_KEY = os.getenv("STABILITY_API_KEY", "")

# CryptoBot API для криптовалютных платежей
CRYPTOBOT_TOKEN = os.getenv("CRYPTOBOT_TOKEN", "")
CRYPTOBOT_CURRENCY = os.getenv("CRYPTOBOT_CURRENCY", "USDT")
