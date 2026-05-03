# ⚙️ Configuration Reference

Complete reference for all environment variables and settings.

---

## Table of Contents

1. [Video Settings](#video-settings)
2. [LLM Configuration](#llm-configuration)
3. [API Keys](#api-keys)
4. [Media Generation](#media-generation)
5. [Output & Logging](#output--logging)
6. [Remotion Settings](#remotion-settings)
7. [Advanced Options](#advanced-options)

---

## Video Settings

Control video dimensions and aspect ratios.

### `VIDEO_WIDTH`

**Type:** Integer (pixels)  
**Default:** `1080`  
**Range:** 100-7680  
**Description:** Width of generated video

**Examples:**

```env
VIDEO_WIDTH=1080          # Standard vertical (TikTok, Reels)
VIDEO_WIDTH=1920          # Horizontal (YouTube)
VIDEO_WIDTH=720           # Smaller vertical (mobile)
```

### `VIDEO_HEIGHT`

**Type:** Integer (pixels)  
**Default:** `1920`  
**Range:** 100-4320  
**Description:** Height of generated video

**Examples:**

```env
VIDEO_HEIGHT=1920         # Vertical (9:16)
VIDEO_HEIGHT=1080         # Horizontal (16:9)
VIDEO_HEIGHT=1440         # Square (1:1)
```

### `VIDEO_ASPECT_RATIO`

**Type:** String (format: `W:H`)  
**Default:** `9:16`  
**Description:** Display aspect ratio (informational)

**Examples:**

```env
VIDEO_ASPECT_RATIO=9:16   # Vertical (default)
VIDEO_ASPECT_RATIO=16:9   # Horizontal (YouTube, Desktop)
VIDEO_ASPECT_RATIO=1:1    # Square (Instagram Feed)
VIDEO_ASPECT_RATIO=4:5    # Portrait (Pinterest, Reels)
```

### `IMAGE_ASPECT_RATIO`

**Type:** String (format: `W:H`)  
**Default:** Uses `VIDEO_ASPECT_RATIO`  
**Description:** Aspect ratio for generated images

**Note:** If not set, inherits from VIDEO_ASPECT_RATIO

**Examples:**

```env
IMAGE_ASPECT_RATIO=9:16   # Match video dimensions
IMAGE_ASPECT_RATIO=1:1    # Square images (different from video)
```

---

## LLM Configuration

Configure language models for text generation.

### `LLM_PROVIDER`

**Type:** String  
**Options:** `lmstudio`, `gemini`  
**Default:** `lmstudio`  
**Description:** Primary LLM provider

**lmstudio (Recommended):**

- ✅ Private (runs locally)
- ✅ Free (no API costs)
- ✅ Fast (if GPU available)
- ⚠️ Requires LM Studio app running

**gemini:**

- ✅ No local setup needed
- ✅ Powerful models
- ⚠️ Cloud-based (privacy)
- ⚠️ API costs ($)

### `LM_STUDIO_ENABLED`

**Type:** Boolean  
**Default:** `true`  
**Description:** Enable LM Studio integration

### `LM_STUDIO_BASE_URL`

**Type:** URL  
**Default:** `http://localhost:1234/v1`  
**Description:** LM Studio API endpoint

**Must match LM Studio settings:**

```env
# Standard (port 1234)
LM_STUDIO_BASE_URL=http://localhost:1234/v1

# Custom port
LM_STUDIO_BASE_URL=http://localhost:5000/v1

# Remote server
LM_STUDIO_BASE_URL=http://192.168.1.100:1234/v1
```

### `LM_STUDIO_API_KEY`

**Type:** String  
**Default:** `lm-studio`  
**Description:** API key (standard for LM Studio)

**Note:** Usually just `lm-studio`, don't change unless customized

### `LM_STUDIO_MODEL`

**Type:** String  
**Default:** `auto`  
**Options:** `auto`, `mistral-7b`, `llama-2-7b`, etc.  
**Description:** Model name to use

**Common Models:**

```env
LM_STUDIO_MODEL=auto              # Auto-detect loaded model
LM_STUDIO_MODEL=mistral-7b-instruct  # Fast, capable
LM_STUDIO_MODEL=neural-chat-7b    # Optimized chat
LM_STUDIO_MODEL=llama-2-7b        # Meta model
```

### `LM_STUDIO_AUTO_DETECT`

**Type:** Boolean  
**Default:** `true`  
**Description:** Automatically detect LM Studio model

**When enabled:**

- Queries LM Studio API for available models
- Uses first available model
- Ignores `LM_STUDIO_MODEL` setting

### `GEMINI_API_KEY`

**Type:** String  
**Default:** (empty - fallback only)  
**Description:** Google Gemini API key

**Get key:**

1. Visit https://ai.google.dev/
2. Click "Get started"
3. Create API key
4. Copy to .env

```env
GEMINI_API_KEY=AIzaSy...your_long_key_here...
```

### `GEMINI_TEXT_MODEL`

**Type:** String  
**Default:** `gemini-2.5-flash`  
**Options:** `gemini-2.5-flash`, `gemini-1.5-pro`, etc.  
**Description:** Model for text generation

```env
GEMINI_TEXT_MODEL=gemini-2.5-flash     # Fast, cheap (recommended)
GEMINI_TEXT_MODEL=gemini-1.5-pro       # Slower, more capable
```

### `GEMINI_IMAGE_MODEL`

**Type:** String  
**Default:** `gemini-2.0-flash-exp`  
**Description:** Model for image generation

```env
GEMINI_IMAGE_MODEL=gemini-2.0-flash-exp
GEMINI_IMAGE_MODEL=gemini-pro-vision
```

---

## API Keys

External service authentication.

### `APIFY_API_TOKEN`

**Type:** String  
**Required for:** Researcher agent (Meta ads scraping)  
**Default:** (empty)

**Get token:**

1. Visit https://apify.com/
2. Sign up (free tier available)
3. Get API token from Settings
4. Add to .env

```env
APIFY_API_TOKEN=apif_your_token_here
```

### `APIFY_META_ADS_ACTOR_ID`

**Type:** String  
**Default:** `whoareyouanas/meta-ad-scraper`  
**Description:** Apify actor to use for scraping

**Options:**

```env
# Recommended
APIFY_META_ADS_ACTOR_ID=whoareyouanas/meta-ad-scraper

# Alternative
APIFY_META_ADS_ACTOR_ID=apify/meta-ads-dataset
```

### `APIFY_META_ADS_SEARCH_QUERY`

**Type:** String  
**Default:** `trading`  
**Description:** What ads to search for

**Examples:**

```env
APIFY_META_ADS_SEARCH_QUERY=forex trading
APIFY_META_ADS_SEARCH_QUERY=cryptocurrency
APIFY_META_ADS_SEARCH_QUERY=fitness training
APIFY_META_ADS_SEARCH_QUERY=weight loss
```

### `APIFY_META_ADS_COUNTRY`

**Type:** String (2-letter country code)  
**Default:** `US`  
**Description:** Country for ad targeting

```env
APIFY_META_ADS_COUNTRY=US    # United States
APIFY_META_ADS_COUNTRY=GB    # United Kingdom
APIFY_META_ADS_COUNTRY=CA    # Canada
APIFY_META_ADS_COUNTRY=AU    # Australia
```

### `APIFY_META_ADS_MAX_AGE_DAYS`

**Type:** Integer  
**Default:** `30`  
**Range:** 1-365  
**Description:** Maximum age of ads to include

```env
APIFY_META_ADS_MAX_AGE_DAYS=7      # Recent ads only
APIFY_META_ADS_MAX_AGE_DAYS=30     # Last month
APIFY_META_ADS_MAX_AGE_DAYS=90     # Last 3 months
```

---

## Media Generation

Configuration for images, audio, and voice.

### Text-to-Speech

#### `TTS_PROVIDER`

**Type:** String  
**Options:** `edge-tts`, `elevenlabs`  
**Default:** `edge-tts`  
**Description:** Primary TTS provider

**edge-tts (Recommended):**

- ✅ Free (Microsoft)
- ✅ No API key needed
- ✅ Good quality
- ⚠️ Limited voices

**elevenlabs:**

- ✅ Premium quality
- ✅ Many voices
- ⚠️ Requires API key
- ⚠️ Costs money

#### `TTS_FALLBACK`

**Type:** String  
**Options:** `elevenlabs`, `edge-tts`  
**Default:** `elevenlabs`  
**Description:** Fallback if primary TTS fails

#### `EDGE_TTS_VOICE`

**Type:** String  
**Default:** `en-US-AriaNeural`  
**Description:** Voice for Edge TTS

**Available Voices:**

**American English:**

```
en-US-AriaNeural          (female, professional)
en-US-GuyNeural           (male, professional)
en-US-JennyNeural         (female, friendly)
en-US-AmberNeural         (female, warm)
en-US-AshleyNeural        (female, neutral)
```

**British English:**

```
en-GB-RyanNeural          (male, professional)
en-GB-SoniaNeural         (female, professional)
en-GB-LibbyNeural         (female, friendly)
```

**Australian English:**

```
en-AU-NatashaNeural       (female)
en-AU-WilliamNeural       (male)
```

#### `EDGE_TTS_LANGUAGE`

**Type:** String  
**Default:** `en-US`  
**Description:** Language/locale for Edge TTS

```env
EDGE_TTS_LANGUAGE=en-US      # US English
EDGE_TTS_LANGUAGE=en-GB      # British English
EDGE_TTS_LANGUAGE=en-AU      # Australian English
```

#### `EDGE_TTS_OUTPUT_FORMAT`

**Type:** String  
**Default:** `audio-24khz-48kbitrate-mono-mp3`  
**Description:** Audio output format

**Common Formats:**

```
audio-24khz-48kbitrate-mono-mp3    (good quality)
audio-24khz-32kbitrate-mono-mp3    (smaller files)
audio-16khz-32kbitrate-mono-mp3    (low quality)
```

#### `ELEVENLABS_API_KEY`

**Type:** String  
**Required for:** Premium TTS or fallback  
**Default:** (empty)

**Get key:**

1. Visit https://elevenlabs.io/
2. Sign up (free tier available)
3. Get API key from Settings
4. Add to .env

```env
ELEVENLABS_API_KEY=sk_your_key_here
```

#### `ELEVENLABS_VOICE_ID`

**Type:** String  
**Default:** `21m00Tcm4TlvDq8ikWAM`  
**Description:** Voice ID for ElevenLabs

**Popular Voices:**

```
21m00Tcm4TlvDq8ikWAM    (Rachel, female, professional)
EXAVITQu4zHgPcw14YNe    (Bella, female, warm)
TX3LPaxmHKvcMaxdDDMd    (Michael, male, professional)
```

#### `ELEVENLABS_MODEL_ID`

**Type:** String  
**Default:** `eleven_multilingual_v2`  
**Options:** `eleven_multilingual_v2`, `eleven_monolog_v1`  
**Description:** ElevenLabs model

---

### Image Generation

#### `GEMINI_IMAGE_ENDPOINT`

**Type:** URL  
**Default:** `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent`  
**Description:** Gemini image generation endpoint

**Note:** Usually doesn't need changing

#### Fallback: Pollinations.ai

If Gemini API key not set, automatically uses free Pollinations.ai:

- ✅ Free (no auth needed)
- ✅ Fast
- ⚠️ Lower quality than Gemini

---

## Google Drive Integration

Extract source material from Google Docs.

### `GOOGLE_APPLICATION_CREDENTIALS`

**Type:** File path  
**Default:** (empty)  
**Description:** Path to Google service account JSON

**Setup:**

1. Visit https://console.cloud.google.com/
2. Create new project
3. Enable Google Drive API
4. Create Service Account
5. Download JSON key
6. Set path to key:

```env
GOOGLE_APPLICATION_CREDENTIALS=./cred.json
```

### `GOOGLE_DRIVE_FILE_ID`

**Type:** String  
**Default:** (empty)  
**Description:** ID of Google Doc to extract text from

**Get ID:**

1. Open Google Doc
2. Copy from URL: `docs.google.com/document/d/{ID}/`
3. Add to .env:

```env
GOOGLE_DRIVE_FILE_ID=1abc...xyz123...
```

### `GOOGLE_DRIVE_SCOPES`

**Type:** URL  
**Default:** `https://www.googleapis.com/auth/drive.readonly`  
**Description:** Google API permissions

**Common Scopes:**

```
drive.readonly               (read-only access)
drive                        (full access)
docs                         (Google Docs only)
```

---

## Output & Logging

### `RUN_LOG_FILE`

**Type:** File path  
**Default:** `./output/run.log`  
**Description:** Where to save execution logs

**Examples:**

```env
RUN_LOG_FILE=./output/run.log        # Default
RUN_LOG_FILE=./logs/execution.log    # Custom location
RUN_LOG_FILE=~/video_generation.log  # Home directory
```

### `LOG_LEVEL`

**Type:** String  
**Options:** `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`  
**Default:** `INFO`  
**Description:** Logging verbosity level

**Levels:**

```
DEBUG      # Very detailed (development)
INFO       # Normal info messages (default)
WARNING    # Warning messages only
ERROR      # Errors only
CRITICAL   # Critical errors only
```

**Examples:**

```env
LOG_LEVEL=DEBUG     # See all details
LOG_LEVEL=INFO      # Normal (recommended)
LOG_LEVEL=ERROR     # Only errors
```

---

## Remotion Settings

Video rendering configuration.

### `REMOTION_APP_DIR`

**Type:** Directory path  
**Default:** `./remotion-app`  
**Description:** Location of Remotion app

```env
REMOTION_APP_DIR=./remotion-app        # Default (relative)
REMOTION_APP_DIR=/absolute/path/app    # Absolute path
```

### `REMOTION_ENTRY_POINT`

**Type:** File path  
**Default:** `src/index.tsx`  
**Description:** Entry point for Remotion composition

```env
REMOTION_ENTRY_POINT=src/index.tsx     # Standard
REMOTION_ENTRY_POINT=src/Video.tsx     # Custom
```

### `REMOTION_COMPOSITION_ID`

**Type:** String  
**Default:** `Video`  
**Description:** Composition name to render

```env
REMOTION_COMPOSITION_ID=Video          # Default
REMOTION_COMPOSITION_ID=VideoEnhanced  # Enhanced
```

### `RENDER_OUTPUT_DIR`

**Type:** Directory path  
**Default:** `out`  
**Description:** Output directory within Remotion app

```env
RENDER_OUTPUT_DIR=out                  # Default
RENDER_OUTPUT_DIR=build                # Custom
RENDER_OUTPUT_DIR=videos               # Custom
```

---

## Advanced Options

### Scene Timing

#### `SCENE_MIN_DURATION_SECONDS`

**Type:** Float  
**Default:** `3`  
**Range:** 0.5-10  
**Description:** Minimum time each scene displays

```env
SCENE_MIN_DURATION_SECONDS=3      # 3 seconds minimum
SCENE_MIN_DURATION_SECONDS=5      # Longer scenes
SCENE_MIN_DURATION_SECONDS=1      # Quick cuts
```

#### `SCENE_GAP_SECONDS`

**Type:** Float  
**Default:** `0.5`  
**Range:** 0-2  
**Description:** Time between scenes (transitions)

```env
SCENE_GAP_SECONDS=0.5     # Half second
SCENE_GAP_SECONDS=1       # One second
SCENE_GAP_SECONDS=0       # No gap
```

---

## Environment File Examples

### Minimal Setup (Local Only)

```env
# Video
VIDEO_WIDTH=1080
VIDEO_HEIGHT=1920

# Local LLM
LLM_PROVIDER=lmstudio
LM_STUDIO_BASE_URL=http://localhost:1234/v1

# Audio
TTS_PROVIDER=edge-tts
EDGE_TTS_VOICE=en-US-AriaNeural

# Logging
LOG_LEVEL=INFO
```

### Full Setup (Cloud APIs)

```env
# Video
VIDEO_WIDTH=1080
VIDEO_HEIGHT=1920

# LLM
GEMINI_API_KEY=AIzaSy...
GEMINI_TEXT_MODEL=gemini-2.5-flash

# Media Scraping
APIFY_API_TOKEN=apif_...
APIFY_META_ADS_SEARCH_QUERY=trading

# TTS
TTS_PROVIDER=elevenlabs
ELEVENLABS_API_KEY=sk_...
EDGE_TTS_VOICE=en-US-AriaNeural

# Google Docs
GOOGLE_APPLICATION_CREDENTIALS=./cred.json
GOOGLE_DRIVE_FILE_ID=1abc...

# Logging
LOG_LEVEL=INFO
RUN_LOG_FILE=./output/run.log

# Remotion
REMOTION_APP_DIR=./remotion-app
REMOTION_ENTRY_POINT=src/index.tsx
REMOTION_COMPOSITION_ID=Video
```

### Development Setup

```env
# Local everything
LLM_PROVIDER=lmstudio
LM_STUDIO_AUTO_DETECT=true

# Verbose logging
LOG_LEVEL=DEBUG

# Quick renders
SCENE_MIN_DURATION_SECONDS=2
VIDEO_WIDTH=720
VIDEO_HEIGHT=1280

# Short output names
RUN_LOG_FILE=./log.txt
```

---

## Configuration Precedence

Settings are loaded in this order:

1. **Environment variables** (highest priority)
2. **.env file** in project root
3. **Pydantic defaults** in `config/settings.py`
4. **System defaults**

**Example:** If you set `GEMINI_API_KEY` as environment variable, it overrides .env file.

---

## Validation

Invalid values will cause errors at startup:

```bash
# Test configuration
python -c "from config.settings import get_settings; s = get_settings(); print(f'✓ Config valid: {s.VIDEO_WIDTH}x{s.VIDEO_HEIGHT}')"
```

Common errors:

- Empty `LM_STUDIO_BASE_URL`
- Invalid `VIDEO_WIDTH` (not a number)
- Non-existent file path for credentials
- Invalid API key format

---

**See .env.example for all options with descriptions**
