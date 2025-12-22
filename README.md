# Daily AI Digest - Enhanced Edition

**Personalized, insightful AI news digest** with 50+ global RSS feeds, intelligent content scoring, and engaging analysis tailored for innovation teams.

Fetches from diverse sources, uses advanced AI to provide opinionated insights (not boring summaries), and delivers via Gmail. Works locally and in GitHub Actions (scheduled at 10:00 AM IST).

## 🆕 Latest Enhancements

The system has been **significantly upgraded**! See [UPGRADE_GUIDE.md](UPGRADE_GUIDE.md) for full details.

**Key improvements:**
- 📰 **50+ diverse RSS feeds** (was 10) - global coverage from US, UK, EU, India, Asia, Australia
- 🎯 **Intelligent scoring** - keyword weighting, recency boost, source diversity
- 💡 **Insightful analysis** - opinionated takes, pattern recognition, innovation angles
- 🌍 **Personalized** - tailored for innovation teams tracking latest AI developments
- 📧 **Better formatting** - engaging structure with themes, detailed analysis, bottom-line insights

---

## Features
- RSS-only source list (no paid news API required)
- Strict "no-hallucination" prompt: summaries only use article metadata
- Curated default feeds (MIT Tech Review, The Verge, Reuters, NYT, etc.) — overridable via env
- Dry-run mode for safe local previews
- Supports custom OpenAI base URL and model
- Simple Gmail SMTP sending using App Password (or swap to SendGrid if preferred)

---

## Files
- `enhanced_daily_ai_digest.py` — **NEW Enhanced version** (production-ready with advanced features)
- `daily_ai_digest.py` — Original version (kept as backup)
- `.github/workflows/daily-digest.yml` — GitHub Actions workflow (runs daily at 10:00 AM IST)
- `requirements.txt` — Python dependencies
- `.env` — local environment file (not checked into git)
- `.env.example` — Template for local setup
- `UPGRADE_GUIDE.md` — Detailed guide on new features and setup

---

## Quick start (local)

1. **Create & activate a Python venv:**
	```bash
	python3 -m venv venv
	source venv/bin/activate     # mac/linux
	# venv\Scripts\activate      # windows
	```

2. **Install dependencies:**
	```bash
	pip install -r requirements.txt
	```

3. **Create a `.env` file from the example:**
	```bash
	cp .env.example .env
	```

4. **Edit `.env` with your credentials:**
	```ini
	OPENAI_API_KEY=sk-...
	OPENAI_MODEL=gpt-4o                                  # or gpt-4o-mini for lower cost
	TO_EMAIL=your.receive@mail.com
	FROM_EMAIL=your.sender@gmail.com
	GMAIL_APP_PASSWORD=abcdefghijklmnop                  # 16-char Gmail app password (no spaces)
	MAX_ARTICLES=20                                      # 15-25 recommended
	DRY_RUN=true
	```

5. **Test the enhanced version (dry run):**
	```bash
	python enhanced_daily_ai_digest.py
	```

6. **Review the output** and when satisfied, set `DRY_RUN=false` to send actual emails.

7. **See [UPGRADE_GUIDE.md](UPGRADE_GUIDE.md)** for detailed documentation and customization options.