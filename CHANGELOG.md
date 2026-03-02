# Changelog

All notable changes to the Image Gen AI Bot will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.3.0] - 2026-02-22

### Added

#### New Features
- **GPT Image Models Integration**
  - GPT Image 1.5 (4x faster, 20% cheaper than DALL-E 3) - now default
  - GPT Image 1 (advanced quality model)
  - GPT Image Mini (fast and lightweight)
  - Model selection in keyboards.py with descriptions

- **/getprompt Command**
  - Analyze images with Gemini 2.5 Flash Vision AI
  - Extract detailed prompts from any image
  - Automatic +30% prompt enhancement with professional terminology
  - Analyzes: style, composition, lighting, colors, atmosphere, technical details
  - Use cases: reverse engineering, learning, variations, style documentation

- **Premium User System**
  - Unlimited generations for premium users
  - `set_premium(user_id, is_premium=True)` function for admins
  - Premium status tracking with `premium_since` timestamps
  - Automatic status checking in `can_generate()` and `get_user_stats()`
  - Returns 999999 remaining for premium users

#### Documentation
- help.html updated with all February 2026 features
- MIGRATION_COMPLETE_STYLETRANSFER.md - Style Transfer migration guide
- PREMIUM_USER_813910081.md - Premium system documentation
- HELP_HTML_UPDATE_FEB2026.md - help.html update notes
- GPT_IMAGE_INTEGRATION.md - GPT Image models guide
- GETPROMPT_FEATURE.md - /getprompt feature documentation

### Changed

#### Major Migrations
- **Style Transfer → Google Imagen (Nano Banana Pro)**
  - Simplified workflow: **7 steps → 3 steps** (57% reduction)
  - Removed SD parameters: negative_prompt, style_strength, composition_fidelity, change_strength
  - Now only requires: init_image, style_image, prompt
  - Significantly better quality vs Stable Diffusion
  - Uses BytesIO for better memory management
  - Faster generation: 60-90 seconds

- **Style Guide → Google Imagen (Nano Banana Pro)**
  - Simplified workflow: **5 steps → 2 steps** (60% reduction)
  - Removed parameters: negative_prompt, aspect_ratio, fidelity
  - Now only requires: style_image, prompt
  - Improved style following and consistency
  - Fixed aspect ratio at 1:1

#### Code Improvements
- Reduced Style Transfer/Style Guide handlers by **115 lines** (39% code reduction)
- Changed from file-based (`download_to_drive()`) to BytesIO-based (`download_as_bytearray()`) image handling
- Better error handling with proper Exception catching
- Consistent image processing across all style commands

#### API Updates
- DALL-E 2/3 marked as deprecated in keyboards (kept for backward compatibility)
- Default DALL-E model changed from `dall-e-3` to `gpt-image-1.5`
- Added Gemini 2.5 Flash Vision API for image analysis
- Integrated Google Imagen 3 Custom (Nano Banana Pro) for style operations

### Fixed

- **Critical Bug:** /styleguide BytesIO error
  - **Error:** `'PosixPath' object has no attribute 'seek'`
  - **Cause:** Still using `download_to_drive()` instead of `download_as_bytearray()`
  - **Fix:** Changed to BytesIO implementation consistent with Style Transfer
  - **Commit:** 3c85f17
  - **Impact:** /styleguide now works correctly with Google Imagen

- /getprompt message formatting
  - Removed double-escaped `\\n` characters
  - Fixed HTML formatting in output messages
  - Added to bot command menu

- Emoji encoding errors in automation scripts
  - Replaced emoji characters with ASCII equivalents
  - Fixed UnicodeEncodeError in add_getprompt.py

### Deprecated

- **DALL-E 2 and DALL-E 3 models** (still functional, marked as "Устарела" in UI)
- **Stable Diffusion for Style Transfer/Style Guide** (replaced by Google Imagen)
- Old multi-parameter workflows (replaced by simplified versions)

### Removed

- negative_prompt parameter from Style Transfer and Style Guide
- style_strength, composition_fidelity, change_strength from Style Transfer
- fidelity parameter from Style Guide
- aspect_ratio selection from Style Guide (now fixed at 1:1)

### Breaking Changes

⚠️ **Style Transfer & Style Guide Parameters Removed:**

Users who relied on fine-tuning with Stable Diffusion parameters must adapt to the new simplified workflow:

**Style Transfer:**
- ❌ Removed: negative_prompt, style_strength, composition_fidelity, change_strength
- ✅ Kept: prompt, aspect_ratio (fixed 1:1)

**Style Guide:**
- ❌ Removed: negative_prompt, aspect_ratio selection, fidelity
- ✅ Kept: prompt

**Migration Guide:** The new Google Imagen implementation is easier to use and produces superior results. No manual parameter tuning needed.

### Security

- All API keys properly handled in .env
- User input sanitization maintained
- Premium status verification on every generation
- No security vulnerabilities introduced

### Performance

- **GPT Image 1.5:** 4x faster generation than DALL-E 3
- **BytesIO usage:** Reduced disk I/O operations
- **Simplified workflows:** Faster processing, fewer user inputs
- **Code reduction:** 39% less code = fewer potential bugs
- **Google Imagen:** 60-90 second generation time

### Infrastructure

- Google Cloud Storage integration maintained
- Google Sheets logging operational
- Telegram Mini App for inpaint editor working
- All services running on 31.44.7.144
- Bot deployed at /root/bots/usp/
- Webhook-free polling mode

### Developer Notes

**Commits in this release:**
- 3c85f17 - Fix /styleguide BytesIO issue
- fc5727f - Add help.html update documentation
- 53e08ae - Update help.html with February 2026 features
- a71fb9e - Add documentation for premium user 813910081
- 36375d1 - Add Premium user support to user_limits system
- 9bc98d5 - Add Style Transfer migration documentation
- 44d236c - Migrate /styletransfer and /styleguide to Google Imagen
- fd957c9 - Add Imagen-based style transfer
- c53f0f6 - Add /getprompt to menu and fix formatting
- 90e868c - Fix syntax errors in /getprompt command

**Statistics:**
- 9 commits
- 6 new documentation files
- 3 major features added
- 2 commands migrated
- 1 critical bug fixed

---

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
