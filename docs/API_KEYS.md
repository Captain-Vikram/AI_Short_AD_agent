# 🔑 How to Get API Keys

Step-by-step guides for obtaining credentials from each service.

---

## Table of Contents

1. [Quick Summary](#quick-summary)
2. [Gemini API (Google)](#gemini-api-google)
3. [Apify Token](#apify-token)
4. [Google Drive/Docs](#google-drivedocs)
5. [ElevenLabs (Optional)](#elevenlabs-optional)
6. [LM Studio (Local - No Key Needed)](#lm-studio-local--no-key-needed)

---

## Quick Summary

| Service     | Required?     | Cost      | Setup Time |
| ----------- | ------------- | --------- | ---------- |
| LM Studio   | No (local)    | Free      | 5-15 min   |
| Gemini API  | No (fallback) | Free tier | 5 min      |
| Apify       | No (fallback) | Free tier | 5 min      |
| Google Docs | No (optional) | Free      | 10 min     |
| ElevenLabs  | No (optional) | Free tier | 5 min      |
| Edge TTS    | No (builtin)  | Free      | 0 min      |

**Minimum Setup:** Start with LM Studio only (completely free, no API keys)

---

## Gemini API (Google)

**Used for:** Text generation, image generation  
**Cost:** Free tier available (60 requests/minute)  
**Setup Time:** 5 minutes

### Step 1: Visit Google AI Studio

```
https://ai.google.dev/
```

### Step 2: Click "Get Started"

- Scroll down
- Click blue "Get API Key" button
- Select "Create API key in new project"

### Step 3: Create/Select Project

- Choose "Create a new Google Cloud project"
- Or select existing project
- Click "CREATE"

### Step 4: Copy API Key

- Click "Copy" button next to API key
- Save somewhere safe (treat like password)

### Step 5: Add to .env

```bash
# Edit .env file
nano .env
# or
vim .env
# or use your text editor

# Add this line:
GEMINI_API_KEY=AIzaSy...your_long_key_here...

# Save and exit
```

### Step 6: Verify

```bash
# Test the API key
python -c "
from config.settings import get_settings
s = get_settings()
if s.GEMINI_API_KEY:
    print(f'✓ Gemini API key configured')
else:
    print('✗ Gemini API key not set')
"
```

### Usage Notes

- **Free tier:** 60 requests/minute, high daily limits
- **Models:** Choose `gemini-2.5-flash` (recommended) or `gemini-1.5-pro`
- **Cost:** Free for most use (check Google Cloud Console for usage)

### Troubleshooting

**Issue:** "Invalid API key" error

**Solution:**

```bash
# Verify key format (should start with AIzaSy...)
echo $GEMINI_API_KEY

# Check for extra whitespace
# Edit .env and remove any spaces around =
GEMINI_API_KEY=AIzaSy...  # Wrong (has space after)
GEMINI_API_KEY=AIzaSy...  # Correct
```

**Issue:** "API key restricted"

**Solution:**

1. Visit Google Cloud Console
2. Find your API key
3. Click to edit
4. Remove any API restrictions
5. Save and retry

---

## Apify Token

**Used for:** Scraping Meta ads (Facebook/Instagram)  
**Cost:** Free tier available  
**Setup Time:** 5 minutes

### Step 1: Sign Up

```
https://apify.com/
```

Click "Sign Up" → Fill in details → Click "Create Account"

### Step 2: Verify Email

- Check your email
- Click verification link
- Return to Apify

### Step 3: Get API Token

**Method A (Dashboard):**

1. Click your profile icon (top right)
2. Click "Settings"
3. Find "API tokens" section
4. Click "Create token"
5. Copy the token

**Method B (Direct):**

```
https://console.apify.com/account/integrations
```

### Step 4: Add to .env

```bash
# Edit .env
APIFY_API_TOKEN=apif_your_token_here

# Also set search query
APIFY_META_ADS_SEARCH_QUERY=trading
APIFY_META_ADS_COUNTRY=US
```

### Step 5: Verify

```bash
python -c "
from config.settings import get_settings
s = get_settings()
if s.APIFY_API_TOKEN:
    print(f'✓ Apify token configured')
else:
    print('✗ Apify token not set')
"
```

### Usage Notes

- **Free tier:** 5,000 API calls/month
- **Actor:** Use `whoareyouanas/meta-ad-scraper` (recommended)
- **Search queries:** Examples: "trading", "crypto", "forex", "weight loss"

### Troubleshooting

**Issue:** "Invalid API token"

**Solution:**

```bash
# Verify token format
echo $APIFY_API_TOKEN
# Should be: apif_something...

# Check if token has spaces
cat .env | grep APIFY_API_TOKEN
# Remove any whitespace around =
```

**Issue:** "Unauthorized" when running researcher

**Solution:**

1. Check API token is valid (test in Apify dashboard)
2. Check monthly quota not exceeded (Apify Console → API Usage)
3. Try creating new token and updating .env

---

## Google Drive/Docs

**Used for:** Extracting text from Google Docs as source material  
**Cost:** Free  
**Setup Time:** 10 minutes  
**Note:** Optional - only needed if using Google Docs as input

### Step 1: Create Google Cloud Project

1. Visit https://console.cloud.google.com/
2. Click project dropdown (top left)
3. Click "NEW PROJECT"
4. Name: "Video Generator"
5. Click "CREATE"
6. Wait for creation (1-2 minutes)

### Step 2: Enable APIs

1. In search box at top, search: "Google Drive API"
2. Click "Google Drive API"
3. Click "ENABLE"
4. Wait for it to enable
5. Go back and search: "Google Docs API"
6. Click "Google Docs API"
7. Click "ENABLE"

### Step 3: Create Service Account

1. In left menu, click "Credentials"
2. Click "CREATE CREDENTIALS"
3. Select "Service Account"
4. Fill in details:
   - Service account name: "video-generator"
   - Description: "For video generation"
5. Click "CREATE AND CONTINUE"
6. Click "CONTINUE" (skip optional steps)
7. Click "DONE"

### Step 4: Create JSON Key

1. Find your service account in the list
2. Click on the email address
3. Go to "KEYS" tab
4. Click "ADD KEY" → "Create new key"
5. Select "JSON"
6. Click "CREATE"
7. File downloads automatically (save as `cred.json`)

### Step 5: Place JSON File

```bash
# Move the downloaded JSON file to project root
mv ~/Downloads/[service-account-name].json ./cred.json

# Verify
ls -la cred.json
```

### Step 6: Share Google Doc

1. Open your Google Doc
2. Click "Share" (top right)
3. Copy email from your `cred.json` file:
   ```json
   {
     "client_email": "video-generator@project...iam.gserviceaccount.com"
   }
   ```
4. Paste in share dialog
5. Click "Share" (you don't need to send email)

### Step 7: Add to .env

```bash
# Get your Google Doc ID
# Open doc → URL: docs.google.com/document/d/[ID]/edit
# Copy [ID]

GOOGLE_APPLICATION_CREDENTIALS=./cred.json
GOOGLE_DRIVE_FILE_ID=your_document_id_here
```

### Step 8: Verify

```bash
python -c "
from config.settings import get_settings
s = get_settings()
creds = s.GOOGLE_APPLICATION_CREDENTIALS
doc_id = s.GOOGLE_DRIVE_FILE_ID
if creds and doc_id:
    print(f'✓ Google Docs configured')
else:
    print('✗ Google Docs not configured')
"
```

### Usage Notes

- **Permissions:** Service account needs read access to document
- **Formats:** Extracts plain text from Google Docs
- **Usage:** Used by Copywriter agent to get source material

### Troubleshooting

**Issue:** "404 Document not found"

**Solution:**

```bash
# Verify you shared the doc with service account email
# Check GOOGLE_DRIVE_FILE_ID is correct:
# Open doc → URL: docs.google.com/document/d/[ID]/

# Test:
python -c "
from src.media.gdrive_helper import fetch_doc_text
text = fetch_doc_text()
print(f'Document text: {text[:100]}...')
"
```

**Issue:** "Permission denied"

**Solution:**

1. Open Google Doc
2. Click "Share"
3. Verify service account email is listed
4. Check it has "Editor" access
5. Retry

---

## ElevenLabs (Optional)

**Used for:** Premium voice synthesis (alternative to Edge TTS)  
**Cost:** Free tier (10,000 characters/month)  
**Setup Time:** 5 minutes  
**Note:** Optional - Edge TTS is free and works well

### When to Use ElevenLabs

- ✅ Want premium natural-sounding voices
- ✅ Need specific voice options
- ✅ Generating many videos (more quota)

### When to Skip

- ✅ Using Edge TTS (free, built-in)
- ✅ Want to save money
- ✅ Quality is adequate

### Step 1: Sign Up

```
https://elevenlabs.io/
```

Click "Sign Up" → Fill details → "Create Account"

### Step 2: Verify Email

- Check email
- Click verification link
- Return to ElevenLabs

### Step 3: Get API Key

1. Click profile icon (top right)
2. Click "Profile"
3. Scroll to "API Key"
4. Click "Copy"

### Step 4: Select Voice

1. Go to "Voice Lab"
2. Browse available voices
3. Note the Voice ID
4. Common voice IDs:
   ```
   21m00Tcm4TlvDq8ikWAM    Rachel (female, professional)
   EXAVITQu4zHgPcw14YNe    Bella (female, warm)
   TX3LPaxmHKvcMaxdDDMd    Michael (male)
   ```

### Step 5: Add to .env

```bash
# Primary: Edge TTS (free)
TTS_PROVIDER=edge-tts

# Fallback: ElevenLabs (premium)
TTS_FALLBACK=elevenlabs
ELEVENLABS_API_KEY=sk_your_key_here
ELEVENLABS_VOICE_ID=21m00Tcm4TlvDq8ikWAM
```

### Step 6: Verify

```bash
python -c "
from config.settings import get_settings
s = get_settings()
if s.ELEVENLABS_API_KEY:
    print(f'✓ ElevenLabs configured')
else:
    print('✗ ElevenLabs not configured')
"
```

### Usage Notes

- **Free tier:** 10,000 characters/month
- **Upgrade:** Paid plans for more usage
- **Voices:** Browse all voices in "Voice Lab"
- **Billing:** See usage in Account → Billing

### Troubleshooting

**Issue:** "Invalid API key"

**Solution:**

```bash
# Verify key format (should start with sk_)
echo $ELEVENLABS_API_KEY

# Check for spaces around =
# Should be: ELEVENLABS_API_KEY=sk_...
```

**Issue:** "Quota exceeded"

**Solution:**

1. Wait until next month (resets monthly)
2. Upgrade ElevenLabs account
3. Use Edge TTS instead (free, unlimited)

---

## LM Studio (Local - No Key Needed)

**Used for:** Text generation (local, private)  
**Cost:** Free  
**Setup Time:** 10-20 minutes

### Why LM Studio?

- ✅ Completely private (runs on your computer)
- ✅ Free (no API costs)
- ✅ Fast (if you have GPU)
- ✅ No internet required
- ⚠️ Requires downloading model (1-7 GB)

### Step 1: Download LM Studio

```
https://lmstudio.ai/
```

Download for your OS:

- Windows → `.exe` installer
- macOS → `.dmg` installer
- Linux → `.AppImage` or `.deb`

### Step 2: Install

**Windows:** Run installer, click through, install

**macOS:** Double-click `.dmg`, drag to Applications

**Linux:**

```bash
chmod +x LM\ Studio-[version].AppImage
./LM\ Studio-[version].AppImage
```

### Step 3: Open LM Studio

- Windows: Search for "LM Studio", click
- macOS: Open Applications folder, double-click "LM Studio"
- Linux: Run the AppImage

### Step 4: Load a Model

1. Click "Model Library" (left sidebar)
2. Search for:
   - **Mistral 7B** (recommended - fast, capable)
   - **Llama 2 7B** (good alternative)
   - **Neural Chat 7B** (optimized for chat)
3. Click model
4. Click "Download"
5. Wait for download (1-7 GB, takes 5-30 minutes)

**Note:** Choose based on your RAM:

- 8 GB RAM → 7B model (smallest)
- 16+ GB RAM → 13B model (better quality)

### Step 5: Start Local Server

1. Click "Local Server" (left sidebar)
2. Select your model in dropdown
3. Click "Start Server"
4. Wait for: "Server started on http://localhost:1234"

### Step 6: Add to .env

```bash
# No API key needed - just point to local server
LLM_PROVIDER=lmstudio
LM_STUDIO_BASE_URL=http://localhost:1234/v1
LM_STUDIO_API_KEY=lm-studio
LM_STUDIO_MODEL=auto
LM_STUDIO_AUTO_DETECT=true
```

### Step 7: Verify

```bash
# Test connection
curl http://localhost:1234/v1/models

# Should return JSON with available models
```

### Usage Notes

- **Models:** 7B (small), 13B (medium), 70B (large, requires lots of RAM)
- **Speed:** Depends on GPU
  - With GPU: Fast (5-10 seconds per response)
  - Without GPU (CPU): Slow (30-60 seconds)
- **Quality:** Good for most purposes

### Troubleshooting

**Issue:** "Cannot connect to http://localhost:1234"

**Solution:**

```bash
# 1. Check LM Studio is running
# 2. Check port is correct (default 1234)
# 3. Test connection:
curl http://localhost:1234/v1/models

# 4. If error, restart LM Studio
# 5. Check firewall isn't blocking port 1234
```

**Issue:** Model downloads very slowly

**Solution:**

- Download usually takes 5-30 minutes
- Check internet connection
- Try different model (some are smaller)
- Download in background while doing other work

**Issue:** "Out of memory" when running inference

**Solution:**

- You have insufficient RAM for the model
- Options:
  1. Load smaller model (7B instead of 13B)
  2. Add more RAM to computer
  3. Use cloud API (Gemini) instead

---

## Quick Verification Checklist

```bash
# Test all configured APIs
python << 'EOF'
import sys
from config.settings import get_settings

s = get_settings()
checks = {
    "LM Studio": s.LM_STUDIO_BASE_URL,
    "Gemini API": s.GEMINI_API_KEY,
    "Apify Token": s.APIFY_API_TOKEN,
    "Google Docs": s.GOOGLE_APPLICATION_CREDENTIALS,
    "ElevenLabs": s.ELEVENLABS_API_KEY,
}

print("\n=== API Configuration Check ===\n")
for name, value in checks.items():
    status = "✓" if value else "✗"
    print(f"{status} {name}")

print("\nAt minimum, configure:")
print("  - LM Studio (local, no key) OR")
print("  - Gemini API (cloud alternative)")
EOF
```

---

## Summary

**Minimum Setup (Free, Private):**

- ✅ LM Studio (5-20 min setup, no API key)
- ✅ Edge TTS (built-in, no setup)
- ✅ Pollinations.ai (free, no key)

**Full Setup (Cloud-Powered):**

- ✅ Gemini API (5 min, free tier)
- ✅ Apify Token (5 min, free tier)
- ✅ Google Docs (10 min, free)
- ✅ ElevenLabs (5 min, optional)

**Recommended:** Start with just LM Studio, add APIs as needed.

---

**Next:** See [SETUP.md](SETUP.md) or [USAGE.md](USAGE.md)
