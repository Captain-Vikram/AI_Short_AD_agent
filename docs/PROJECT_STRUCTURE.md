# Project Structure

```
internship-agent-dev/
├── src/                          # Main source code
│   ├── __init__.py
│   ├── core/                     # Core pipeline components
│   │   ├── __init__.py
│   │   ├── director.py           # Asset assembly & props generation
│   │   ├── remotion_render.py    # Video rendering bridge
│   │   └── script_validator.py   # Scene schema validation
│   ├── media/                    # Media generation modules
│   │   ├── __init__.py
│   │   ├── gemini_image.py       # Image generation (Gemini + Pollinations.ai)
│   │   ├── tts.py                # Audio synthesis (Edge TTS + ElevenLabs)
│   │   ├── apify_helper.py       # Meta Ads scraping
│   │   └── gdrive_helper.py      # Google Drive text extraction
│   └── utils/                    # Shared utilities
│       ├── __init__.py
│       ├── logger.py             # Rich logging + file output
│       └── retry.py              # Exponential backoff retry logic
├── config/                       # Configuration & credentials
│   ├── __init__.py
│   ├── settings.py               # Pydantic settings & environment config
│   ├── cred.json                 # Service account credentials
│   ├── design_system_examples.json  # Design presets
│   ├── *.json                    # Generated output configs
├── output/                       # Generated outputs
│   ├── assets/
│   │   ├── images/               # Generated scene images
│   │   └── audio/                # Generated narration audio
│   ├── run.log                   # Execution logs
│   └── *.json                    # Scripts, props, reports
├── docs/                         # Documentation
│   ├── README.md
│   └── TEMPLATE_GUIDE.md
├── remotion-app/                 # React/TypeScript video renderer
│   ├── src/
│   │   ├── index.tsx
│   │   ├── Root.tsx              # Composition registry
│   │   ├── Video.tsx             # Main template (enhanced)
│   │   ├── VideoEnhanced.tsx     # Professional infographic template
│   │   ├── VideoGenerated.tsx    # LLM-generated compositions
│   │   └── types.ts              # TypeScript interfaces
│   ├── public/assets/            # Copied assets for rendering
│   ├── package.json
│   └── tsconfig.json
├── scripts/                      # Utility scripts
│   ├── generate_example.py       # Offline smoke test
│   └── ...
├── agents.py                     # CLI & agent orchestration
├── requirements.txt              # Python dependencies
├── .env & .env.example          # Environment variables
├── .gitignore
├── .venv/                        # Virtual environment
└── __pycache__/
```

## Module Organization

### `src/core/`

**Pipeline orchestration and rendering**

- `director.py`: Generates images, synthesizes audio, builds remotion_props.json
- `remotion_render.py`: Bridge to Remotion CLI, asset copying, render invocation
- `script_validator.py`: Scene schema validation, JSON serialization

### `src/media/`

**Media generation providers**

- `gemini_image.py`: Gemini image API + Pollinations.ai FLUX fallback
- `tts.py`: Edge TTS (default) + ElevenLabs (fallback)
- `apify_helper.py`: Meta Ads scraper via Apify platform
- `gdrive_helper.py`: Google Drive document text extraction

### `src/utils/`

**Shared infrastructure**

- `logger.py`: Rich console logging + file output to `output/run.log`
- `retry.py`: Exponential backoff decorator with jitter

### `config/`

**Settings and credentials**

- `settings.py`: Pydantic BaseSettings with .env support
- `cred.json`: Service account credentials
- `*.json`: Generated configuration files (moved from root)

### `output/`

**Generated files and logs**

- `assets/images/`: Scene images (from Gemini/Pollinations)
- `assets/audio/`: Scene audio (MP3 files)
- `run.log`: Execution logs with Rich formatting
- `*.json`: Scripts, props, reports (remotion_props.json, asset_report.json, etc.)

## Top-Level Files

- `agents.py` - Main CLI entry point with agent orchestration
- `requirements.txt` - Python package dependencies
- `.env` / `.env.example` - Environment configuration
- `.gitignore` - Git exclusions

## Execution Flow

```
agents.py (CLI)
  ├─ Researcher → apify_helper → successful_ads.json
  ├─ Strategist → LLM analysis → marketing_strategy.json
  ├─ Copywriter → script generation → script.json
  ├─ Director → director.py
  │   ├─ generate_image(gemini_image.py)
  │   ├─ synthesize(tts.py)
  │   └─ build_remotion_props() → output/remotion_props.json
  ├─ Designer → LLM design spec → output/video_design.json
  └─ Render → remotion_render.py
      └─ npx remotion render → output/remotion-app/out/video.mp4
```

## Key Improvements

✅ **Modular organization** - Clear separation of concerns by layer  
✅ **Consistent imports** - All relative imports use `src.` or `config.` prefixes  
✅ **Output organization** - Generated files in `/output` for cleanliness  
✅ **Configuration isolated** - All credentials and configs in `/config`  
✅ **Documentation co-located** - Guides in `/docs`  
✅ **Media providers abstracted** - Easy to add new image/audio/data sources  
✅ **Core pipeline centralized** - Director, validator, renderer in `/src/core`  
✅ **Shared utils extracted** - Logging, retry logic in `/src/utils`
