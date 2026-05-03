# 📖 Usage Guide - Complete Command Reference

This guide explains how to use each agent and command with detailed examples.

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Agent Commands](#agent-commands)
3. [Full Pipeline](#full-pipeline)
4. [Advanced Usage](#advanced-usage)
5. [Output Files](#output-files)
6. [Examples](#examples)

---

## Quick Start

### Simplest Setup (Local Only, No API Keys)

```bash
# 1. Start LM Studio
# Open LM Studio app → Click "Local Server" → Start

# 2. Run one command
python agents.py render

# Done! Check: remotion-app/out/video.mp4
```

### What This Does

- Uses LM Studio (local, private, free)
- Generates test images with Pollinations.ai (free)
- Uses Edge TTS for audio (free)
- Renders a professional video

---

## Agent Commands

### 1. Researcher 🔍

**Purpose:** Scrape successful Meta ads for research

**Command:**

```bash
python agents.py researcher
```

**What it does:**

- Searches Meta ads using your configured search query
- Finds ads that are actively being promoted
- Extracts creative copy, images, and engagement metrics
- Saves to: `output/successful_ads.json`

**Configuration (.env):**

```env
APIFY_API_TOKEN=your_token_here
APIFY_META_ADS_ACTOR_ID=whoareyouanas/meta-ad-scraper
APIFY_META_ADS_SEARCH_QUERY=trading
APIFY_META_ADS_COUNTRY=US
APIFY_META_ADS_MAX_AGE_DAYS=30
```

**Output Example:**

```json
{
  "items": [
    {
      "ad_id": "123456",
      "headline": "Make Money Trading",
      "body": "Learn trading in 7 days...",
      "engagement": 45000,
      "image_url": "https://..."
    }
  ]
}
```

**Note:** Requires Apify API token (free tier available)

---

### 2. Strategist 📊

**Purpose:** Analyze ads and create marketing strategy

**Command:**

```bash
python agents.py strategist
```

**Dependencies:** Requires output from Researcher (`output/successful_ads.json`)

**What it does:**

- Analyzes top 10 ads
- Identifies common patterns and themes
- Extracts key messaging
- Creates strategic recommendations
- Saves to: `output/marketing_strategy.json`

**Output Example:**

```json
{
  "target_audience": "Beginner traders aged 25-45",
  "key_messages": [
    "Quick learn to trade",
    "Proven success stories",
    "Limited time offer"
  ],
  "recommended_tone": "Energetic, trustworthy",
  "design_suggestions": "Bright colors, dynamic transitions"
}
```

**LLM Used:** Local LM Studio or Gemini API

---

### 3. Copywriter ✍️

**Purpose:** Generate video script from strategy

**Command:**

```bash
python agents.py copywriter
```

**Dependencies:** Requires output from Strategist (`output/marketing_strategy.json`)

**What it does:**

- Creates 4-6 scene video script
- Generates compelling narration for each scene
- Creates prompts for image generation
- Validates script structure
- Saves to: `output/script.json`

**Options:**

```bash
# Custom strategy file
python agents.py copywriter --strategy custom_strategy.json

# Custom output
python agents.py copywriter --script custom_script.json

# Custom duration (default: 60 seconds)
python agents.py copywriter --duration 30
```

**Output Example:**

```json
{
  "scenes": [
    {
      "scene": 1,
      "narration": "Are you ready to transform your financial future?",
      "image_prompt": "Professional trader at computer with charts"
    },
    {
      "scene": 2,
      "narration": "Our proven method helps beginners earn consistent income",
      "image_prompt": "Success metrics and growth charts"
    }
  ]
}
```

**Script Duration Calculation:**

- Typical speaking rate: 150 words/minute
- Scene with 30 words ≈ 12 seconds narration
- Plus visual time = 15-20 second scene

---

### 4. Director 🎬

**Purpose:** Generate video assets (images and audio)

**Command:**

```bash
python agents.py director
```

**Dependencies:** Requires script (`output/script.json`)

**What it does:**

- Generates images for each scene
- Synthesizes narration audio
- Creates props file for Remotion
- Saves files to: `output/assets/` and `output/remotion_props.json`

**Options:**

```bash
# Custom script
python agents.py director --script custom_script.json

# Custom assets directory
python agents.py director --assets-dir my_assets/

# Custom props output
python agents.py director --props custom_props.json
```

**Output Files:**

```
output/assets/
├── images/
│   ├── scene_1.png
│   ├── scene_2.png
│   └── ...
├── audio/
│   ├── scene_1.mp3
│   ├── scene_2.mp3
│   └── ...

output/remotion_props.json  (Ready for Remotion)
```

**Processing Steps:**

1. **Image Generation** (Gemini or Pollinations.ai)
   - Takes prompt from script
   - Generates 1080x1920 images
   - Saves as PNG

2. **Audio Synthesis** (Edge TTS or ElevenLabs)
   - Takes narration text
   - Generates natural speech
   - Saves as MP3 (48 kHz, stereo)

**Time Estimate:**

- Per scene: 10-30 seconds
- 6 scenes: 1-3 minutes total
- Depends on API response times

---

### 5. Designer 🎨

**Purpose:** Create visual design specifications

**Command:**

```bash
python agents.py designer
```

**Dependencies:** Requires script (`output/script.json`)

**What it does:**

- Analyzes script content
- Creates design specification with:
  - Color palette (bg, accent, text, secondary)
  - Layout (fullscreen, split, picture-in-picture, minimal)
  - Animation style (subtle, dynamic, bold)
  - Element customization
- Saves to: `output/video_design.json`

**Options:**

```bash
# Custom script
python agents.py designer --script custom_script.json

# Custom design output
python agents.py designer --design custom_design.json

# Custom Remotion code output (optional)
python agents.py designer --video-code src/CustomVideo.tsx
```

**Output Example:**

```json
{
  "design": {
    "bg_color": "#0f172a",
    "accent_color": "#3b82f6",
    "text_color": "#f8fafc",
    "secondary_color": "#1e293b",
    "layout": "fullscreen",
    "animation_style": "dynamic",
    "floating_elements": true,
    "show_badge": true,
    "text_position": "bottom",
    "element_scale": 1.2,
    "blur_strength": 8,
    "audio_gain": 1.4
  }
}
```

**Design Presets Used:**

- Tech Startup → Blue/purple, dynamic
- Lifestyle → Warm colors, bold
- Corporate → Neutral, minimal
- Fitness → Bright accents, energetic
- And 6 more...

See [TEMPLATE_GUIDE.md](TEMPLATE_GUIDE.md) for full customization.

---

### 6. Render 🎥

**Purpose:** Generate final MP4 video

**Command:**

```bash
python agents.py render
```

**Dependencies:** Requires props file (`output/remotion_props.json`)

**What it does:**

- Runs Remotion composition
- Generates video frames at 30 FPS
- Applies design styling
- Encodes to H.264 MP4
- Saves to: `remotion-app/out/video.mp4`

**Options:**

```bash
# Custom props file
python agents.py render --props output/custom_props.json

# Custom design (optional override)
python agents.py render --design output/custom_design.json

# Custom output path
python agents.py render --output my_video.mp4

# Custom Remotion app directory
python agents.py render --remotion-app /path/to/remotion-app

# Custom composition (if you have multiple)
python agents.py render --composition VideoEnhanced
```

**Rendering Process:**

1. **Preparation** - Copy assets to Remotion public folder (5 sec)
2. **Bundling** - Build React components (15-30 sec)
3. **Rendering** - Generate frames at 30 FPS (depends on duration)
   - 20 second video: ~30 seconds
   - 60 second video: ~2 minutes
4. **Encoding** - Compress to H.264 MP4 (30-60 sec)

**Total Time:** 2-5 minutes per video

**Output:**

```
remotion-app/out/video.mp4
Size: 1-5 MB
Duration: 20-60 seconds
Resolution: 1080x1920 (9:16)
Codec: H.264
```

---

## Full Pipeline

### Option 1: Complete Automated Pipeline

```bash
# One command does everything:
# 1. Research (scrape ads)
# 2. Strategy (analyze)
# 3. Copywrite (write script)
# 4. Direct (generate assets)
# 5. Design (create specs)
# 6. Render (make video)

python agents.py all --render
```

**Time Required:** 5-15 minutes (depending on API speeds)

**Output:** `remotion-app/out/video.mp4`

### Option 2: Pipeline Without Rendering

```bash
# Generate all assets but don't render
python agents.py all

# Later, render when ready
python agents.py render
```

### Option 3: Custom Pipeline

```bash
# Run specific commands in sequence
python agents.py researcher
python agents.py strategist
python agents.py copywriter
python agents.py director
python agents.py designer
python agents.py render
```

**Advantage:** Can modify files between steps

### Option 4: Skip to Rendering

```bash
# If you already have a script, skip ahead
python agents.py director
python agents.py render
```

---

## Advanced Usage

### Custom Script (No LLM Generation)

```bash
# Create output/script.json manually:
{
  "scenes": [
    {
      "scene": 1,
      "narration": "Your text here",
      "image_prompt": "Image description"
    }
  ]
}

# Then generate assets
python agents.py director
python agents.py render
```

### Custom Design (Override Auto-Generated)

```bash
# Create output/video_design.json:
{
  "design": {
    "bg_color": "#ff0000",
    "accent_color": "#00ff00",
    "animation_style": "bold"
    // ... other properties
  }
}

# Render with custom design
python agents.py render --design output/video_design.json
```

### Batch Processing Multiple Videos

```bash
# Process list of search queries
for query in "trading" "crypto" "forex"; do
  APIFY_META_ADS_SEARCH_QUERY=$query python agents.py all --render
  mv remotion-app/out/video.mp4 output/${query}_video.mp4
done
```

### Different Video Dimensions

```bash
# Modify .env:
VIDEO_WIDTH=1920
VIDEO_HEIGHT=1080
VIDEO_ASPECT_RATIO=16:9

# Then regenerate
python agents.py director
python agents.py render
```

---

## Output Files

### Directory Structure

```
output/
├── successful_ads.json           # Scraped ads (Researcher)
├── marketing_strategy.json       # Strategy analysis (Strategist)
├── script.json                   # Video script (Copywriter)
├── video_design.json             # Design specs (Designer)
├── remotion_props.json           # Normalized props (Director)
├── run.log                       # Execution log
└── assets/
    ├── images/
    │   ├── scene_1.png
    │   ├── scene_2.png
    │   └── ...
    └── audio/
        ├── scene_1.mp3
        ├── scene_2.mp3
        └── ...

remotion-app/
└── out/
    └── video.mp4                 # FINAL VIDEO
```

### File Purposes

| File                      | Size          | Purpose                |
| ------------------------- | ------------- | ---------------------- |
| `successful_ads.json`     | 50-500 KB     | Ad research data       |
| `marketing_strategy.json` | 5-20 KB       | Strategic analysis     |
| `script.json`             | 2-5 KB        | Video script           |
| `video_design.json`       | 1-2 KB        | Design specs           |
| `remotion_props.json`     | 5-10 KB       | Remotion configuration |
| `scene_1.png`             | 500 KB - 1 MB | Generated image        |
| `scene_1.mp3`             | 200-500 KB    | Narration audio        |
| `video.mp4`               | 1-5 MB        | **Final video**        |

---

## Examples

### Example 1: Trading Video (Complete)

```bash
# 1. Set search query
export APIFY_META_ADS_SEARCH_QUERY="forex trading"

# 2. Run full pipeline
python agents.py all --render

# 3. Find video
ls -lh remotion-app/out/video.mp4
# Output: 2.3 MB 60 second video
```

### Example 2: Fitness Video (With Custom Design)

```bash
# 1. Generate script first
python agents.py copywriter

# 2. Create custom design
cat > output/video_design.json << 'EOF'
{
  "design": {
    "bg_color": "#1a1a2e",
    "accent_color": "#ff6b6b",
    "text_color": "#ffffff",
    "animation_style": "dynamic",
    "element_scale": 1.5
  }
}
EOF

# 3. Generate assets
python agents.py director

# 4. Render with custom design
python agents.py render --design output/video_design.json
```

### Example 3: Local-Only (No Internet, No APIs)

```bash
# 1. Ensure LM Studio is running locally

# 2. Use only local generation
python agents.py copywriter    # Uses LM Studio
python agents.py director      # Uses Pollinations.ai (no auth)
python agents.py render        # Uses Remotion (local)

# Video generated entirely without cloud APIs!
```

### Example 4: Manual Script Creation

```bash
# 1. Create your own script
cat > output/script.json << 'EOF'
{
  "scenes": [
    {
      "scene": 1,
      "narration": "Welcome to success",
      "image_prompt": "Beautiful sunrise over mountains"
    },
    {
      "scene": 2,
      "narration": "Your journey starts now",
      "image_prompt": "Person running on beach"
    }
  ]
}
EOF

# 2. Generate assets
python agents.py director

# 3. Render
python agents.py render
```

### Example 5: Different Aspect Ratio

```bash
# Update .env
echo "VIDEO_WIDTH=1920" >> .env
echo "VIDEO_HEIGHT=1080" >> .env
echo "VIDEO_ASPECT_RATIO=16:9" >> .env

# Regenerate
python agents.py director
python agents.py render

# Check output
ffprobe remotion-app/out/video.mp4 | grep "Video:"
# Should show: 1920x1080
```

---

## Troubleshooting Usage

### Video is blank/black

```bash
# Issue: Assets not generated
# Solution:
python agents.py director
python agents.py render
```

### Script validation failed

```bash
# Issue: Script JSON format invalid
# Check output/script.json has correct structure:
{
  "scenes": [
    {
      "scene": 1,
      "narration": "text",
      "image_prompt": "text"
    }
  ]
}
```

### Render times out

```bash
# Issue: Remotion taking too long
# Try shorter video:
python agents.py copywriter --duration 30
python agents.py director
python agents.py render
```

### Audio missing in video

```bash
# Issue: MP3 files corrupt
# Regenerate:
rm -rf output/assets/audio/
python agents.py director
python agents.py render
```

---

## Next Steps

- **Customize Design:** See [TEMPLATE_GUIDE.md](TEMPLATE_GUIDE.md)
- **All Options:** See [CONFIGURATION.md](CONFIGURATION.md)
- **API Setup:** See [API_KEYS.md](API_KEYS.md)
- **Project Structure:** See [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)

---

**Ready to create videos! Start with:** `python agents.py render`
