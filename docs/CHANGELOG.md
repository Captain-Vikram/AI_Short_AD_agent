# Changelog - Agent Enhancements (2026-05-03)

This log tracks the major functional upgrades made to the CrowdWisdomTrading AI Agent.

## Summary of Changes

1.  **Deep Ad Analysis**: Upgraded the Strategist to perform "Why/How/What" psychological deconstruction.
2.  **Market Signal Integration**: Updated the Copywriter to weave real-time market data into scripts.
3.  **Recursive Research Engine**: Added a multi-layered investigation loop (Google -> reasoning -> Social Deep-Dive).
4.  **Cinematic Elevation**: Added a Director's Review phase to enhance visual metaphors and continuity.
5.  **Multi-Source Intelligence**: Integrated YouTube, X (Twitter), and Reddit scraping.

---

## Detailed Component Upgrades

### 1. Advanced Web Intelligence (`src/media/web_explorer.py` - NEW)
- **Recursive Explorer**: Implemented a two-phase discovery engine.
- **Entity Extraction**: Uses LLM reasoning to extract tickers, influencers, and trending topics from Google Search results.
- **Dynamic Targeting**: Automatically suggests deep-dive platforms based on discovered trends.

### 2. Multi-Source Scraper (`src/media/market_research.py` - NEW)
- **Platform Expansion**: Integrated Apify actors for YouTube, X, and Reddit.
- **Source Weighting**: Implemented logic to calculate data significance based on volume and relevance.
- **Signal Aggregation**: Formats disparate social data into a unified "Market Signal" structure.

### 3. Intelligence Agent (`agents.py` - NEW)
- **Market Intelligence Agent**: A specialized persona that distill raw web noise into high-signal market reports.
- **Signal Specs**: Captures price targets, technical levels, news impact, and professional trader wisdom.

### 4. Psychological Strategist (`agents.py` - ENHANCED)
- **Why/How/What Framework**: Now analyzes ads for psychological triggers (The Why), visual/narrative structure (The How), and core offer mechanics (The What).
- **Market Insights**: Extracts broad trends across ad samples to inform the creative process.

### 5. Data-Driven Copywriter (`agents.py` - ENHANCED)
- **Market Signal Weaving**: Now accepts `--market-data`. It can ingest prices, tickers, and expert quotes to create "live" feeling ads.
- **Retention Engineering**: Hardcoded "A-List" copywriting techniques (Pattern Interrupt, Open Loops, High-Status Language) to eliminate generic AI output.

### 6. Cinematic Director (`agents.py` - ENHANCED)
- **Director's Review**: Added a script elevation phase where a "Film Director" persona adds visual metaphors, camera directions (e.g., Dutch angle), and visual continuity keywords.

### 7. Unified CLI (`agents.py` - EXPANDED)
- New Command: `market-intel` for standalone research.
- New Flags for `all`: `--multi-source` (recursive research), `--market-data` (custom signal input).

### 8. CrewAI Integration (`src/agents/crewai_agents.py` - UPDATED)
- **Recursive Pipeline**: Updated the `MarketingVideoCrew` to 5 agents: Researcher -> Market Analyst -> Strategist -> Copywriter -> Director.
- **Advanced Tools**: Exposed the new recursive research and weighted signal tools to the CrewAI framework.

---

## How to Verify
Run the complete advanced pipeline:
```bash
python agents.py all --query "Nasdaq Growth" --multi-source --render
```
Check `output/market_signals.json` to see the results of the recursive web investigation.
