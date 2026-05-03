# 🔧 Complete Setup Guide

This guide provides step-by-step instructions for setting up the Internship Agent Dev tool on Windows, macOS, or Linux.

---

## Table of Contents

1. [System Requirements](#system-requirements)
2. [Installation Steps](#installation-steps)
3. [Environment Configuration](#environment-configuration)
4. [Verification](#verification)
5. [Troubleshooting](#troubleshooting)

---

## System Requirements

### Minimum Requirements

- **OS:** Windows 10+, macOS 10.15+, or Linux (Ubuntu 20.04+)
- **Python:** 3.13 or later
- **Node.js:** 18.0 or later
- **RAM:** 8 GB
- **Disk Space:** 2 GB

### Recommended Setup

- **OS:** Windows 11 or macOS 12+
- **Python:** 3.13 (latest)
- **Node.js:** 20 LTS or later
- **RAM:** 16 GB
- **GPU:** Optional (for faster rendering with Remotion)

### Verify Installed Versions

```bash
# Check Python
python --version
# Expected: Python 3.13.x

# Check Node.js
node --version
# Expected: v18.x.x or v20.x.x

npm --version
# Expected: 9.x.x or later

# Check Git
git --version
# Expected: git version 2.x.x
```

If any are missing, install from:

- **Python:** https://www.python.org/downloads/
- **Node.js:** https://nodejs.org/ (installs npm automatically)
- **Git:** https://git-scm.com/

---

## Installation Steps

### Step 1: Clone/Navigate to Project

```bash
# If cloning:
git clone <repository-url>
cd internship-agent-dev

# Or if you already have the folder:
cd Internship\ agent\ dev
```

### Step 2: Create Virtual Environment

A virtual environment isolates project dependencies from your system Python.

**On Windows:**

```bash
python -m venv .venv
.venv\Scripts\activate
```

**On macOS/Linux:**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

**Verify activation:**

```bash
# Your prompt should show (.venv) prefix
# Like: (.venv) C:\Users\...\Internship agent dev>
```

### Step 3: Upgrade pip

```bash
# Ensure you have the latest pip
python -m pip install --upgrade pip
```

### Step 4: Install Python Dependencies

```bash
# Install all required packages
pip install -r requirements.txt

# Verify installation
pip list | grep -E "pydantic|httpx|Pillow|edge-tts|mutagen"
```

**Expected packages:**

- `pydantic` - Configuration management
- `httpx` - Async HTTP requests
- `Pillow` - Image processing
- `edge-tts` - Text-to-speech
- `mutagen` - Audio metadata

### Step 5: Setup Remotion (Node.js)

```bash
# Navigate to Remotion app
cd remotion-app

# Install dependencies
npm install
# or
npm ci  # More reliable, uses exact versions from package-lock.json

# Wait for installation to complete (1-3 minutes)

# Verify installation
npm list remotion
# Should show: remotion@4.x.x

# Go back to project root
cd ..
```

### Step 6: Create Environment File

```bash
# Copy the example environment file
cp .env.example .env

# On Windows PowerShell:
Copy-Item .env.example .env

# Edit .env with your settings
# See Environment Configuration section below
```

### Step 7: Verify Installation

```bash
# Test Python imports
python -c "import agents; print('✓ agents module OK')"

# Test Node/Remotion
cd remotion-app
npx remotion --version
cd ..
```

---

## Environment Configuration

### Quick Setup (Local Only - No API Keys)

For testing without external API costs:

```bash
# Edit .env with these minimal settings:

# Local LLM
LLM_PROVIDER=lmstudio
LM_STUDIO_BASE_URL=http://localhost:1234/v1
LM_STUDIO_MODEL=auto

# Video settings
VIDEO_WIDTH=1080
VIDEO_HEIGHT=1920
VIDEO_ASPECT_RATIO=9:16

# Logging
LOG_LEVEL=INFO
RUN_LOG_FILE=./output/run.log
```

**Note:** Before running, start LM Studio (see below)

### Setup with API Keys (Production)

If you want full features with cloud APIs:

#### 1. Get Gemini API Key

```
1. Visit: https://ai.google.dev/
2. Click "Get started with Google AI Studio"
3. Create/select a Google Cloud project
4. Create new API key
5. Copy key to .env:
```

```env
GEMINI_API_KEY=AIzaSy...your_key_here...
GEMINI_TEXT_MODEL=gemini-2.5-flash
```

#### 2. Get Apify Token (Optional - for Meta Ads scraping)

```
1. Visit: https://apify.com/
2. Sign up for free account
3. Get your API token from Settings
4. Add to .env:
```

```env
APIFY_API_TOKEN=apif_your_token...
APIFY_META_ADS_ACTOR_ID=whoareyouanas/meta-ad-scraper
```

#### 3. Get Google Docs Integration (Optional)

```
1. Visit: https://console.cloud.google.com/
2. Create new project
3. Enable "Google Drive API" and "Google Docs API"
4. Create Service Account
5. Download JSON key
6. Share Google Doc with service account email
7. Add to .env:
```

```env
GOOGLE_APPLICATION_CREDENTIALS=./cred.json
GOOGLE_DRIVE_FILE_ID=your_doc_id
```

#### 4. Get ElevenLabs Key (Optional - premium voices)

```
1. Visit: https://elevenlabs.io/
2. Sign up for account
3. Get API key from Settings
4. Add to .env:
```

```env
ELEVENLABS_API_KEY=sk_...
ELEVENLABS_VOICE_ID=21m00Tcm4TlvDq8ikWAM
```

### Complete .env Example

See [.env.example](.env.example) for all 50+ options with full documentation.

Key sections:

- **Video Settings** - Dimensions, aspect ratios
- **LM Studio** - Local LLM configuration
- **Gemini API** - Text and image generation
- **Apify** - Meta ads scraping
- **Google Drive** - Source material
- **TTS** - Audio synthesis
- **Remotion** - Video rendering

---

## LM Studio Setup (Recommended)

For **privacy-first** local inference without API costs:

### Step 1: Download & Install

1. Visit https://lmstudio.ai/
2. Download for your OS (Windows/Mac/Linux)
3. Run installer
4. Complete installation

### Step 2: Load a Model

1. Open LM Studio
2. Click "Model Library" (left sidebar)
3. Search for a model:
   - **Mistral 7B** (Recommended - fast, capable)
   - **Llama 2 7B** (Alternative - smaller)
   - **Neural Chat** (Alternative - faster)
4. Click download
5. Wait for download (1-5 GB, takes 5-20 minutes)

### Step 3: Start Local Server

1. Click "Local Server" (left sidebar)
2. Select your downloaded model in dropdown
3. Click "Start Server"
4. Wait for message: "Server started on http://localhost:1234"

### Step 4: Verify Connection

```bash
# Test the local server
curl http://localhost:1234/v1/models

# Should return JSON with available models
```

### Step 5: Update .env

```env
LLM_PROVIDER=lmstudio
LM_STUDIO_BASE_URL=http://localhost:1234/v1
LM_STUDIO_MODEL=auto
LM_STUDIO_AUTO_DETECT=true
```

**Now you can run the tool without any API keys!**

---

## Verification

### Test 1: Python Environment

```bash
# Ensure venv is activated (should see (.venv) in prompt)

# Test all imports
python -c "
import agents
from config.settings import get_settings
from src.core.director import build_remotion_props
from src.media.gemini_image import generate_image
from src.utils import get_logger
print('✓ All Python imports OK')
"
```

**Expected output:** `✓ All Python imports OK`

### Test 2: Node/Remotion

```bash
cd remotion-app
npx remotion --version
# Expected: @remotion/cli 4.x.x
cd ..
```

### Test 3: Configuration

```bash
# Verify .env is correctly loaded
python -c "
from config.settings import get_settings
s = get_settings()
print(f'✓ Video: {s.VIDEO_WIDTH}x{s.VIDEO_HEIGHT}')
print(f'✓ LLM: {s.LM_STUDIO_BASE_URL}')
print(f'✓ Log: {s.RUN_LOG_FILE}')
"
```

### Test 4: Full Pipeline (Optional - with test data)

```bash
# This tests without real API calls
python agents.py render
# Should show: "Remotion: render complete"
```

---

## Troubleshooting

### Python Installation Issues

**Problem:** `python: command not found`

**Solution:**

```bash
# Verify Python is installed
python3 --version

# If not found, install from https://www.python.org/
# Or use package manager:
# macOS: brew install python@3.13
# Ubuntu: sudo apt install python3.13
# Windows: Download from python.org
```

**Problem:** Virtual environment activation fails

**Solution:**

```bash
# Delete and recreate venv
rm -rf .venv
python -m venv .venv

# Windows:
# Delete and recreate
rmdir /s .venv
python -m venv .venv
```

### Node/Remotion Issues

**Problem:** `npm: command not found`

**Solution:**

```bash
# Reinstall Node.js from https://nodejs.org/
# Make sure you download LTS version (currently 20.x)
# Verify: node --version && npm --version
```

**Problem:** Remotion install fails

**Solution:**

```bash
# Clear npm cache and reinstall
cd remotion-app
npm cache clean --force
rm -rf node_modules package-lock.json
npm install
cd ..
```

### Environment/Configuration Issues

**Problem:** `.env` file not being read

**Solution:**

```bash
# Verify .env exists in project root
ls -la .env  # macOS/Linux
dir .env    # Windows

# Verify it has content
cat .env | head -20

# Ensure no BOM (Byte Order Mark)
# If using Windows Notepad, save as UTF-8 without BOM
```

**Problem:** `ImportError: No module named 'lmstudio'`

**Solution:** LM Studio is not a Python module - it's a separate desktop app

```bash
# You need to:
# 1. Download LM Studio from https://lmstudio.ai/
# 2. Start the local server (Server tab)
# 3. Verify: curl http://localhost:1234/v1/models
```

### Permission Issues

**Problem:** `Permission denied` when running scripts

**Solution (macOS/Linux):**

```bash
# Make script executable
chmod +x agents.py

# Or run with python directly
python agents.py all
```

**Solution (Windows):**

```powershell
# If in PowerShell, allow execution
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned

# Then run
python agents.py all
```

### Common Setup Errors

| Error                           | Cause                      | Solution                                                    |
| ------------------------------- | -------------------------- | ----------------------------------------------------------- |
| `ModuleNotFoundError`           | Dependencies not installed | `pip install -r requirements.txt`                           |
| `LM_STUDIO: connection refused` | LM Studio not running      | Start LM Studio app, go to Server tab                       |
| `GEMINI_API_KEY: empty`         | API key not set            | Add key to .env, restart terminal                           |
| `Remotion: render failed`       | Assets missing             | Run `python agents.py director` first                       |
| `ffprobe: not found`            | FFmpeg not installed       | Install via `conda install ffmpeg` or `brew install ffmpeg` |

---

## Next Steps

Once setup is complete:

1. ✅ Review [USAGE.md](USAGE.md) for commands
2. ✅ Check [CONFIGURATION.md](CONFIGURATION.md) for all options
3. ✅ Run your first video: `python agents.py render`
4. ✅ Customize design: See [TEMPLATE_GUIDE.md](TEMPLATE_GUIDE.md)

---

## Getting Help

- **Issues:** Check troubleshooting section above
- **Detailed Config:** See [CONFIGURATION.md](CONFIGURATION.md)
- **API Setup:** See [API_KEYS.md](API_KEYS.md)
- **Template:** See [TEMPLATE_GUIDE.md](TEMPLATE_GUIDE.md)

---

**✅ Setup Complete! Ready to generate videos.**
