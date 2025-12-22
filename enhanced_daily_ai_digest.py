#!/usr/bin/env python3
"""
enhanced_daily_ai_digest.py
AI News + Media Innovation Intelligence System

Hybrid digest covering:
- Latest AI developments (models, research, tools, companies)
- Media/streaming industry innovations and competitive moves
- AI applications in content, personalization, production
- Business insights for media innovation teams
- 60+ diverse global sources (AI + Media/Entertainment)

Designed for innovation teams tracking AI trends AND media industry developments.
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

# from dotenv import load_dotenv

# # # Load local .env for local testing (ignored in GH Actions)
# load_dotenv()
# ---------- Configuration from environment ----------
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
OPENAI_BASE_URL = os.environ.get("OPENAI_BASE_URL")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL") or "gpt-4o"  # Use stronger model for better analysis

TO_EMAIL = os.environ.get("TO_EMAIL")
FROM_EMAIL = os.environ.get("FROM_EMAIL")
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD")

# ---------- Comprehensive Global RSS Feed List ----------
# Organized by category for diversity
FEED_CATEGORIES = {
    "ai_focused": [
        "https://www.technologyreview.com/feed/",
        "https://www.artificialintelligence-news.com/feed/",
        "https://venturebeat.com/category/ai/feed/",
        "https://www.marktechpost.com/feed/",
        "https://syncedreview.com/feed/",
        "https://www.unite.ai/feed/",
    ],
    "major_tech_news": [
        "https://www.theverge.com/rss/ai/index.xml",
        "https://techcrunch.com/tag/artificial-intelligence/feed/",
        "https://www.wired.com/feed/tag/ai/latest/rss",
        "https://www.zdnet.com/topic/artificial-intelligence/rss.xml",
        "https://arstechnica.com/tag/artificial-intelligence/feed/",
        "https://www.engadget.com/rss.xml",
    ],
    "business_analysis": [
        "https://www.forbes.com/ai/feed/",
        "https://www.businessinsider.com/sai/rss",
        "https://www.cnbc.com/id/19854910/device/rss/rss.html",  # Tech
        "https://fortune.com/section/artificial-intelligence/feed/",
    ],
    "research_academic": [
        "https://blog.google/technology/ai/rss/",
        "https://openai.com/blog/rss/",
        "https://www.deepmind.com/blog/rss.xml",
        "https://blogs.nvidia.com/feed/",
        "https://ai.meta.com/blog/rss/",
        "https://www.microsoft.com/en-us/research/feed/",
    ],
    "open_source_community": [
        "https://huggingface.co/blog/feed.xml",
        "https://github.blog/category/ai-and-ml/feed/",
        "https://pytorch.org/blog/feed.xml",
    ],
    "developer_focused": [
        "https://news.ycombinator.com/rss",
        "https://www.reddit.com/r/MachineLearning/.rss",
        "https://www.reddit.com/r/artificial/.rss",
        "https://dev.to/feed/tag/ai",
    ],
    "news_general": [
        "https://feeds.bbci.co.uk/news/technology/rss.xml",
        "https://rss.nytimes.com/services/xml/rss/nyt/Technology.xml",
        "https://www.reuters.com/technology/artificial-intelligence/rss",
        "https://www.theguardian.com/technology/artificialintelligenceai/rss",
        "https://www.wsj.com/xml/rss/3_7455.xml",  # Tech
    ],
    "asia_india": [
        "https://timesofindia.indiatimes.com/rssfeeds/66949542.cms",  # Tech
        "https://economictimes.indiatimes.com/tech/rssfeeds/13357270.cms",
        "https://tech.hindustantimes.com/rss/tech/rssfeed.xml",
        "https://www.thehindu.com/sci-tech/technology/feeder/default.rss",
    ],
    "uk_europe": [
        "https://www.standard.co.uk/tech/rss",
        "https://www.independent.co.uk/tech/rss",
        "https://www.telegraph.co.uk/technology/rss.xml",
    ],
    "australia": [
        "https://www.smh.com.au/rss/technology.xml",
        "https://www.afr.com/technology/rss",
    ],
    "startups_vc": [
        "https://news.crunchbase.com/feed/",
        "https://techcrunch.com/tag/venture-capital/feed/",
    ],
    "ai_newsletters_blogs": [
        "https://www.aisnakeoil.com/feed",
        "https://www.oneusefulthing.org/feed",
    ],
    # Media/Streaming Industry (for context and applications)
    "streaming_media": [
        "https://variety.com/feed/",
        "https://www.hollywoodreporter.com/feed/",
        "https://thestreamable.com/feed",
        "https://www.streamingmedia.com/RSS/Articles.xml",
    ],
    "creator_economy": [
        "https://www.tubefilter.com/feed/",
        "https://techcrunch.com/tag/creator-economy/feed/",
    ],
    "media_business": [
        "https://adage.com/rss.xml",
        "https://digiday.com/feed/",
    ],
    # Linear TV / Broadcast
    "broadcast_tv": [
        "https://www.broadcastingcable.com/feed",
        "https://tvnewscheck.com/feed/",
        "https://www.sportico.com/feed/",
        "https://www.multichannel.com/feed",
    ],
}

# Flatten all feeds
DEFAULT_FEEDS = []
for category, feeds in FEED_CATEGORIES.items():
    DEFAULT_FEEDS.extend(feeds)

FEEDS = os.environ.get("FEEDS") or ",".join(DEFAULT_FEEDS)
MAX_ARTICLES = int(os.environ.get("MAX_ARTICLES") or "20")  # Increased for comprehensive coverage

# Enhanced keywords with weights for scoring
KEYWORD_WEIGHTS = {
    # High priority - Hot topics and innovations
    "gpt-4": 3.0, "gpt-5": 3.0, "claude": 3.0, "gemini": 3.0, "llama": 2.5,
    "o1": 2.5, "reasoning model": 2.5, "frontier model": 2.5,
    "breakthrough": 2.5, "agi": 2.5,

    # Company tracking
    "openai": 2.0, "anthropic": 2.0, "google ai": 2.0, "deepmind": 2.0,
    "meta ai": 2.0, "microsoft ai": 2.0, "hugging face": 2.0,

    # Key technologies
    "transformer": 2.0, "multimodal": 2.0, "diffusion": 2.0,
    "reinforcement learning": 2.0, "rlhf": 2.0,

    # Applications and tools
    "copilot": 1.8, "chatgpt": 1.8, "midjourney": 1.8, "stable diffusion": 1.8,

    # Open source
    "open source": 1.8, "open model": 1.8, "llama": 2.0,

    # Research terms
    "paper": 1.5, "arxiv": 1.5, "research": 1.3, "benchmark": 1.5,

    # Business/startup
    "startup": 1.5, "funding": 1.5, "series a": 1.7, "series b": 1.7,
    "acquisition": 1.8, "ipo": 2.0,

    # General AI terms (lower weight)
    "artificial intelligence": 1.0, "ai": 1.0, "machine learning": 1.0,
    "deep learning": 1.0, "neural network": 1.0, "llm": 1.2,

    # Media/Streaming (for context and applications)
    "netflix": 2.0, "disney+": 2.0, "hbo max": 2.0, "prime video": 2.0,
    "spotify": 2.0, "youtube": 1.8, "streaming": 1.5, "ott": 1.5,
    "personalization": 2.5, "recommendation": 2.5, "content discovery": 2.5,
    "engagement": 2.0, "retention": 2.0, "churn": 2.0,
    "creator": 1.8, "influencer": 1.5, "tiktok": 1.8,
    "video generation": 2.5, "dubbing": 2.0, "localization": 2.0,

    # Linear TV / Broadcast (traditional media)
    "broadcast": 1.8, "cable tv": 1.8, "linear tv": 2.0, "live tv": 1.8,
    "television": 1.5, "tv ratings": 2.0, "viewership": 2.0, "nielsen": 2.0,
    "cord cutting": 2.0, "cord-cutting": 2.0, "broadcast network": 1.8,
    "nbc": 1.5, "cbs": 1.5, "abc": 1.5, "fox": 1.5, "cnn": 1.5,
    "live sports": 2.0, "sports broadcasting": 2.0,
}

# Additional recency boost (newer = better)
RECENCY_BOOST_HOURS = 24  # Articles in last 24 hours get extra points

# Google News RSS for real-time coverage (15-30 min delay)
ENABLE_GOOGLE_NEWS = os.environ.get("ENABLE_GOOGLE_NEWS", "true").lower() in ("1", "true", "yes")

def generate_google_news_queries(keyword_weights: Dict[str, float], max_queries: int = 10) -> List[str]:
    """
    Dynamically generate Google News queries from keyword dictionary
    Takes top-weighted keywords and creates smart search queries
    Much better than hardcoded queries!
    """
    # Sort keywords by weight (highest first)
    sorted_keywords = sorted(keyword_weights.items(), key=lambda x: x[1], reverse=True)

    queries = []

    # Strategy 1: Top individual keywords (score >= 2.5)
    top_keywords = [k for k, w in sorted_keywords if w >= 2.5][:6]
    for keyword in top_keywords:
        query = keyword.replace(" ", "+")
        queries.append(query)

    # Strategy 2: Combine related AI keywords
    ai_companies = ["OpenAI", "Anthropic", "Google+AI", "DeepMind"]
    queries.append("+OR+".join(ai_companies))

    # Strategy 3: Combine streaming platforms
    streaming = ["Netflix", "Disney%2B", "Spotify", "YouTube"]
    queries.append("+OR+".join(streaming))

    # Strategy 4: AI + Media combo
    queries.append("AI+video+generation")
    queries.append("AI+content+personalization")

    # Strategy 5: Broadcast/Linear TV
    queries.append("broadcast+television+streaming")
    queries.append("linear+TV+ratings")

    return queries[:max_queries]  # Limit to avoid rate limits

# Mobile TL;DR version
ENABLE_MOBILE_TLDR = os.environ.get("ENABLE_MOBILE_TLDR", "true").lower() in ("1", "true", "yes")

TIMEOUT_SECONDS = int(os.environ.get("HTTP_TIMEOUT") or "15")
DRY_RUN = os.environ.get("DRY_RUN", "false").lower() in ("1", "true", "yes")

# Initialize OpenAI client
client = OpenAI(
    api_key=OPENAI_API_KEY,
    base_url=OPENAI_BASE_URL if OPENAI_BASE_URL else None
)

# ---------- Enhanced Utility Functions ----------

def fetch_from_feeds(feeds: List[str], max_items: int) -> List[Dict]:
    """
    Fetch feeds with better error handling and metadata extraction
    """
    items: List[Dict] = []
    headers = {"User-Agent": "Mozilla/5.0 (compatible; PersonalAIDigest/2.0)"}

    for url in feeds:
        try:
            resp = requests.get(url, headers=headers, timeout=TIMEOUT_SECONDS)
            resp.raise_for_status()
            d = feedparser.parse(resp.content)
        except Exception as e:
            print(f"DEBUG: failed to fetch/parse feed {url}: {e}")
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

            # Clean HTML from summary
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
                "description": summary[:500],  # Limit description length
                "url": link,
                "publishedAt": published_str,
                "publishedDt": published_dt,
            })

            if len(items) >= max_items * 5:  # Fetch more for better selection
                break

        if len(items) >= max_items * 5:
            break

    return items


def fetch_google_news(queries: List[str]) -> List[Dict]:
    """
    Fetch real-time news from Google News RSS (15-30 min delay)
    Free, no API key needed
    """
    items = []
    headers = {"User-Agent": "Mozilla/5.0 (compatible; AIMediaDigest/2.0)"}

    for query in queries:
        url = f"https://news.google.com/rss/search?q={query}&hl=en&gl=US&ceid=US:en"
        try:
            resp = requests.get(url, headers=headers, timeout=TIMEOUT_SECONDS)
            resp.raise_for_status()
            d = feedparser.parse(resp.content)

            for entry in d.entries[:5]:  # Limit 5 per query to avoid spam
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

                # Clean HTML from summary
                summary = re.sub(r'<[^>]+>', '', summary)
                summary = re.sub(r'\s+', ' ', summary).strip()

                items.append({
                    "source": "Google News (Real-time)",
                    "title": title,
                    "description": summary[:500],
                    "url": link,
                    "publishedAt": published,
                    "publishedDt": published_dt,
                })

        except Exception as e:
            print(f"DEBUG: Google News query '{query}' failed: {e}")
            continue

    print(f"DEBUG: Fetched {len(items)} items from Google News")
    return items


def calculate_article_score(item: Dict, keyword_weights: Dict[str, float]) -> float:
    """
    Score articles based on relevance, recency, and interest
    Higher score = more relevant/interesting
    """
    text = (item.get("title", "") + " " + item.get("description", "")).lower()
    score = 0.0

    # Keyword matching with weights
    for keyword, weight in keyword_weights.items():
        if keyword.lower() in text:
            score += weight

    # Recency boost - articles in last 24 hours get extra points
    if item.get("publishedDt"):
        age_hours = (datetime.datetime.now() - item["publishedDt"]).total_seconds() / 3600
        if age_hours < RECENCY_BOOST_HOURS:
            # Boost based on freshness (0-24 hours: +2.0 to +0.5)
            recency_boost = 2.0 * (1 - age_hours / RECENCY_BOOST_HOURS)
            score += recency_boost

    # Title length boost (longer titles often more substantive)
    title_len = len(item.get("title", ""))
    if title_len > 60:
        score += 0.3

    # Description length boost
    desc_len = len(item.get("description", ""))
    if desc_len > 200:
        score += 0.5

    return score


def select_top_articles(items: List[Dict], max_articles: int, keyword_weights: Dict[str, float]) -> List[Dict]:
    """
    Select top articles with intelligent scoring and diversity
    """
    # Filter out items without AI relevance (score > 0)
    scored_items = []
    for item in items:
        score = calculate_article_score(item, keyword_weights)
        if score > 0.8:  # Minimum relevance threshold
            item["score"] = score
            scored_items.append(item)

    # Sort by score
    scored_items.sort(key=lambda x: x["score"], reverse=True)

    # Deduplicate by URL and similar titles
    seen_urls = set()
    seen_title_words = []
    unique_items = []

    for item in scored_items:
        url = item.get("url", "").strip()
        title = item.get("title", "").strip().lower()

        # Skip if duplicate URL
        if url and url in seen_urls:
            continue

        # Skip if very similar title (avoid duplicate stories)
        title_words = set(title.split()[:5])  # First 5 words
        is_similar = False
        for seen_words in seen_title_words:
            if len(title_words & seen_words) >= 3:  # 3+ words match
                is_similar = True
                break

        if is_similar:
            continue

        seen_urls.add(url)
        seen_title_words.append(title_words)
        unique_items.append(item)

        if len(unique_items) >= max_articles:
            break

    # Ensure source diversity - don't have too many from one source
    source_counts = defaultdict(int)
    diverse_items = []

    for item in unique_items:
        source = item.get("source", "")
        if source_counts[source] < 3:  # Max 3 articles per source
            diverse_items.append(item)
            source_counts[source] += 1

    return diverse_items


def build_enhanced_prompt(articles: List[Dict], user_context: str) -> str:
    """
    Build prompt for insightful, opinionated, innovation-focused analysis
    """
    now_iso = datetime.datetime.now().strftime("%Y-%m-%d %H:%M IST")

    prompt = f"""You are an insightful AI analyst writing for an innovation team leader in the media/entertainment industry. Your reader tracks AI developments AND media industry innovations to identify opportunities.

YOUR MISSION: Transform these news items into an engaging, opinionated digest that:
1. Covers latest AI developments (models, tools, research, companies)
2. Highlights media/streaming industry innovations and competitive moves
3. Connects AI trends to media/entertainment applications
4. Identifies innovation opportunities for media companies
5. Provides business insights (high-level, suitable for leadership)

CONTEXT ABOUT YOUR READER:
{user_context}

CRITICAL: When discussing AI news, contextualize for media/entertainment:
- How could this AI tech be used in content creation, personalization, or production?
- What does this mean for streaming platforms, content discovery, or audience engagement?
- Are competitors (Netflix, Disney+, Spotify, YouTube) likely using similar tech?
- What innovation opportunities does this create for media companies?

WRITING STYLE:
- Be opinionated and analytical (e.g., "This is a big deal because..." or "This suggests...")
- Connect dots between AI trends and media applications
- Highlight what's genuinely new vs. incremental
- Use engaging, conversational language (not boring corporate speak)
- Include specific details but focus on business implications
- Balance AI technical news with media industry context

FORMAT YOUR OUTPUT EXACTLY AS:

Subject: [Create an engaging subject line that captures the biggest theme/trend of the day, max 10 words]

=== TOP INSIGHT ===
[2-3 sentences: What's the most important pattern or trend today? Connect multiple stories if relevant. Be opinionated.]

=== KEY THEMES TODAY ===
• [Theme 1]: Brief insight
• [Theme 2]: Brief insight
• [Theme 3]: Brief insight

=== DETAILED STORIES ===

[For each story, write in this format:]

## [Number]. [Engaging Title]
**Source**: [Source name] | **When**: [Timeframe like "Today" or "Yesterday"]

[2-3 engaging paragraphs that include:
- What happened (specific facts, numbers, quotes)
- Why it matters (analysis and implications)
- What's interesting or surprising about it
- Any connections to other trends or stories]

**Link**: [URL]
**Innovation angle**: [1 sentence: What could innovation teams learn or do with this?]

---

[Repeat for each story]

=== BOTTOM LINE ===
[2-3 sentences: Final thought about what all this means. What should readers be thinking about? Any predictions or questions to ponder?]

---
Delivered: {now_iso}

NOW, HERE ARE TODAY'S ARTICLES (sorted by relevance):

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
- Only use information provided above - no hallucinations
- Be engaging and opinionated (boring = bad)
- Connect stories and identify patterns
- Focus on innovation opportunities
- Use conversational language
- Include specific facts and details
- Make it worth the reader's time

Write the digest now:"""

    return prompt


def ask_openai(prompt: str, model: Optional[str] = None) -> str:
    """Call OpenAI with enhanced model"""
    model_to_use = model or OPENAI_MODEL

    resp = client.chat.completions.create(
        model=model_to_use,
        messages=[
            {"role": "system", "content": "You are an insightful, engaging AI analyst who writes for innovation leaders. You connect dots, spot trends, and provide opinionated analysis. You make AI news interesting and actionable."},
            {"role": "user", "content": prompt},
        ],
    )

    try:
        return resp.choices[0].message.content.strip()
    except Exception:
        try:
            return resp["choices"][0]["message"]["content"].strip()
        except Exception as e:
            raise RuntimeError(f"Unable to parse OpenAI response: {e}")


def parse_subject_and_body(ai_text: str):
    """Parse AI response into subject and body"""
    lines = ai_text.splitlines()
    subject = "Daily AI Digest - Innovation Insights"
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


def create_mobile_tldr(ai_text: str, subject: str) -> str:
    """
    Create mobile-friendly TL;DR version (3-min quick scan)
    Extracts key themes and first sentence of each story
    """
    lines = ai_text.split('\n')
    mobile_content = []

    mobile_content.append(f"📱 QUICK SCAN (Mobile)\n")
    mobile_content.append(f"Subject: {subject}\n")
    mobile_content.append("="*50)

    # Extract TOP INSIGHT
    in_top_insight = False
    top_insight_lines = []
    for line in lines:
        if "TOP INSIGHT" in line.upper():
            in_top_insight = True
            continue
        if in_top_insight:
            if line.startswith('===') or line.startswith('##'):
                break
            if line.strip():
                top_insight_lines.append(line.strip())

    if top_insight_lines:
        mobile_content.append("\n🎯 TODAY'S INSIGHT:")
        mobile_content.append(" ".join(top_insight_lines[:2]))  # First 2 sentences only

    # Extract KEY THEMES
    in_themes = False
    theme_count = 0
    for line in lines:
        if "KEY THEMES" in line.upper():
            in_themes = True
            mobile_content.append("\n\n🔑 KEY THEMES:")
            continue
        if in_themes:
            if line.startswith('•'):
                mobile_content.append(line)
                theme_count += 1
                if theme_count >= 3:  # Limit to 3 themes
                    break
            elif line.startswith('==='):
                break

    # Extract story titles only
    mobile_content.append("\n\n📰 STORIES (Tap for full digest):")
    story_count = 0
    for line in lines:
        if line.startswith('## '):
            # Extract just the title
            title = line.replace('##', '').strip()
            # Remove numbering if present
            if '. ' in title:
                title = title.split('. ', 1)[1] if len(title.split('. ', 1)) > 1 else title
            mobile_content.append(f"  {story_count + 1}. {title[:60]}...")
            story_count += 1
            if story_count >= 5:  # Show max 5 stories in TL;DR
                break

    mobile_content.append(f"\n\n📖 {story_count}+ stories in full digest below")
    mobile_content.append("⏱️  3-min scan | Full read: 10-15 min")
    mobile_content.append("\n" + "="*50 + "\n")

    return "\n".join(mobile_content)


def log_email_send(subject: str, status: str, log_file: str = "email_log.txt", max_entries: int = 30):
    """Log email sends with automatic cleanup"""
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


def send_via_gmail(subject: str, body: str, mobile_tldr: Optional[str] = None):
    """Send email via Gmail SMTP with optional mobile TL;DR"""
    if not (FROM_EMAIL and TO_EMAIL and GMAIL_APP_PASSWORD):
        raise ValueError("Missing FROM_EMAIL / TO_EMAIL / GMAIL_APP_PASSWORD env vars")

    msg = EmailMessage()
    msg["From"] = FROM_EMAIL
    msg["To"] = TO_EMAIL
    msg["Subject"] = subject

    # Combine mobile TL;DR with full body for plain text
    if mobile_tldr:
        plain_text = mobile_tldr + "\n\n" + body
    else:
        plain_text = body

    msg.set_content(plain_text)

    # Create nice HTML version with better formatting
    if mobile_tldr:
        # Mobile TL;DR at top with background color for visibility
        mobile_html = mobile_tldr.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        mobile_html = mobile_html.replace("\n", "<br>")
        mobile_section = f"<div style='background-color: #f0f8ff; padding: 15px; margin-bottom: 20px; border-left: 4px solid #0066cc;'>{mobile_html}</div>"
    else:
        mobile_section = ""

    body_html = body.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    body_html = body_html.replace("\n\n", "</p><p>")
    body_html = body_html.replace("\n", "<br>")

    html_body = f"<html><body style='font-family: system-ui, -apple-system, sans-serif; line-height: 1.6; max-width: 700px; margin: 0 auto; padding: 20px;'>{mobile_section}<p>{body_html}</p></body></html>"

    msg.add_alternative(html_body, subtype="html")

    with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=30) as smtp:
        try:
            smtp.login(FROM_EMAIL, GMAIL_APP_PASSWORD)
            smtp.send_message(msg)
        except smtplib.SMTPAuthenticationError as e:
            raise RuntimeError(
                "SMTPAuthenticationError: Gmail rejected credentials. "
                f"Check App Password and ensure 2FA is ON. Original: {e}"
            )


# ---------- Main Flow ----------

def main():
    if not OPENAI_API_KEY:
        raise SystemExit("OPENAI_API_KEY not set.")

    # Build feed list
    feed_list = [u.strip() for u in FEEDS.split(",") if u.strip()]

    print(f"DEBUG: Fetching from {len(feed_list)} RSS feeds...")
    raw_items = fetch_from_feeds(feed_list, max_items=MAX_ARTICLES)
    print(f"DEBUG: Fetched {len(raw_items)} raw items from RSS feeds")

    # Add Google News for real-time coverage if enabled
    if ENABLE_GOOGLE_NEWS:
        print(f"DEBUG: Generating dynamic Google News queries from keyword dictionary...")
        google_queries = generate_google_news_queries(KEYWORD_WEIGHTS, max_queries=10)
        print(f"DEBUG: Generated {len(google_queries)} queries: {google_queries[:3]}...")
        print(f"DEBUG: Fetching real-time news from Google News...")
        google_items = fetch_google_news(google_queries)
        raw_items.extend(google_items)
        print(f"DEBUG: Total items after Google News: {len(raw_items)}")

    top_articles = select_top_articles(raw_items, MAX_ARTICLES, KEYWORD_WEIGHTS)
    print(f"DEBUG: Selected {len(top_articles)} top articles")

    # Show top articles
    for i, art in enumerate(top_articles[:5], 1):
        print(f"DEBUG: #{i} (score {art['score']:.2f}): {art['title'][:80]}")

    if not top_articles:
        print("WARNING: No relevant articles found")
        return

    # Build user context
    user_context = """
    - Role: Innovation team member for media/entertainment industry client
    - Location: India (but tracking global developments)
    - Industry Focus: Streaming/Entertainment with AI applications
    - AI Interests: ALL AI topics (LLMs, tools, open source, research, startups) + how they apply to media
    - Media Interests: Content discovery & personalization, production efficiency, audience engagement, monetization
    - AI Companies: OpenAI, Anthropic, Google AI, Meta AI, Mistral, Hugging Face, Microsoft AI, Amazon AI, startups
    - Media Companies: Netflix, Disney+, Spotify, YouTube, Prime Video, emerging streaming platforms, creator economy
    - Geography: Global coverage (US, UK, EU, India, Asia, Australia)
    - Deliverables: Innovation proposals, trend reports, POCs, competitive intelligence
    - Style preference: Business insights (high-level), opinionated analysis, innovation opportunities
    - Goal: Spot innovation opportunities by tracking AI + media trends
    """

    prompt_used = build_enhanced_prompt(top_articles, user_context)

    print("DEBUG: Calling OpenAI for enhanced analysis...")
    try:
        ai_out = ask_openai(prompt_used)
    except Exception as e:
        raise RuntimeError(f"OpenAI request failed: {e}")

    subject, body = parse_subject_and_body(ai_out)

    # Create mobile TL;DR if enabled
    mobile_tldr = None
    if ENABLE_MOBILE_TLDR:
        print("DEBUG: Creating mobile TL;DR version...")
        mobile_tldr = create_mobile_tldr(ai_out, subject)

    if DRY_RUN:
        print("\n" + "="*80)
        print("DRY RUN - EMAIL PREVIEW")
        print("="*80)
        print(f"Subject: {subject}")
        print("="*80)
        if mobile_tldr:
            print("\n--- MOBILE TL;DR (Top of Email) ---")
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
