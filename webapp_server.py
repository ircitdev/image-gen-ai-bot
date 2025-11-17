"""
Веб-сервер для Telegram Mini App - Inpaint Editor
Обслуживает HTML редактор маски и изображения для редактирования
"""

from flask import Flask, send_from_directory, request, jsonify
from flask_cors import CORS
import os
import base64
from io import BytesIO
from PIL import Image
import secrets

app = Flask(__name__)
CORS(app)

# Директории для статических файлов и изображений
STATIC_DIR = os.path.join(os.path.dirname(__file__), 'static')
IMAGES_DIR = os.path.join(STATIC_DIR, 'images')

# Создаем директории если их нет
os.makedirs(STATIC_DIR, exist_ok=True)
os.makedirs(IMAGES_DIR, exist_ok=True)

# Хранилище изображений (в production использовать Redis/DB)
uploaded_images = {}


@app.route('/')
def index():
    """Главная страница Mini App"""
    return send_from_directory(STATIC_DIR, 'inpaint_editor.html')


@app.route('/images/<filename>')
def serve_image(filename):
    """Отдача изображений"""
    return send_from_directory(IMAGES_DIR, filename)


@app.route('/upload_image', methods=['POST'])
def upload_image():
    """
    Загрузка изображения для редактирования
    Возвращает token для доступа к изображению
    """
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        image_data = data.get('image')  # base64 или URL

        if not user_id or not image_data:
            return jsonify({'error': 'Missing parameters'}), 400

        # Генерируем уникальный токен
        token = secrets.token_urlsafe(16)

        # Сохраняем изображение
        if image_data.startswith('data:image'):
            # Base64 изображение
            image_b64 = image_data.split(',')[1]
            image_bytes = base64.b64decode(image_b64)

            # Сохраняем в файл
            filename = f"{token}.png"
            filepath = os.path.join(IMAGES_DIR, filename)

            with open(filepath, 'wb') as f:
                f.write(image_bytes)
        else:
            # URL изображения - просто сохраняем токен
            filename = f"{token}.png"
            filepath = os.path.join(IMAGES_DIR, filename)

            # Скачиваем изображение из URL
            import requests
            response = requests.get(image_data)
            if response.status_code == 200:
                with open(filepath, 'wb') as f:
                    f.write(response.content)
            else:
                return jsonify({'error': 'Failed to download image'}), 400

        # Сохраняем информацию
        uploaded_images[token] = {
            'user_id': user_id,
            'filename': filename
        }

        return jsonify({
            'token': token,
            'url': f'/images/{filename}'
        })

    except Exception as e:
        print(f"Error uploading image: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({'status': 'ok'})


if __name__ == '__main__':
    print("Starting Mini App server on http://0.0.0.0:5000")
    app.run(host='0.0.0.0', port=5000, debug=False)
