# Changelog

All notable changes to the Image Gen AI Bot will be documented in this file.

## [2.1.1] - 2025-12-03

### Fixed
- **Inpaint Mask Editor URL Fix**: Corrected WebApp URL generation in `upload_image_to_webapp()` function
  - Changed from root path `/` to proper static file path `/static/inpaint_editor.html`
  - This fixes the issue where clicking "Готово" button in the mask editor didn't trigger mask upload
  - Affected files: `bot.py` (lines 67, 101)
  - Root cause: Mini App was loading wrong/empty page instead of inpaint_editor.html
  - Impact: Inpaint mask editor now fully functional with proper mask upload workflow

### Technical Details
- **Before**: `https://imagegen.tools.uspeshnyy.ru/?v=20251203094000&image=...&user_id=...`
- **After**: `https://imagegen.tools.uspeshnyy.ru/static/inpaint_editor.html?v=20251203094000&image=...&user_id=...`

The fix ensures that:
1. Telegram Mini App loads the correct HTML file with mask editor interface
2. JavaScript code properly executes mask upload via `/upload_mask` endpoint
3. Mask ID is sent to bot via `/send_mask_id` endpoint
4. User can complete inpaint workflow by clicking "✅ Завершить" callback button

## [2.1.0] - 2025-11-22

### Added
- **Advanced Image Library System**
  - Google Cloud Storage integration for image management
  - 4 categories: generated, uploaded, edited, favorites
  - Image filtering by tags, date, generator
  - Export to PDF and ZIP
  - 18 auto-save points throughout the bot

- **Google Sheets Logging**
  - Automatic logging of all generations
  - User statistics tracking
  - Error logging

- **Telegram Mini App**
  - Interactive inpaint mask editor
  - Touch-enabled drawing interface
  - Brush size control
  - Undo/clear functionality

- **Prompts Management**
  - Save and reuse custom prompts
  - Quick access to favorite prompts
  - Prompt history

### Enhanced
- **Payment System**: Added Telegram Stars support alongside CryptoBot
- **AI Models**: Expanded to include SD 3.5 Large, Turbo, Medium, Flash
- **Documentation**: Comprehensive README and Quick Start guides

## [2.0.0] - 2025-10-15

### Added
- **Multi-Model Support**
  - Stable Diffusion 3.5 (4 variants)
  - DALL-E 2 and 3
  - OpenAI GPT-4o and GPT-5

- **AI Tools**
  - Upscale, Remove Background, Face Restore
  - Inpaint, Outpaint, Variations
  - Search & Recolor, Search & Replace, Erase

- **Parameter System**
  - 18 styles, 10 formats
  - 8 shot types, 9 camera angles
  - 8 lighting types

- **Preset System**
  - Save/load generation settings
  - Quick preset application

- **Payment Integration**
  - 4 pricing tiers
  - CryptoBot USDT payments
  - Referral program (+5 generations per referral)

## [1.0.0] - 2025-09-01

### Initial Release
- Basic Stable Diffusion image generation
- Simple text-to-image workflow
- Basic bot commands (/start, /new, /help)
- File-based image storage
