# 🎬 Internship Agent Dev - AI-Powered Marketing Video Generator

> **Automated video creation tool that generates professional marketing videos using AI agents, LLMs, and advanced infographics.**

## 📋 Overview

This tool automates the creation of professional marketing videos by:

1. **Researching** successful ads using Apify (Meta Ads scraping)
2. **Strategizing** marketing approaches with AI analysis
3. **Writing** compelling video scripts with LLM
4. **Creating** visually stunning designs with design specs
5. **Directing** asset generation (images & audio)
6. **Rendering** professional 9:16 vertical videos with Remotion

The entire pipeline runs as AI agents that work together to produce publication-ready videos in minutes.

### ⚡ Key Features

- ✅ **Fully Automated** - One command generates complete videos
- ✅ **Local-First** - Works with local LLMs (LM Studio) for privacy
- ✅ **Professional Templates** - VideoEnhanced with floating animations
- ✅ **Dynamic Design** - 10+ design presets and full customization
- ✅ **Multi-Modal AI** - Text, image, and audio generation
- ✅ **Vertical Format** - Optimized for social media (1080x1920, 9:16)
- ✅ **Cloud Fallbacks** - Seamless fallback to cloud APIs when needed

---

## 🚀 Quick Start (5 minutes)

### 1. Prerequisites

- **Python 3.13+** with venv
- **Node.js 18+** (for Remotion)
- **Git**

### 2. Clone & Setup

```bash
# Clone/navigate to project
cd Intership\ agent\ dev

# Create virtual environment
python -m venv .venv

# Activate
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Setup Remotion
cd remotion-app
npm install
cd ..
```

### 3. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your settings (see Configuration section)
```

### 4. Run Your First Video

```bash
# Generate a test video without external APIs
python agents.py render

# Or run the full pipeline
python agents.py all
```

### 5. Find Your Output

Video: `remotion-app/out/video.mp4` ✅

---

## 📁 Project Structure

```
internship-agent-dev/
├── README.md                      # This file
├── requirements.txt               # Python dependencies
├── .env.example                   # Environment template (copy to .env)
├── agents.py                      # CLI entry point & agent orchestration
│
├── config/
│   └── settings.py               # Pydantic configuration
│
├── src/
│   ├── core/
│   │   ├── director.py           # Asset generation orchestrator
│   │   ├── remotion_render.py    # Remotion CLI bridge
│   │   └── script_validator.py   # Scene schema validation
│   │
│   ├── media/
│   │   ├── gemini_image.py       # Image generation (Gemini API)
│   │   ├── tts.py                # Audio synthesis (Edge TTS, ElevenLabs)
│   │   ├── gdrive_helper.py      # Google Docs text extraction
│   │   └── apify_helper.py       # Meta Ads scraping
│   │
│   └── utils/
│       ├── logger.py             # Rich logging + file output
│       └── retry.py              # Exponential backoff retry logic
│
├── remotion-app/                 # React/TypeScript video composition
│   ├── src/
│   │   ├── VideoEnhanced.tsx     # Professional infographic template
│   │   ├── types.ts              # TypeScript type definitions
│   │   ├── Root.tsx              # Composition wrapper
│   │   └── index.tsx             # Entry point
│   ├── package.json
│   └── public/
│       └── assets/               # Generated images & audio
│
├── output/                        # Generated files
│   ├── assets/                   # Images and audio
│   ├── script.json               # Validated video script
│   ├── video_design.json         # Design specifications
│   ├── remotion_props.json       # Normalized props for Remotion
│   └── run.log                   # Execution log
│
└── docs/                         # Detailed documentation
    ├── SETUP.md                  # Installation & environment setup
    ├── USAGE.md                  # How to use each agent
    ├── CONFIGURATION.md          # Detailed config reference
    └── API_KEYS.md               # How to get API keys
```

---

## 🎯 Usage

### Command Structure

```bash
python agents.py <command> [--options]
```

### Available Commands

#### 1. **Researcher** - Scrape Successful Ads

```bash
python agents.py researcher
# Output: output/successful_ads.json
# Scrapes Meta ads matching your search query
```

#### 2. **Strategist** - Analyze & Create Strategy

```bash
python agents.py strategist
# Input: output/successful_ads.json
# Output: output/marketing_strategy.json
# Analyzes top ads and creates strategy
```

#### 3. **Copywriter** - Generate Video Script

```bash
python agents.py copywriter
# Input: output/marketing_strategy.json
# Output: output/script.json
# Creates 4-6 scene script with narration
```

#### 4. **Director** - Generate Assets

```bash
python agents.py director
# Input: output/script.json
# Output: output/remotion_props.json
# Generates images and audio for each scene
```

#### 5. **Designer** - Create Visual Design

```bash
python agents.py designer
# Input: output/script.json
# Output: output/video_design.json
# Creates design specification (colors, animations, layout)
```

#### 6. **Render** - Generate Video

```bash
python agents.py render
# Input: output/remotion_props.json
# Output: remotion-app/out/video.mp4
# Renders final video using Remotion
```

### Run Full Pipeline

```bash
# Complete pipeline: Research → Strategy → Script → Assets → Render
python agents.py all --render

# Just render without options
python agents.py all
# (Render with: python agents.py render)
```

### Advanced Options

```bash
# Custom script path
python agents.py director --script custom_script.json

# Custom output paths
python agents.py render --props output/custom_props.json --output video_output.mp4

# Custom assets directory
python agents.py director --assets-dir my_assets

# Specify design file
python agents.py render --design output/custom_design.json
```

---

## ⚙️ Configuration

### Environment Variables

See `.env.example` for all options. Key settings:

**Video Settings:**

```env
VIDEO_WIDTH=1080
VIDEO_HEIGHT=1920
VIDEO_ASPECT_RATIO=9:16
```

**LM Studio (Local LLM - Recommended):**

```env
LLM_PROVIDER=lmstudio
LM_STUDIO_BASE_URL=http://localhost:1234/v1
LM_STUDIO_API_KEY=lm-studio
LM_STUDIO_MODEL=auto
```

**Gemini API (Fallback):**

```env
GEMINI_API_KEY=your_key_here
GEMINI_TEXT_MODEL=gemini-2.5-flash
```

**TTS (Edge TTS - Free):**

```env
TTS_PROVIDER=edge-tts
EDGE_TTS_VOICE=en-US-AriaNeural
```

**Apify (Meta Ads Scraping):**

```env
APIFY_API_TOKEN=your_token_here
APIFY_META_ADS_ACTOR_ID=whoareyouanas/meta-ad-scraper
```

### Configuration Priority

1. **Environment variables** (`.env`)
2. **Environment file** if set
3. **Pydantic defaults** in `config/settings.py`

---

## 🔧 Setup Guides

### Option A: Local-Only (Recommended - No API Keys)

**Best for:** Privacy-focused, testing, local development

```bash
# 1. Download LM Studio
# Visit: https://lmstudio.ai
# Download & install

# 2. Start LM Studio
# Open LM Studio → Load a model (Mistral 7B, Llama 2)
# Start local server (default: http://localhost:1234)

# 3. Update .env
LLM_PROVIDER=lmstudio
LM_STUDIO_BASE_URL=http://localhost:1234/v1

# 4. Run
python agents.py all --render
```

**Note:** Image generation will use free Pollinations.ai, audio uses Edge TTS (both free)

### Option B: Cloud APIs (Full Features)

**Best for:** Production, advanced features, higher quality

See [docs/API_KEYS.md](docs/API_KEYS.md) for:

- Getting Gemini API key (image/text)
- Getting Apify token (ad scraping)
- Setting up Google Docs integration
- ElevenLabs setup (premium voices)

### Option C: Hybrid (Recommended)

Use local LM Studio + cloud Gemini (cheapest):

```env
# Local LLM
LLM_PROVIDER=lmstudio
LM_STUDIO_BASE_URL=http://localhost:1234/v1

# Cloud image generation
GEMINI_API_KEY=your_key_here

# Free TTS & scraping (Pollinations + Edge TTS)
```

---

## 📊 Design System

### 10 Built-in Presets

Videos come with professional design presets:

- **Tech Startup Modern** - Blues, gradients, dynamic animations
- **Lifestyle Vibrant** - Warm colors, bold transitions
- **Corporate Professional** - Neutral tones, minimal design
- **Fitness Energetic** - Bright accents, dynamic elements
- **Educational Calm** - Soft colors, centered layout
- **Luxury Minimal** - Dark backgrounds, elegant typography
- **Gaming Intense** - Bold colors, rapid animations
- **E-commerce Sale** - Urgency-driven, bright accents
- **Nonprofit Inclusive** - Accessible colors, clear messaging
- **Minimal Split** - Two-column layout, clean design

### Custom Designs

Create custom `video_design.json`:

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

See [docs/TEMPLATE_GUIDE.md](docs/TEMPLATE_GUIDE.md) for full design customization.

---

## 📚 Documentation

- **[SETUP.md](docs/SETUP.md)** - Detailed installation & environment setup
- **[USAGE.md](docs/USAGE.md)** - How to use each agent command
- **[CONFIGURATION.md](docs/CONFIGURATION.md)** - All configuration options explained
- **[API_KEYS.md](docs/API_KEYS.md)** - Getting API credentials
- **[TEMPLATE_GUIDE.md](docs/TEMPLATE_GUIDE.md)** - Video template customization
- **[PROJECT_STRUCTURE.md](docs/PROJECT_STRUCTURE.md)** - Codebase overview

---

## 🐛 Troubleshooting

### Issue: "ImportError: No module named 'lmstudio'"

**Solution:** LM Studio not installed or not running on `localhost:1234`

```bash
# Download LM Studio: https://lmstudio.ai
# Start the server in LM Studio app
# Check: http://localhost:1234/v1/models (should return list)
```

### Issue: "Gemini API rate limit (429)"

**Solution:** Too many requests. Either:

- Wait a few minutes before retrying
- Switch to local LM Studio
- Upgrade Gemini API plan

### Issue: "Video renders with black images"

**Solution:** Assets not copied to Remotion public folder

```bash
# The director command automatically copies assets
python agents.py director

# Check: remotion-app/public/assets/images/ (should have images)
```

### Issue: "ffprobe failed on MP3"

**Solution:** Audio files corrupt or invalid format

```bash
# Delete audio folder and regenerate
rm -r output/assets/audio/
python agents.py director
```

See [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) for more issues.

---

## 📈 Output Files

### Generated During Pipeline

| File                             | Purpose                       | Created By |
| -------------------------------- | ----------------------------- | ---------- |
| `output/successful_ads.json`     | Scraped ads data              | Researcher |
| `output/marketing_strategy.json` | Strategy analysis             | Strategist |
| `output/script.json`             | Video script (4-6 scenes)     | Copywriter |
| `output/video_design.json`       | Visual design specs           | Designer   |
| `output/remotion_props.json`     | Normalized props for Remotion | Director   |
| `output/assets/images/*.png`     | Generated scene images        | Director   |
| `output/assets/audio/*.mp3`      | Generated narration audio     | Director   |
| `output/run.log`                 | Full execution log            | Logger     |
| `remotion-app/out/video.mp4`     | **Final rendered video**      | Remotion   |

---

## 🔐 Security & Privacy

- **Local-first:** Use LM Studio for zero external data leakage
- **API keys:** Stored in `.env` (gitignored by default)
- **No tracking:** Self-hosted infrastructure
- **Data control:** All generated files on your machine

---

## 📦 Dependencies

**Python:** See `requirements.txt`

- `pydantic` - Configuration validation
- `httpx` - Async HTTP client
- `Pillow` - Image processing
- `edge-tts` - Text-to-speech
- `mutagen` - Audio metadata

**Node.js:** See `remotion-app/package.json`

- `remotion` - Video composition
- `react` - UI framework
- `typescript` - Type safety

---

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/improvement`)
3. Commit changes (`git commit -m 'Add improvement'`)
4. Push to branch (`git push origin feature/improvement`)
5. Open Pull Request

---

## 📄 License

MIT License - See LICENSE file for details

---

## 🆘 Support

- **Documentation:** See `/docs` folder
- **Issues:** Check troubleshooting section
- **Questions:** Review `.env.example` for all options

---

## 🎓 Learning Resources

- [Remotion Docs](https://www.remotion.dev/)
- [Pydantic Docs](https://docs.pydantic.dev/)
- [LM Studio Guide](https://lmstudio.ai/docs)
- [Gemini API Docs](https://ai.google.dev/)
- [Apify Docs](https://apify.com/docs)

---

**Created with ❤️ for AI-powered content creation**
