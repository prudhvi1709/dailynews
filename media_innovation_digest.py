#!/usr/bin/env python3
"""
media_innovation_digest.py
Media Innovation Intelligence System for Streaming/Entertainment Industry

Designed for innovation teams tracking:
- Streaming/OTT platform innovations
- Content discovery & personalization
- Production efficiency & AI tools
- Audience acquisition & retention strategies
- Monetization & business model innovations
- Global media trends

Delivers high-level business insights for leadership presentations and innovation proposals.
"""

import os
import datetime
import feedparser
import requests
import smtplib
from email.message import EmailMessage
from typing import List, Dict, Optional
from openai import OpenAI
from collections import defaultdict
import re

# ---------- Configuration from environment ----------
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
OPENAI_BASE_URL = os.environ.get("OPENAI_BASE_URL")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL") or "gpt-4o"

TO_EMAIL = os.environ.get("TO_EMAIL")
FROM_EMAIL = os.environ.get("FROM_EMAIL")
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD")

# Configurable industry focus (keep generic for GitHub)
INDUSTRY_FOCUS = os.environ.get("INDUSTRY_FOCUS", "streaming_entertainment")
ANALYSIS_STYLE = os.environ.get("ANALYSIS_STYLE", "business_insights")  # business_insights, technical_deep, balanced

# ---------- Comprehensive Media Industry RSS Feeds ----------
FEED_CATEGORIES = {
    # Core Streaming/Entertainment Industry News
    "streaming_industry": [
        "https://variety.com/feed/",
        "https://www.hollywoodreporter.com/feed/",
        "https://thestreamable.com/feed",
        "https://www.streamingmedia.com/RSS/Articles.xml",
        "https://videoweek.com/feed/",
        "https://www.lightreading.com/rss.asp",
        "https://www.nexttv.com/feed",
    ],

    # Media Business & Strategy
    "media_business": [
        "https://www.mediapost.com/rss/disp.cfm",
        "https://www.pressgazette.co.uk/feed/",
        "https://adage.com/rss.xml",
        "https://digiday.com/feed/",
        "https://www.fastcompany.com/latest/rss",
    ],

    # Creator Economy & Platform News
    "creator_economy": [
        "https://www.tubefilter.com/feed/",
        "https://www.theverge.com/rss/creators/index.xml",
        "https://techcrunch.com/tag/creator-economy/feed/",
    ],

    # AI for Media & Content
    "ai_media": [
        "https://www.marktechpost.com/feed/",  # AI tools/tech
        "https://venturebeat.com/category/ai/feed/",
        "https://www.artificialintelligence-news.com/feed/",
        "https://blog.google/technology/ai/rss/",
        "https://openai.com/blog/rss/",
        "https://ai.meta.com/blog/rss/",
    ],

    # Major Tech Companies (Media Initiatives)
    "big_tech": [
        "https://techcrunch.com/tag/streaming/feed/",
        "https://www.theverge.com/rss/tech/index.xml",
        "https://www.engadget.com/rss.xml",
        "https://arstechnica.com/gadgets/feed/",
    ],

    # Streaming Platform Blogs
    "platform_blogs": [
        "https://about.netflix.com/en/news.rss",  # Netflix blog might not have RSS, using news
        "https://newsroom.spotify.com/feeds/",
        "https://www.youtube.com/feeds/videos.xml?channel_id=UC_x5XG1OV2P6uZZ5FSM9Ttw",  # YouTube Official
    ],

    # Entertainment Tech & Innovation
    "entertainment_tech": [
        "https://www.protocol.com/newsletters/entertainment",  # May be limited
        "https://www.wired.com/feed/category/business/media/rss",
    ],

    # Global News Sources
    "global_news": [
        "https://www.reuters.com/technology/media-telecom/rss",
        "https://feeds.bbci.co.uk/news/entertainment_and_arts/rss.xml",
        "https://rss.nytimes.com/services/xml/rss/nyt/Business.xml",
    ],

    # India Entertainment/Media (for global perspective)
    "india_media": [
        "https://economictimes.indiatimes.com/industry/media/entertainment/rssfeeds/13357348.cms",
        "https://www.exchange4media.com/rss/news.xml",
        "https://www.medianama.com/feed/",
    ],

    # Business Strategy & Analysis
    "business_strategy": [
        "https://hbr.org/feed",
        "https://www.mckinsey.com/featured-insights/rss",
        "https://www.businessinsider.com/sai/rss",
    ],

    # Startup & VC (Media/Entertainment focus)
    "startups": [
        "https://news.crunchbase.com/feed/",
        "https://techcrunch.com/tag/entertainment/feed/",
        "https://venturebeat.com/category/media-entertainment/feed/",
    ],
}

# Flatten all feeds
DEFAULT_FEEDS = []
for category, feeds in FEED_CATEGORIES.items():
    DEFAULT_FEEDS.extend(feeds)

FEEDS = os.environ.get("FEEDS") or ",".join(DEFAULT_FEEDS)
MAX_ARTICLES = int(os.environ.get("MAX_ARTICLES") or "20")

# ---------- Media Innovation Keywords with Weights ----------
# Organized by innovation focus areas
KEYWORD_WEIGHTS = {
    # Streaming Platforms & Services (HIGH)
    "netflix": 2.5, "disney+": 2.5, "disney plus": 2.5, "hbo max": 2.5, "max": 2.0,
    "prime video": 2.5, "amazon prime": 2.0, "apple tv+": 2.5, "apple tv": 2.0,
    "spotify": 2.5, "youtube": 2.0, "peacock": 2.0, "paramount+": 2.0, "hulu": 2.0,

    # Streaming Business Models
    "svod": 2.0, "avod": 2.0, "fast": 2.0, "subscription": 1.5, "streaming": 1.3,
    "ott": 1.5, "ctv": 1.5, "connected tv": 1.5,

    # Content Discovery & Personalization (HIGH - your pain point)
    "personalization": 3.0, "recommendation": 3.0, "discovery": 2.5, "algorithm": 2.0,
    "content discovery": 3.0, "search": 1.8, "browse": 1.5,

    # User Engagement & Retention (HIGH - your pain point)
    "engagement": 2.5, "retention": 3.0, "churn": 3.0, "subscriber growth": 2.5,
    "user acquisition": 2.5, "viral": 2.0, "social features": 2.0,

    # Monetization & Revenue (HIGH - your pain point)
    "monetization": 2.5, "arpu": 2.5, "pricing": 2.0, "revenue": 1.8,
    "advertising": 1.8, "ad-supported": 2.0, "bundle": 2.0, "bundling": 2.0,

    # Production Innovation (HIGH - your pain point)
    "virtual production": 2.5, "ai editing": 2.5, "automated production": 2.5,
    "content creation": 2.0, "generative ai": 2.0, "dubbing": 2.0, "localization": 2.0,
    "translation": 1.8, "subtitles": 1.5,

    # AI for Content/Media
    "generative video": 2.5, "text-to-video": 2.5, "video generation": 2.5,
    "content moderation": 2.0, "automatic tagging": 2.0, "metadata": 1.8,

    # Content Strategy
    "original content": 2.0, "licensing": 1.8, "content library": 1.8,
    "binge": 1.5, "release strategy": 2.0,

    # Creator Economy
    "creator": 2.0, "influencer": 1.8, "ugc": 2.0, "user generated": 2.0,
    "substack": 1.8, "patreon": 1.8, "tiktok": 2.0,

    # Technology
    "machine learning": 1.5, "ai": 1.3, "deep learning": 1.5,
    "cloud": 1.2, "cdn": 1.5, "streaming technology": 1.8,

    # Business Events
    "acquisition": 2.0, "merger": 2.0, "partnership": 1.8, "launch": 1.8,
    "funding": 2.0, "ipo": 2.5, "valuation": 2.0,

    # Metrics & Performance
    "subscriber": 1.8, "viewership": 1.8, "watch time": 2.0,
    "engagement rate": 2.0, "conversion": 2.0,

    # Indian streaming (for local context)
    "hotstar": 2.0, "zee5": 2.0, "sonyliv": 2.0, "jiocinema": 2.0,
    "alt balaji": 1.8, "mx player": 1.8,
}

# Add Google News RSS for real-time coverage
ENABLE_GOOGLE_NEWS = os.environ.get("ENABLE_GOOGLE_NEWS", "true").lower() in ("1", "true", "yes")
GOOGLE_NEWS_QUERIES = [
    "streaming+service+innovation",
    "netflix+disney+strategy",
    "content+personalization",
    "OTT+platform+launch",
    "video+streaming+technology",
    "creator+economy",
]

TIMEOUT_SECONDS = int(os.environ.get("HTTP_TIMEOUT") or "15")
DRY_RUN = os.environ.get("DRY_RUN", "false").lower() in ("1", "true", "yes")

# Initialize OpenAI client
client = OpenAI(
    api_key=OPENAI_API_KEY,
    base_url=OPENAI_BASE_URL if OPENAI_BASE_URL else None
)

# ---------- Feed Health Monitoring ----------
FEED_LOG_FILE = "feed_health.log"

def log_feed_health(url: str, success: bool, error: str = ""):
    """Log feed fetch results for monitoring"""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    status = "SUCCESS" if success else f"FAILED: {error[:50]}"
    log_entry = f"{timestamp} | {url[:60]} | {status}\n"

    try:
        with open(FEED_LOG_FILE, "a") as f:
            f.write(log_entry)
    except:
        pass  # Don't fail on logging errors

# ---------- Utility Functions ----------

def fetch_google_news(queries: List[str]) -> List[Dict]:
    """Fetch real-time news from Google News RSS"""
    items = []
    headers = {"User-Agent": "Mozilla/5.0 (compatible; MediaInnovationDigest/1.0)"}

    for query in queries:
        url = f"https://news.google.com/rss/search?q={query}&hl=en&gl=US&ceid=US:en"
        try:
            resp = requests.get(url, headers=headers, timeout=TIMEOUT_SECONDS)
            resp.raise_for_status()
            d = feedparser.parse(resp.content)

            for entry in d.entries[:5]:  # Limit per query
                title = entry.get("title", "").strip()
                summary = entry.get("summary", "").strip()
                link = entry.get("link", "").strip()
                published = entry.get("published", "")

                # Parse published date
                published_parsed = entry.get("published_parsed")
                if published_parsed:
                    try:
                        published_dt = datetime.datetime(*published_parsed[:6])
                    except:
                        published_dt = None
                else:
                    published_dt = None

                items.append({
                    "source": "Google News",
                    "title": title,
                    "description": re.sub(r'<[^>]+>', '', summary)[:500],
                    "url": link,
                    "publishedAt": published,
                    "publishedDt": published_dt,
                })

        except Exception as e:
            print(f"DEBUG: Google News query '{query}' failed: {e}")
            continue

    return items


def fetch_from_feeds(feeds: List[str], max_items: int) -> List[Dict]:
    """Fetch feeds with health monitoring"""
    items: List[Dict] = []
    headers = {"User-Agent": "Mozilla/5.0 (compatible; MediaInnovationDigest/1.0)"}

    for url in feeds:
        try:
            resp = requests.get(url, headers=headers, timeout=TIMEOUT_SECONDS)
            resp.raise_for_status()
            d = feedparser.parse(resp.content)
            log_feed_health(url, True)
        except Exception as e:
            print(f"DEBUG: failed to fetch/parse feed {url}: {e}")
            log_feed_health(url, False, str(e))
            continue

        source_title = d.feed.get("title", "") or url

        for entry in d.entries:
            title = (entry.get("title") or "").strip()

            # Get description
            if entry.get("summary"):
                summary = entry.get("summary", "").strip()
            elif entry.get("content"):
                content = entry.get("content")
                if isinstance(content, list) and content:
                    summary = content[0].get("value", "").strip()
                else:
                    summary = str(content).strip()
            else:
                summary = entry.get("description", "").strip()

            # Clean HTML
            summary = re.sub(r'<[^>]+>', '', summary)
            summary = re.sub(r'\s+', ' ', summary).strip()

            link = (entry.get("link") or "").strip()

            # Parse published date
            published_parsed = entry.get("published_parsed") or entry.get("updated_parsed")
            if published_parsed:
                try:
                    published_dt = datetime.datetime(*published_parsed[:6])
                except:
                    published_dt = None
            else:
                published_dt = None

            published_str = entry.get("published", entry.get("updated", ""))

            items.append({
                "source": source_title,
                "title": title,
                "description": summary[:500],
                "url": link,
                "publishedAt": published_str,
                "publishedDt": published_dt,
            })

            if len(items) >= max_items * 5:
                break

        if len(items) >= max_items * 5:
            break

    return items


def calculate_article_score(item: Dict, keyword_weights: Dict[str, float]) -> float:
    """Score articles based on media innovation relevance"""
    text = (item.get("title", "") + " " + item.get("description", "")).lower()
    score = 0.0

    # Keyword matching with weights
    for keyword, weight in keyword_weights.items():
        if keyword.lower() in text:
            score += weight

    # Recency boost - articles in last 24 hours get extra points
    if item.get("publishedDt"):
        age_hours = (datetime.datetime.now() - item["publishedDt"]).total_seconds() / 3600
        if age_hours < 24:
            recency_boost = 2.0 * (1 - age_hours / 24)
            score += recency_boost

    # Title/description quality signals
    title_len = len(item.get("title", ""))
    if title_len > 60:
        score += 0.3

    desc_len = len(item.get("description", ""))
    if desc_len > 200:
        score += 0.5

    return score


def select_top_articles(items: List[Dict], max_articles: int, keyword_weights: Dict[str, float]) -> List[Dict]:
    """Select top articles with intelligent scoring and diversity"""
    scored_items = []
    for item in items:
        score = calculate_article_score(item, keyword_weights)
        if score > 1.0:  # Minimum relevance threshold
            item["score"] = score
            scored_items.append(item)

    # Sort by score
    scored_items.sort(key=lambda x: x["score"], reverse=True)

    # Deduplicate
    seen_urls = set()
    seen_title_words = []
    unique_items = []

    for item in scored_items:
        url = item.get("url", "").strip()
        title = item.get("title", "").strip().lower()

        if url and url in seen_urls:
            continue

        # Check title similarity
        title_words = set(title.split()[:5])
        is_similar = False
        for seen_words in seen_title_words:
            if len(title_words & seen_words) >= 3:
                is_similar = True
                break

        if is_similar:
            continue

        seen_urls.add(url)
        seen_title_words.append(title_words)
        unique_items.append(item)

        if len(unique_items) >= max_articles:
            break

    # Ensure source diversity
    source_counts = defaultdict(int)
    diverse_items = []

    for item in unique_items:
        source = item.get("source", "")
        if source_counts[source] < 3:
            diverse_items.append(item)
            source_counts[source] += 1

    return diverse_items


def build_media_innovation_prompt(articles: List[Dict]) -> str:
    """Build prompt for media innovation insights"""
    now_iso = datetime.datetime.now().strftime("%Y-%m-%d %H:%M IST")

    prompt = f"""You are a media industry analyst writing for an innovation team at a streaming/entertainment company. Your reader needs HIGH-LEVEL BUSINESS INSIGHTS for leadership presentations and innovation proposals.

YOUR MISSION:
Write an engaging digest that identifies innovation opportunities in streaming/entertainment. Focus on:
1. Competitive moves by streaming platforms (Netflix, Disney+, etc.)
2. New technologies affecting content discovery, production, or monetization
3. Business model innovations and pricing strategies
4. Audience engagement and retention tactics
5. What can be learned and applied

CRITICAL FOCUS AREAS (client's pain points):
- Content Discovery & Personalization innovations
- Content Production Efficiency (AI tools, automation)
- User Acquisition & Retention strategies
- Monetization & Revenue Growth models

WRITING STYLE:
- **Business-focused, not technical** - suitable for leadership presentations
- Opinionated and analytical ("This matters because...")
- Connect dots between stories
- Focus on "what can we learn?" and "what should we consider?"
- Highlight competitive intelligence
- Identify emerging trends
- Be conversational and engaging

FORMAT OUTPUT EXACTLY AS:

Subject: [Engaging subject line capturing biggest industry trend today, max 10 words]

=== TOP INNOVATION INSIGHT ===
[2-3 sentences: What's the most important innovation trend or competitive move today? Why does it matter for streaming/entertainment companies?]

=== KEY THEMES TODAY ===
• [Theme 1]: Brief insight
• [Theme 2]: Brief insight
• [Theme 3]: Brief insight

=== INNOVATION STORIES ===

[For each story:]

## [Number]. [Engaging Title]
**Source**: [Source name] | **Category**: [Discovery/Production/Engagement/Monetization/Other]

[2-3 paragraphs covering:
- What happened (specific facts)
- Why it matters to streaming/entertainment
- Competitive implications
- What's innovative or surprising]

**Innovation Opportunity**: [1-2 sentences: What could streaming companies learn or implement from this?]
**Link**: [URL]

---

[Repeat for each story]

=== BOTTOM LINE ===
[2-3 sentences: What do these stories collectively tell us about where the industry is heading? What should innovation teams be thinking about?]

---
Delivered: {now_iso}

NOW, HERE ARE TODAY'S ARTICLES (sorted by relevance to streaming/entertainment innovation):

"""

    for i, article in enumerate(articles, 1):
        prompt += f"""
[{i}] Title: {article.get('title')}
Source: {article.get('source')}
Published: {article.get('publishedAt')}
URL: {article.get('url')}
Description: {article.get('description')}
Relevance Score: {article.get('score', 0):.2f}

"""

    prompt += """
IMPORTANT REMINDERS:
- Only use information provided - no hallucinations
- BUSINESS INSIGHTS, not technical details
- Focus on streaming/entertainment innovation
- Every story should have "Innovation Opportunity"
- Connect stories and identify patterns
- Write for leadership presentations

Write the digest now:"""

    return prompt


def ask_openai(prompt: str, model: Optional[str] = None) -> str:
    """Call OpenAI for analysis"""
    model_to_use = model or OPENAI_MODEL

    resp = client.chat.completions.create(
        model=model_to_use,
        messages=[
            {"role": "system", "content": "You are a media industry analyst who writes insightful business analysis for innovation teams at streaming/entertainment companies. You identify innovation opportunities and provide actionable competitive intelligence."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.7,
    )

    try:
        return resp.choices[0].message.content.strip()
    except Exception:
        try:
            return resp["choices"][0]["message"]["content"].strip()
        except Exception as e:
            raise RuntimeError(f"Unable to parse OpenAI response: {e}")


def parse_subject_and_body(ai_text: str):
    """Parse AI response"""
    lines = ai_text.splitlines()
    subject = "Media Innovation Digest"
    body_lines = []

    if lines:
        first = lines[0].strip()
        if first.lower().startswith("subject:"):
            subject = first.split(":", 1)[1].strip()
            body_lines = lines[1:]
        else:
            body_lines = lines

    body = "\n".join(body_lines).strip()
    return subject, body


def create_mobile_tldr(ai_text: str) -> str:
    """Create mobile-friendly TL;DR version"""
    # Extract key themes and first line of each story
    lines = ai_text.split('\n')
    mobile_content = []

    mobile_content.append("📱 QUICK BRIEF (Mobile)\n")

    # Find KEY THEMES section
    in_themes = False
    for line in lines:
        if "KEY THEMES" in line.upper():
            in_themes = True
            mobile_content.append("\n🔑 TODAY'S THEMES:\n")
            continue
        if in_themes:
            if line.startswith('•'):
                mobile_content.append(line)
            elif line.startswith('==='):
                break

    mobile_content.append("\n\n📖 Read full analysis on desktop for detailed insights and innovation opportunities.")

    return "\n".join(mobile_content)


def log_email_send(subject: str, status: str, log_file: str = "email_log.txt", max_entries: int = 30):
    """Log email sends"""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"{timestamp} | {status} | {subject}\n"

    try:
        with open(log_file, "r") as f:
            lines = f.readlines()
    except FileNotFoundError:
        lines = []

    lines.append(log_entry)
    lines = lines[-max_entries:]

    with open(log_file, "w") as f:
        f.writelines(lines)


def send_via_gmail(subject: str, body: str, mobile_version: Optional[str] = None):
    """Send email via Gmail"""
    if not (FROM_EMAIL and TO_EMAIL and GMAIL_APP_PASSWORD):
        raise ValueError("Missing FROM_EMAIL / TO_EMAIL / GMAIL_APP_PASSWORD")

    msg = EmailMessage()
    msg["From"] = FROM_EMAIL
    msg["To"] = TO_EMAIL
    msg["Subject"] = subject

    # If mobile version exists, send it as plain text
    if mobile_version:
        msg.set_content(mobile_version + "\n\n---\n\nFULL DIGEST:\n\n" + body)
    else:
        msg.set_content(body)

    # HTML version
    html_body = body.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    html_body = html_body.replace("\n\n", "</p><p>")
    html_body = html_body.replace("\n", "<br>")
    html_body = f"<html><body style='font-family: system-ui, sans-serif; line-height: 1.6; max-width: 700px; margin: 0 auto; padding: 20px;'><p>{html_body}</p></body></html>"

    msg.add_alternative(html_body, subtype="html")

    with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=30) as smtp:
        try:
            smtp.login(FROM_EMAIL, GMAIL_APP_PASSWORD)
            smtp.send_message(msg)
        except smtplib.SMTPAuthenticationError as e:
            raise RuntimeError(f"Gmail authentication failed: {e}")


# ---------- Main Flow ----------

def main():
    if not OPENAI_API_KEY:
        raise SystemExit("OPENAI_API_KEY not set")

    feed_list = [u.strip() for u in FEEDS.split(",") if u.strip()]

    print(f"DEBUG: Fetching from {len(feed_list)} RSS feeds...")
    raw_items = fetch_from_feeds(feed_list, max_items=MAX_ARTICLES)

    # Add Google News if enabled
    if ENABLE_GOOGLE_NEWS:
        print(f"DEBUG: Fetching real-time news from Google News...")
        google_items = fetch_google_news(GOOGLE_NEWS_QUERIES)
        raw_items.extend(google_items)
        print(f"DEBUG: Added {len(google_items)} items from Google News")

    print(f"DEBUG: Fetched {len(raw_items)} total items")

    top_articles = select_top_articles(raw_items, MAX_ARTICLES, KEYWORD_WEIGHTS)
    print(f"DEBUG: Selected {len(top_articles)} top articles")

    # Show top articles
    for i, art in enumerate(top_articles[:5], 1):
        print(f"DEBUG: #{i} (score {art['score']:.2f}): {art['title'][:80]}")

    if not top_articles:
        print("WARNING: No relevant articles found")
        return

    prompt_used = build_media_innovation_prompt(top_articles)

    print("DEBUG: Calling OpenAI for media innovation analysis...")
    try:
        ai_out = ask_openai(prompt_used)
    except Exception as e:
        raise RuntimeError(f"OpenAI request failed: {e}")

    subject, body = parse_subject_and_body(ai_out)

    # Create mobile TL;DR
    mobile_tldr = create_mobile_tldr(ai_out)

    if DRY_RUN:
        print("\n" + "="*80)
        print("DRY RUN - EMAIL PREVIEW")
        print("="*80)
        print(f"Subject: {subject}")
        print("="*80)
        print("\n--- MOBILE TL;DR ---")
        print(mobile_tldr)
        print("\n--- FULL DIGEST ---")
        print(body)
        print("="*80)
        log_email_send(subject, "DRY_RUN")
    else:
        try:
            send_via_gmail(subject, body, mobile_tldr)
            print(f"SUCCESS: Sent '{subject}'")
            log_email_send(subject, "SUCCESS")
        except Exception as e:
            error_msg = f"FAILED: {str(e)[:100]}"
            print(f"ERROR: Failed to send email: {e}")
            log_email_send(subject, error_msg)
            raise


if __name__ == "__main__":
    main()
