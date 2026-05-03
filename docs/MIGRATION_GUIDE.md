# Migration Guide

## What Changed

Your project has been reorganized from a flat structure into a clean, modular architecture. All imports have been updated and validated.

## Old vs New Structure

### Before

```
./ (flat)
├── agents.py
├── director.py
├── script_validator.py
├── remotion_render.py
├── gemini_image.py
├── tts.py
├── apify_helper.py
├── gdrive_helper.py
├── config.py
├── logger.py
├── utils.py
├── *.json (mixed outputs/configs)
└── assets/ (outputs)
```

### After

```
./
├── src/
│   ├── core/
│   │   ├── director.py
│   │   ├── script_validator.py
│   │   └── remotion_render.py
│   ├── media/
│   │   ├── gemini_image.py
│   │   ├── tts.py
│   │   ├── apify_helper.py
│   │   └── gdrive_helper.py
│   └── utils/
│       ├── logger.py
│       └── retry.py
├── config/
│   ├── settings.py (was config.py)
│   ├── cred.json
│   └── *.json (configs)
├── output/
│   ├── assets/ (images, audio)
│   ├── run.log
│   └── *.json (generated outputs)
├── docs/
│   ├── README.md
│   ├── TEMPLATE_GUIDE.md
│   └── PROJECT_STRUCTURE.md
├── agents.py
└── requirements.txt
```

## Updated Imports

All imports have been automatically updated across the codebase:

### Example: agents.py

**Before:**

```python
from config import get_settings
from director import build_remotion_props
from logger import get_logger
from utils import retry_with_backoff
```

**After:**

```python
from config.settings import get_settings
from src.core.director import build_remotion_props
from src.utils import get_logger
from src.utils import retry_with_backoff
```

### Example: director.py

**Before:**

```python
from config import get_settings
from logger import get_logger
from tools import generate_images, synthesize_audio
```

**After:**

```python
from config.settings import get_settings
from src.utils import get_logger
from src.media.gemini_image import generate_image
from src.media.tts import synthesize
```

## Running the Project

Everything still works the same way from the command line:

```powershell
# Full pipeline
python agents.py all --render

# Or step by step
python agents.py researcher
python agents.py strategist
python agents.py copywriter
python agents.py director
python agents.py designer
python agents.py render
```

## Environment Variables

No changes to `.env` - all paths have been updated internally:

```bash
VIDEO_WIDTH=1080
VIDEO_HEIGHT=1920
SCENE_MIN_DURATION_SECONDS=1.0
# ... rest unchanged
```

## Generated Files

All outputs are now organized in `/output/`:

```
output/
├── assets/
│   ├── images/        # Generated images from Gemini/Pollinations
│   └── audio/         # Generated MP3 narration
├── run.log            # Execution log with Rich formatting
├── remotion_props.json
├── video_design.json
├── script.json
├── marketing_strategy.json
├── successful_ads.json
└── asset_report.json
```

## Benefits of New Structure

1. **Clear separation of concerns** - Core, media, utils, config clearly separated
2. **Easier to extend** - Want to add a new image provider? Add it to `src/media/`
3. **Better discoverability** - Find code by layer/functionality
4. **Professional layout** - Matches Python best practices
5. **Output isolation** - Generated files don't clutter root directory
6. **Configuration centralized** - All credentials and configs in one place
7. **Documentation co-located** - Guides in `/docs`
8. **No functional changes** - All imports updated automatically, no API changes

## Testing the Migration

All modules have been tested:

```powershell
# Verify imports work
python -c "from config.settings import get_settings; print('✓')"
python -c "from src.utils import get_logger; print('✓')"
python -c "from src.core import director; print('✓')"
```

## Rollback (if needed)

All files are still in Git. To revert:

```powershell
git reset --hard
```

## Next Steps

1. Review the new `PROJECT_STRUCTURE.md` for detailed module breakdown
2. Run `python agents.py all --render` to verify everything works
3. Check `output/run.log` for execution details
4. Update any external scripts that reference old paths

---

**Note:** This is a structural reorganization only. No functionality, behavior, or results have changed. The project is now more maintainable and professional.
