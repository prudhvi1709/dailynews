# Daily AI Digest

Automated daily AI newsletter that fetches trusted RSS feeds, uses OpenAI to create a concise, hallucination-safe morning email, and sends it via Gmail SMTP (App Password). Works locally and in GitHub Actions (scheduled at 10:00 AM IST).

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
- `daily_ai_digest.py` — main script (production-ready variant in repo)
- `.github/workflows/daily-digest.yml` — GitHub Actions workflow (runs daily at 10:00 AM IST)
- `requirements.txt` — Python dependencies
- `.env` — local environment file (not checked into git)

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
	# or: pip install openai feedparser python-dotenv
	```

3. **Create a `.env` file in the repo root with your secrets (no quotes):**
	```ini
	OPENAI_API_KEY=sk-...
	OPENAI_BASE_URL=https://api.openai.com/v1            # optional
	OPENAI_MODEL=gpt-4o-mini                             # optional
	TO_EMAIL=your.receive@mail.com
	FROM_EMAIL=your.sender@gmail.com
	GMAIL_APP_PASSWORD=abcdefghijklmnop                  # 16-char Gmail app password (no spaces)
	FEEDS=https://www.technologyreview.com/feed/,https://www.theverge.com/rss/ai/index.xml
	MAX_ARTICLES=8
	KEYWORDS=ai,artificial intelligence,machine learning,llm,chatbot
	HTTP_TIMEOUT=15
	DRY_RUN=true
	```

4. **Preview (dry run):**
	```bash
	python daily_ai_digest.py
	```

5. **Send email:**
	Set `DRY_RUN=false` (or remove) in `.env` to actually send the email.