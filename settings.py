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

# Mini App Web Server URL для Inpaint Editor
WEBAPP_URL = os.getenv("WEBAPP_URL", "http://localhost:5000")

# Google Cloud Storage для хранения изображений
USE_GCS = os.getenv("USE_GCS", "true").lower() == "true"  # Использовать GCS для хранения изображений
GCS_BUCKET_NAME = os.getenv("GCS_BUCKET_NAME", "tgbots-images")
GCS_CREDENTIALS_PATH = os.getenv("GCS_CREDENTIALS_PATH", "tgbots-google-cloud.json")

# Google Sheets для логирования активности
GSHEETS_LOGGING = os.getenv("GSHEETS_LOGGING", "true").lower() == "true"
GSHEETS_SPREADSHEET_ID = os.getenv("GSHEETS_SPREADSHEET_ID", "1TsPo12VGW8u9YmcEhWHcIL-6yWCZ0_svBgku9fTaE0s")
GSHEETS_CREDENTIALS_PATH = os.getenv("GSHEETS_CREDENTIALS_PATH", "tgbots-google-sheets.json")
