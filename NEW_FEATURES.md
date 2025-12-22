# New Features Added - Dec 22, 2025

## ✅ Real-Time News via Google News RSS

**What it does:**
- Fetches breaking AI and media news from Google News
- Updates every 15-30 minutes (much faster than regular RSS)
- Completely FREE - no API key needed
- Searches 6 key topics automatically:
  - AI breakthroughs
  - Major AI companies (OpenAI, Anthropic, Google AI)
  - LLMs and models (GPT, Claude, Gemini)
  - Streaming platforms (Netflix, Disney+)
  - Video AI and personalization
  - LLM developments

**How it works:**
1. After fetching 60+ regular RSS feeds, system queries Google News
2. Adds ~30 real-time articles to the pool
3. All articles scored together (Google News items often score high due to recency)
4. Final selection includes mix of RSS + real-time news

**Configuration:**
```bash
# In .env file (enabled by default):
ENABLE_GOOGLE_NEWS=true
```

To disable:
```bash
ENABLE_GOOGLE_NEWS=false
```

**Impact:**
- ⚡ Hear about breaking news 6-12 hours faster
- 📈 Better coverage of same-day developments
- 🎯 More timely competitive intelligence

---

## ✅ Mobile TL;DR Quick Scan

**What it does:**
- Creates a 3-minute quick scan version at the TOP of your email
- Extracts the most important information:
  - Today's top insight
  - 3 key themes
  - First 5 story titles
- Formatted for easy mobile reading
- Blue highlighted box for visibility
- Full digest appears below for desktop deep-dive

**Example Format:**
```
📱 QUICK SCAN (Mobile)
Subject: [Today's headline]
==================================================

🎯 TODAY'S INSIGHT:
[2-sentence summary of biggest trend]

🔑 KEY THEMES:
• Theme 1
• Theme 2
• Theme 3

📰 STORIES (Tap for full digest):
  1. OpenAI releases new video model...
  2. Netflix tests AI personalization...
  3. Creator economy hits $100B...
  [etc]

📖 5+ stories in full digest below
⏱️  3-min scan | Full read: 10-15 min
==================================================

[Full detailed digest continues...]
```

**Use Cases:**
- **Morning commute**: Quick scan on phone (3 min)
- **Between meetings**: Skim key themes, decide what to read later
- **Desktop deep-dive**: Full analysis when you have time

**Configuration:**
```bash
# In .env file (enabled by default):
ENABLE_MOBILE_TLDR=true
```

To disable:
```bash
ENABLE_MOBILE_TLDR=false
```

**Impact:**
- 📱 Much better mobile experience
- ⏱️ Save time - triage before reading
- 🎯 Never miss the most important story

---

## Combined Impact

With both features enabled, your digest now:

1. **Faster**: Real-time news (15-30 min) + RSS (2-24 hours)
2. **More Flexible**: Quick 3-min scan OR full 10-15 min read
3. **Mobile-Friendly**: Designed for phone first, desktop second
4. **Still Free**: Both features use free services
5. **Still Smart**: All articles scored and ranked together

## System Stats Now

| Metric | Before | After |
|--------|--------|-------|
| **Sources** | 60 RSS feeds | 60 RSS + Google News |
| **Freshness** | 2-24 hour delay | 15 min - 24 hour mix |
| **Email Length** | Long | TL;DR + Long |
| **Mobile Experience** | Poor | Excellent |
| **Cost** | $9/month | $9/month (no change) |

## Testing

Both features are **enabled by default**. Your next email will include:
- ✅ Real-time news from Google News
- ✅ Mobile TL;DR at the top

## How to Test Locally

```bash
# Make sure .env has:
DRY_RUN=true
ENABLE_GOOGLE_NEWS=true
ENABLE_MOBILE_TLDR=true

# Run:
python enhanced_daily_ai_digest.py
```

You'll see:
1. Debug output showing Google News fetch
2. Mobile TL;DR in the preview
3. Full digest below

## FAQ

**Q: Will this increase costs?**
A: No! Both features are free. Google News RSS is free, and TL;DR is just reformatting.

**Q: Will emails be longer?**
A: Plain text: Yes (TL;DR adds ~200 words). HTML: TL;DR is collapsible/scrollable.

**Q: Can I disable them?**
A: Yes, set `ENABLE_GOOGLE_NEWS=false` or `ENABLE_MOBILE_TLDR=false` in your .env

**Q: Does Google News have rate limits?**
A: Soft limits. We fetch modestly (6 queries, 5 items each = 30 items). Should be fine for daily use.

**Q: Will TL;DR work on all email clients?**
A: Yes. It's just formatted text at the top. Looks best on Gmail, Outlook, Apple Mail.

## Disabling Features

If you want to disable either feature:

### Via .env (local testing):
```bash
ENABLE_GOOGLE_NEWS=false
ENABLE_MOBILE_TLDR=false
```

### Via GitHub Secrets (production):
Add these secrets with value `false`:
- `ENABLE_GOOGLE_NEWS`
- `ENABLE_MOBILE_TLDR`

**Note**: If secrets are not set, features are enabled by default.

---

## What's Next (Phase 2 - Future)

Potential future enhancements:
1. **Weekly Summary Email** - Trend analysis over 7 days (8 hours to build)
2. **Click Tracking** - Learn what you actually read (6 hours to build)
3. **Story Threading** - Track stories over multiple days (12 hours to build)
4. **Custom Keyword Weights** - Via .env file (3 hours to build)

Let's see how these new features work first!

---

*Updated: December 22, 2025*
