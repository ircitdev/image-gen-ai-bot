# Развертывание Mini App на imagegen.tools.uspeshnyy.ru

## Что нужно сделать

Развернуть Flask веб-сервер на вашем сервере и настроить nginx.

## Шаг 1: Загрузка файлов на сервер

```bash
# На вашем локальном компьютере
scp -r static/ root@31.44.7.144:/root/bots/usp/
scp webapp_server.py root@31.44.7.144:/root/bots/usp/
```

## Шаг 2: Подключение к серверу и установка зависимостей

```bash
ssh root@31.44.7.144
cd /root/bots/usp/
pip install flask flask-cors pillow requests
```

## Шаг 3: Настройка systemd сервиса

Создайте файл `/etc/systemd/system/webapp-inpaint.service`:

```bash
cat > /etc/systemd/system/webapp-inpaint.service << 'EOF'
[Unit]
Description=Telegram Bot Mini App Web Server
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/bots/usp
Environment="PATH=/usr/local/bin:/usr/bin:/bin"
ExecStart=/usr/bin/python3 /root/bots/usp/webapp_server.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
```

## Шаг 4: Запуск сервиса

```bash
systemctl daemon-reload
systemctl enable webapp-inpaint
systemctl start webapp-inpaint
systemctl status webapp-inpaint
```

## Шаг 5: Настройка nginx

Создайте конфиг `/etc/nginx/sites-available/imagegen-tools`:

```bash
cat > /etc/nginx/sites-available/imagegen-tools << 'EOF'
server {
    listen 80;
    server_name imagegen.tools.uspeshnyy.ru;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
EOF
```

Активируйте конфиг:

```bash
ln -s /etc/nginx/sites-available/imagegen-tools /etc/nginx/sites-enabled/
nginx -t
systemctl reload nginx
```

## Шаг 6: Настройка HTTPS с Let's Encrypt

```bash
apt-get update
apt-get install -y certbot python3-certbot-nginx
certbot --nginx -d imagegen.tools.uspeshnyy.ru
```

При запросе email введите ваш email.
Выберите "Redirect" для автоматического перенаправления HTTP на HTTPS.

## Шаг 7: Проверка

```bash
# Проверить статус сервиса
systemctl status webapp-inpaint

# Проверить логи
journalctl -u webapp-inpaint -f

# Проверить доступность
curl http://127.0.0.1:5000/health
# Должен вернуть: {"status":"ok"}

# Проверить через домен
curl https://imagegen.tools.uspeshnyy.ru/health
```

## Шаг 8: Готово!

Теперь перезапустите бота и проверьте:

1. `/editmy` → загрузите фото
2. Нажмите "🎨 Дорисовать"
3. Должен открыться Mini App редактор!

## Troubleshooting

### Сервис не запускается
```bash
journalctl -u webapp-inpaint -n 50
```

### 502 Bad Gateway
→ Проверьте, запущен ли сервис:
```bash
systemctl status webapp-inpaint
```

### Nginx ошибка
```bash
nginx -t
tail -f /var/log/nginx/error.log
```

### Порт 5000 занят
Измените порт в `webapp_server.py`:
```python
app.run(host='0.0.0.0', port=5001)
```

И в nginx конфиге:
```nginx
proxy_pass http://127.0.0.1:5001;
```

## Обновление веб-сервера

Когда нужно обновить код:

```bash
ssh root@31.44.7.144
cd /root/bots/usp/
# Обновите файлы
systemctl restart webapp-inpaint
```
