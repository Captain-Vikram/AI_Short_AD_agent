# 📚 Documentation Index

Complete guide to all documentation files. Start here to find what you need.

---

## 🚀 Quick Navigation

| Need                        | Go To                                        | Time     |
| --------------------------- | -------------------------------------------- | -------- |
| **First time setup?**       | [SETUP.md](SETUP.md)                         | 15 min   |
| **How to use commands?**    | [USAGE.md](USAGE.md)                         | 10 min   |
| **Environment variables?**  | [CONFIGURATION.md](CONFIGURATION.md)         | 5 min    |
| **Get API keys?**           | [API_KEYS.md](API_KEYS.md)                   | 5-20 min |
| **Customize video design?** | [TEMPLATE_GUIDE.md](TEMPLATE_GUIDE.md)       | 10 min   |
| **Understand structure?**   | [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) | 5 min    |
| **See recent changes?**     | [CHANGELOG.md](CHANGELOG.md)                 | 5 min    |

---

## 📖 All Documentation

### 1. [README.md](../README.md) - Project Overview

**What's in it:**

- Project overview and features
- Quick 5-minute start guide
- Available commands
- Design system overview
- Troubleshooting basics

**Start here if:** You're new to the project

---

### 2. [SETUP.md](SETUP.md) - Installation & Environment

**What's in it:**

- System requirements
- Step-by-step installation
- Virtual environment setup
- LM Studio installation and setup
- Complete environment configuration guide
- Verification tests
- Installation troubleshooting

**Start here if:** Installing for the first time or having setup issues

**Topics covered:**

- Python 3.13+ installation
- Node.js installation
- Virtual environment creation
- Dependency installation
- LM Studio download and setup
- Configuration file creation

---

### 3. [USAGE.md](USAGE.md) - How to Use Commands

**What's in it:**

- Command reference for all agents
- Detailed explanation of each command
- Full pipeline instructions
- Advanced usage examples
- Custom script creation
- Batch processing examples
- Complete real-world examples

**Start here if:** You want to know how to use the tool

**Commands explained:**

- `researcher` - Scrape ads
- `strategist` - Analyze ads
- `copywriter` - Write script
- `director` - Generate assets
- `designer` - Create design
- `render` - Generate video
- `all` - Full pipeline

---

### 4. [CONFIGURATION.md](CONFIGURATION.md) - All Settings Explained

**What's in it:**

- Complete reference for all environment variables
- Default values and ranges
- Detailed descriptions with examples
- Configuration precedence
- Validation information

**Start here if:** You need to understand all configuration options

**Sections:**

- Video settings (width, height, aspect ratios)
- LLM configuration (LM Studio, Gemini)
- API keys setup
- Media generation (TTS, images)
- Google Drive integration
- Logging and output
- Remotion settings
- Advanced options

---

### 5. [API_KEYS.md](API_KEYS.md) - How to Get Credentials

**What's in it:**

- Step-by-step guides for each service
- Where to sign up
- How to find/generate keys
- How to add keys to .env
- Verification steps
- Troubleshooting API issues

**Start here if:** You need to get API credentials

**Services covered:**

- Gemini API (Google) - text and images
- Apify Token - ad scraping
- Google Drive/Docs - source material
- ElevenLabs - premium voices
- LM Studio - local LLM (free, no key)

---

### 6. [TEMPLATE_GUIDE.md](TEMPLATE_GUIDE.md) - Video Design Customization

**What's in it:**

- How the video template works
- Design system explanation
- 10 built-in design presets
- How to create custom designs
- Color guidelines
- Layout options
- Animation styles
- Detailed customization examples
- Performance considerations

**Start here if:** You want to customize video appearance

**Topics:**

- Component architecture
- Floating element animations
- Design properties (colors, layouts, animations)
- Creating presets
- Extending templates

---

### 7. [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) - Codebase Organization

**What's in it:**

- Complete directory tree
- Module descriptions
- Code flow explanation
- File purposes
- Improvement notes

**Start here if:** You want to understand the codebase

---

## 🎯 Common Scenarios

### Scenario 1: "I'm starting from scratch"

1. **Setup (15 min):**
   - Follow [SETUP.md](SETUP.md) from top to bottom
   - Install Python, Node.js, dependencies
   - Start LM Studio

2. **First run (5 min):**
   - Follow "Quick Start" in [README.md](../README.md)
   - Run: `python agents.py render`

3. **Learn commands (10 min):**
   - Read [USAGE.md](USAGE.md) sections 1-3

### Scenario 2: "I want to use cloud APIs"

1. **Get credentials (20 min):**
   - Follow [API_KEYS.md](API_KEYS.md)
   - Get Gemini API key
   - Get Apify token (optional)

2. **Configure (5 min):**
   - Update .env with API keys
   - See [CONFIGURATION.md](CONFIGURATION.md) for exact format

3. **Run (5 min):**
   - Follow full pipeline: `python agents.py all --render`

### Scenario 3: "Video quality doesn't look right"

1. **Check defaults:**
   - See [CONFIGURATION.md](CONFIGURATION.md) section on video settings

2. **Customize design:**
   - Follow [TEMPLATE_GUIDE.md](TEMPLATE_GUIDE.md)
   - Create custom design preset
   - Use: `python agents.py render --design output/custom_design.json`

### Scenario 4: "I'm getting errors"

1. **Installation errors:**
   - Check [SETUP.md](SETUP.md) troubleshooting section

2. **Configuration errors:**
   - See [CONFIGURATION.md](CONFIGURATION.md) validation

3. **API errors:**
   - See [API_KEYS.md](API_KEYS.md) troubleshooting sections

4. **General errors:**
   - Check logs: `tail -f output/run.log`
   - Increase log level: `LOG_LEVEL=DEBUG` in .env

### Scenario 5: "I want to run the full pipeline"

1. **Setup once:** Follow [SETUP.md](SETUP.md)

2. **Configure APIs:** Follow [API_KEYS.md](API_KEYS.md)

3. **Run pipeline:** `python agents.py all --render`

4. **Check output:** `remotion-app/out/video.mp4`

---

## 📚 Reading Path by Role

### For Developers

**Recommended order:**

1. [README.md](../README.md) - Overview
2. [SETUP.md](SETUP.md) - Installation
3. [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) - Codebase
4. [TEMPLATE_GUIDE.md](TEMPLATE_GUIDE.md) - Customization
5. [CONFIGURATION.md](CONFIGURATION.md) - All options

### For End Users

**Recommended order:**

1. [README.md](../README.md) - Quick start
2. [SETUP.md](SETUP.md) - Installation
3. [API_KEYS.md](API_KEYS.md) - Get credentials
4. [USAGE.md](USAGE.md) - Commands
5. [TEMPLATE_GUIDE.md](TEMPLATE_GUIDE.md) - Customize

### For DevOps/Deployment

**Recommended order:**

1. [SETUP.md](SETUP.md) - Installation
2. [CONFIGURATION.md](CONFIGURATION.md) - All settings
3. [API_KEYS.md](API_KEYS.md) - Credentials
4. [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) - Architecture

---

## 🔍 Find Topics by Subject

### Installation & Setup

- System requirements → [SETUP.md](SETUP.md#system-requirements)
- Virtual environment → [SETUP.md](SETUP.md#step-2-create-virtual-environment)
- Dependencies → [SETUP.md](SETUP.md#step-4-install-python-dependencies)
- Verification → [SETUP.md](SETUP.md#verification)

### Commands & Usage

- All commands → [USAGE.md](USAGE.md#agent-commands)
- Full pipeline → [USAGE.md](USAGE.md#full-pipeline)
- Advanced usage → [USAGE.md](USAGE.md#advanced-usage)
- Examples → [USAGE.md](USAGE.md#examples)

### Configuration

- Environment variables → [CONFIGURATION.md](CONFIGURATION.md)
- Video settings → [CONFIGURATION.md](CONFIGURATION.md#video-settings)
- LLM setup → [CONFIGURATION.md](CONFIGURATION.md#llm-configuration)
- Examples → [CONFIGURATION.md](CONFIGURATION.md#environment-file-examples)

### API Keys

- Gemini → [API_KEYS.md](API_KEYS.md#gemini-api-google)
- Apify → [API_KEYS.md](API_KEYS.md#apify-token)
- Google Docs → [API_KEYS.md](API_KEYS.md#google-drivedocs)
- ElevenLabs → [API_KEYS.md](API_KEYS.md#elevenlabs-optional)
- LM Studio → [API_KEYS.md](API_KEYS.md#lm-studio-local--no-key-needed)

### Video Customization

- Design system → [TEMPLATE_GUIDE.md](TEMPLATE_GUIDE.md)
- Presets → [TEMPLATE_GUIDE.md](TEMPLATE_GUIDE.md#10-design-presets)
- Custom designs → [TEMPLATE_GUIDE.md](TEMPLATE_GUIDE.md#custom-designs)

### Troubleshooting

- Installation issues → [SETUP.md](SETUP.md#troubleshooting)
- Usage issues → [USAGE.md](USAGE.md#troubleshooting-usage)
- API issues → [API_KEYS.md](API_KEYS.md#troubleshooting)
- General issues → [README.md](../README.md#-troubleshooting)

---

## 📞 Getting Help

### Where to Find Answers

**"How do I install?"**
→ [SETUP.md](SETUP.md)

**"What commands are available?"**
→ [USAGE.md](USAGE.md#agent-commands)

**"How do I get API key X?"**
→ [API_KEYS.md](API_KEYS.md)

**"What does setting Y do?"**
→ [CONFIGURATION.md](CONFIGURATION.md)

**"How do I customize the video?"**
→ [TEMPLATE_GUIDE.md](TEMPLATE_GUIDE.md)

**"Why am I getting error Z?"**
→ Search relevant doc's troubleshooting section

**"What files does the code contain?"**
→ [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)

---

## 📋 Checklists

### Pre-Launch Checklist

- [ ] Python 3.13+ installed
- [ ] Node.js 18+ installed
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] Remotion installed (`npm install` in remotion-app/)
- [ ] .env file created (copy from .env.example)
- [ ] LM Studio running (or API keys configured)
- [ ] Verification tests passed

### Before First Run

- [ ] Read [README.md](../README.md) quick start
- [ ] Follow [SETUP.md](SETUP.md) completely
- [ ] Review .env settings
- [ ] Test with: `python agents.py render`

### Before Production

- [ ] All API keys configured
- [ ] .env reviewed and correct
- [ ] Video dimensions set appropriately
- [ ] Design customized (if needed)
- [ ] Sample video generated and reviewed
- [ ] Logs monitored

---

## 🔄 Version & Updates

- **Current Version:** 1.0
- **Last Updated:** May 2, 2026
- **Python:** 3.13+
- **Node.js:** 18+

For updates, check project repository.

---

## 📝 Documentation Status

| Document             | Status | Completeness |
| -------------------- | ------ | ------------ |
| README.md            | ✅     | 100%         |
| SETUP.md             | ✅     | 100%         |
| USAGE.md             | ✅     | 100%         |
| CONFIGURATION.md     | ✅     | 100%         |
| API_KEYS.md          | ✅     | 100%         |
| TEMPLATE_GUIDE.md    | ✅     | 100%         |
| PROJECT_STRUCTURE.md | ✅     | 100%         |

All documentation is comprehensive and up to date.

---

**Start with:** [README.md](../README.md) or [SETUP.md](SETUP.md) depending on whether you're new or installing.
