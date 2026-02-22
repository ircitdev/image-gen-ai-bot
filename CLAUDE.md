# Claude AI Instructions for UspImagegen Bot

## Project Overview
UspImagegen is a Telegram bot for AI image generation using multiple engines:
- **DALL-E 3** (OpenAI)
- **Stable Diffusion 3.5** (Stability AI)
- **Google Imagen 4** (Nano Banana 4) - Text-to-image
- **Google Imagen 3 Customization** - Image generation with reference photos (NEW!)

## Project Structure

### Core Files
- `bot.py` - Main bot application (50K+ lines, read with offset/limit)
- `settings.py` - Environment configuration
- `.env` - API keys and secrets (NEVER commit to git)

### API Integrations
- `imagen_api.py` - Google Imagen 4 API integration (text-to-image)
- `imagen_gen_helper.py` - Imagen 4 generation helper
- `imagen3_custom_api.py` - Google Imagen 3 Customization API (reference images) **NEW**
- `imagen3_custom_helper.py` - Imagen 3 Custom helper **NEW**
- `dalle_api.py` - DALL-E 3 API integration
- `dalle_gen_helper.py` - DALL-E generation helper
- `dream_api.py` - Stable Diffusion API integration

### Features
- `ai_tools.py` - Image manipulation (upscale, remove background, variations, inpaint, outpaint)
- `image_library.py` - User image history and favorites
- `presets.py` - User prompt presets
- `style_guide.py` - Style guide generation
- `style_transfer.py` - Style transfer functionality
- `sketch.py` - Sketch to image generation
- `user_limits.py` - Usage limits and referral system
- `payments.py` - CryptoBot payment integration

### Infrastructure
- `gcs_helper.py` - Google Cloud Storage for images
- `gcs_advanced.py` - Advanced GCS features
- `gsheets_logger.py` - Google Sheets logging
- `webapp_server.py` - Mini App web server for inpaint editor
- `mask_server.py` - Mask editor server

### UI Components
- `keyboards.py` - Telegram inline keyboards
- `keyboards_addon.py` - Additional keyboard layouts
- `state.py` - User state management
- `utils.py` - Utility functions

## Important Rules

### File Operations
1. **NEVER read bot.py without offset/limit** - it's 50K+ lines (182KB)
2. **Read bot.py in chunks:**
   ```python
   Read(file_path="bot.py", offset=1, limit=100)
   ```

### Git & Deployment
1. **NEVER commit `.env` file** - it's in `.gitignore`
2. **Server deployment path:** `/root/bots/usp/`
3. **Server IP:** `31.44.7.144` (root@31.44.7.144)
4. **Lock file location:** `/tmp/imagegen_bot.lock`

### Server Management
1. **Before restarting bot:**
   ```bash
   pkill -9 -f "python3.*bot.py"
   rm -f /tmp/imagegen_bot.lock
   sleep 5
   ```

2. **Start bot:**
   ```bash
   cd /root/bots/usp
   nohup python3 bot.py > bot.log 2>&1 &
   ```

3. **Check status:**
   ```bash
   ps aux | grep 'python3 bot.py' | grep '/root/bots/usp' | grep -v grep
   tail -50 /root/bots/usp/bot.log
   ```

### API Keys (in .env)
```bash
# Telegram
TELEGRAM_BOT_TOKEN=<token>

# OpenAI (DALL-E 3)
OPENAI_API_KEY=sk-proj-...

# Stability AI
STABILITY_API_KEY=sk-...

# Google AI (Imagen 3/4 - Nano Banana)
GOOGLE_AI_API_KEY=AIzaSy...

# CryptoBot
CRYPTOBOT_TOKEN=<token>
CRYPTOBOT_CURRENCY=USDT

# Google Cloud Storage
USE_GCS=true
GCS_BUCKET_NAME=tgbots-images
GCS_CREDENTIALS_PATH=tgbots-google-cloud.json

# Google Sheets Logging
GSHEETS_LOGGING=true
GSHEETS_SPREADSHEET_ID=<id>
GSHEETS_CREDENTIALS_PATH=tgbots-google-sheets.json

# Mini App
WEBAPP_URL=https://imagegen.tools.uspeshnyy.ru
```

### Updating .env on Server
1. **Update locally first** - edit `d:\DevTools\Database\UspImagegen\.env`
2. **Update on server:**
   ```bash
   ssh root@31.44.7.144 "sed -i 's/KEY_NAME=.*/KEY_NAME=new_value/' /root/bots/usp/.env"
   ```
3. **Verify:**
   ```bash
   ssh root@31.44.7.144 "grep KEY_NAME /root/bots/usp/.env"
   ```

## Common Tasks

### Adding New API Integration
1. Create `<service>_api.py` with generation function
2. Create `<service>_gen_helper.py` for bot integration
3. Import in `bot.py`
4. Add keyboard option in `keyboards.py`
5. Add handler in `bot.py`
6. Update `.env` with API key
7. Test locally, then deploy to server

### Testing API Integration
```bash
cd /root/bots/usp
python3 -c "from imagen_api import generate_with_imagen; imgs = generate_with_imagen('test prompt', '1:1', 1); print(f'Success! {len(imgs)} images')"
```

### Debugging
1. **Check bot logs:**
   ```bash
   ssh root@31.44.7.144 "tail -100 /root/bots/usp/bot.log"
   ```

2. **Check running processes:**
   ```bash
   ssh root@31.44.7.144 "ps aux | grep bot.py"
   ```

3. **Common issues:**
   - Multiple instances: Kill all and restart
   - Lock file stuck: `rm -f /tmp/imagegen_bot.lock`
   - API errors: Check `.env` keys

## Architecture Notes

### Bot Flow
1. User sends command/message
2. State management (`state.py`) tracks user context
3. Handler processes request
4. API call to generation engine
5. Image processing (watermark, GCS upload)
6. Response to user
7. Log to Google Sheets (if enabled)

### Image Storage
- **Local:** Temporary files during generation
- **GCS:** Permanent storage (if `USE_GCS=true`)
- **Library:** User history in `image_library.py`

### Payment Flow
1. User selects package (`packages_kb`)
2. CryptoBot invoice created
3. User pays
4. Webhook confirms payment
5. Generations added to user account

## Security Notes
- **NEVER expose API keys** in commits or logs
- **Sanitize user input** before API calls
- **Validate file uploads** for Mini App
- **Rate limiting** via `user_limits.py`
- **Admin-only commands** check `ADMIN_ID = 65876198`

## Performance Optimization
1. **Use GCS** for image hosting (reduces server storage)
2. **Enable caching** where possible
3. **Async operations** for long-running tasks
4. **Connection pooling** for API calls

## Monitoring
- **Google Sheets:** Logs all generations (if `GSHEETS_LOGGING=true`)
- **Bot logs:** `/root/bots/usp/bot.log`
- **Process monitoring:** Check PID regularly

## Version History
- v2.2.0 - Added Google Imagen 3 (Nano Banana) integration
- v2.1.1 - Fixed Inpaint mask editor WebApp URL
- v2.1.0 - Added Advanced Image Library System
- Earlier versions - DALL-E, Stability AI, basic features

## Contact
- Admin Telegram ID: `65876198`
- Server: `uspeshnyy.ru` (31.44.7.144)
