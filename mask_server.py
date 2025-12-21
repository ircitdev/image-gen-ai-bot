from flask import Flask, request, jsonify
from flask_cors import CORS
import base64
import uuid
import os
from datetime import datetime, timedelta

app = Flask(__name__)
CORS(app)

# Временное хранилище масок (в памяти)
masks_storage = {}

# Очистка старых масок (старше 1 часа)
def cleanup_old_masks():
    now = datetime.now()
    to_delete = []
    for mask_id, data in masks_storage.items():
        if now - data['timestamp'] > timedelta(hours=1):
            to_delete.append(mask_id)
    for mask_id in to_delete:
        del masks_storage[mask_id]

@app.route('/upload_mask', methods=['POST'])
def upload_mask():
    try:
        cleanup_old_masks()
        
        # Получаем данные
        data = request.get_json()
        user_id = data.get('user_id')
        mask_base64 = data.get('mask')
        original_width = data.get('original_width')
        original_height = data.get('original_height')
        
        if not mask_base64:
            return jsonify({'error': 'No mask data'}), 400
        
        # Генерируем уникальный ID
        mask_id = str(uuid.uuid4())
        
        # Сохраняем в памяти
        masks_storage[mask_id] = {
            'user_id': user_id,
            'mask': mask_base64,
            'original_width': original_width,
            'original_height': original_height,
            'timestamp': datetime.now()
        }
        
        print(f'[MASK] Uploaded mask_id={mask_id} for user_id={user_id}')
        
        return jsonify({'mask_id': mask_id, 'status': 'ok'})
        
    except Exception as e:
        print(f'[ERROR] Upload failed: {e}')
        return jsonify({'error': str(e)}), 500

@app.route('/get_mask/<mask_id>', methods=['GET'])
def get_mask(mask_id):
    try:
        cleanup_old_masks()
        
        if mask_id not in masks_storage:
            return jsonify({'error': 'Mask not found'}), 404
        
        data = masks_storage[mask_id]
        
        # Удаляем после получения (одноразовое использование)
        del masks_storage[mask_id]
        
        return jsonify(data)
        
    except Exception as e:
        print(f'[ERROR] Get mask failed: {e}')
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'masks_count': len(masks_storage)})


@app.route('/send_mask_id', methods=['POST'])
def send_mask_id():
    try:
        data = request.get_json()
        user_id = str(data.get('user_id'))
        mask_id = data.get('mask_id')
        
        if not user_id or not mask_id:
            return jsonify({'error': 'Missing parameters'}), 400
        
        # Сохраняем связку user_id -> mask_id в памяти mask_server
        if not hasattr(app, 'pending_masks'):
            app.pending_masks = {}
        app.pending_masks[user_id] = mask_id
        
        print(f'[PENDING] Saved mask_id={mask_id} for user_id={user_id}')
        return jsonify({'status': 'ok'})
        
    except Exception as e:
        print(f'[ERROR] Send failed: {e}')
        return jsonify({'error': str(e)}), 500


@app.route('/get_pending_mask/<user_id>', methods=['GET'])
def get_pending_mask(user_id):
    try:
        if not hasattr(app, 'pending_masks'):
            return jsonify({'error': 'No pending masks'}), 404
        
        mask_id = app.pending_masks.get(user_id)
        if not mask_id:
            return jsonify({'error': 'No mask for this user'}), 404
        
        # Удаляем после получения
        del app.pending_masks[user_id]
        
        return jsonify({'mask_id': mask_id})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500



if __name__ == '__main__':
    print('[MASK SERVER] Starting on port 5555...')
    app.run(host='0.0.0.0', port=5555, debug=False)
