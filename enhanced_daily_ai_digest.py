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
# Organized by category for diversity and freshness
FEED_CATEGORIES = {
    # ── AI-dedicated newsletters & blogs (highest signal) ──────────────────
    "ai_newsletters_primary": [
        "https://www.deeplearning.ai/the-batch/feed/",       # Andrew Ng's The Batch
        "https://importai.substack.com/feed",                # Import AI – Jack Clark
        "https://bensbites.beehiiv.com/feed",                # Ben's Bites
        "https://www.aisnakeoil.com/feed",                   # AI Snake Oil
        "https://www.oneusefulthing.org/feed",               # Ethan Mollick / wharton
        "https://thegradient.pub/rss/",                      # The Gradient
        "https://simonwillison.net/atom/everything/",        # Simon Willison – LLMs
        "https://lilianweng.github.io/index.xml",            # Lilian Weng (OpenAI)
        "https://magazine.sebastianraschka.com/feed",        # Sebastian Raschka
        "https://www.interconnects.ai/feed",                 # Nathan Lambert – RLHF/alignment
    ],
    # ── AI lab / company official blogs ────────────────────────────────────
    "ai_labs": [
        "https://openai.com/blog/rss/",
        "https://www.anthropic.com/rss.xml",
        "https://blog.google/technology/ai/rss/",
        "https://deepmind.google/blog/feed/basic/",
        "https://ai.meta.com/blog/rss/",
        "https://mistral.ai/news/rss.xml",
        "https://cohere.com/blog/rss/",
        "https://www.together.ai/blog/rss.xml",
        "https://www.microsoft.com/en-us/research/feed/",
        "https://blogs.nvidia.com/feed/",
    ],
    # ── Top AI-focused news sites ───────────────────────────────────────────
    "ai_news_sites": [
        "https://www.technologyreview.com/feed/",
        "https://www.artificialintelligence-news.com/feed/",
        "https://www.marktechpost.com/feed/",
        "https://syncedreview.com/feed/",
        "https://www.unite.ai/feed/",
        "https://404media.co/rss/",                          # Indie, great AI coverage
    ],
    # ── Major tech media with strong AI sections ────────────────────────────
    "major_tech_news": [
        "https://www.theverge.com/rss/ai/index.xml",
        "https://techcrunch.com/tag/artificial-intelligence/feed/",
        "https://www.wired.com/feed/tag/ai/latest/rss",
        "https://arstechnica.com/tag/artificial-intelligence/feed/",
        "https://www.zdnet.com/topic/artificial-intelligence/rss.xml",
    ],
    # ── Business & financial press ──────────────────────────────────────────
    "business_analysis": [
        "https://fortune.com/section/artificial-intelligence/feed/",
        "https://www.cnbc.com/id/19854910/device/rss/rss.html",
        "https://news.crunchbase.com/feed/",
        "https://techcrunch.com/tag/venture-capital/feed/",
    ],
    # ── Open-source / developer community ──────────────────────────────────
    "open_source_community": [
        "https://huggingface.co/blog/feed.xml",
        "https://github.blog/category/ai-and-ml/feed/",
        "https://pytorch.org/blog/feed.xml",
        "https://news.ycombinator.com/rss",
        "https://www.reddit.com/r/MachineLearning/.rss",
        "https://dev.to/feed/tag/ai",
    ],
    # ── Research / academic ─────────────────────────────────────────────────
    "research_academic": [
        "https://arxiv.org/rss/cs.AI",                       # arXiv AI papers
        "https://arxiv.org/rss/cs.LG",                       # arXiv ML papers
        "https://paperswithcode.com/latest/feed",
    ],
    # ── Broad global tech news ──────────────────────────────────────────────
    "news_general": [
        "https://feeds.bbci.co.uk/news/technology/rss.xml",
        "https://rss.nytimes.com/services/xml/rss/nyt/Technology.xml",
        "https://www.reuters.com/technology/artificial-intelligence/rss",
        "https://www.theguardian.com/technology/artificialintelligenceai/rss",
    ],
    # ── India / Asia coverage ───────────────────────────────────────────────
    "asia_india": [
        "https://timesofindia.indiatimes.com/rssfeeds/66949542.cms",
        "https://economictimes.indiatimes.com/tech/rssfeeds/13357270.cms",
        "https://www.thehindu.com/sci-tech/technology/feeder/default.rss",
    ],
    # ── Media / Streaming (applications context) ───────────────────────────
    "streaming_media": [
        "https://variety.com/feed/",
        "https://www.hollywoodreporter.com/feed/",
        "https://digiday.com/feed/",
        "https://www.tubefilter.com/feed/",
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

# Organization-level ideation (strategic innovation ideas)
ENABLE_IDEATION = os.environ.get("ENABLE_IDEATION", "true").lower() in ("1", "true", "yes")

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

FORMAT YOUR OUTPUT FOR EMAIL (use simple formatting that renders well in email clients):

Subject: [Create an engaging subject line that captures the biggest theme/trend of the day, max 10 words]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 TOP INSIGHT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[2-3 sentences: What's the most important pattern or trend today? Connect multiple stories if relevant. Be opinionated.]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔑 KEY THEMES TODAY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

• [Theme 1]: Brief insight
• [Theme 2]: Brief insight
• [Theme 3]: Brief insight

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📰 DETAILED STORIES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[For each story, write in this format:]

─────────────────────────────────────────
[Number]. [ENGAGING TITLE IN CAPS]
─────────────────────────────────────────
Source: [Source name] | When: [Timeframe like "Today" or "Yesterday"]

[2-3 engaging paragraphs that include:
- What happened (specific facts, numbers, quotes)
- Why it matters (analysis and implications)
- What's interesting or surprising about it
- Any connections to other trends or stories]

🔗 Link: [URL]
💡 Innovation angle: [1 sentence: What could innovation teams learn or do with this?]

[Repeat for each story]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📌 BOTTOM LINE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[2-3 sentences: Final thought about what all this means. What should readers be thinking about? Any predictions or questions to ponder?]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
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
- Follow the email format EXACTLY as specified above (use emojis, unicode lines, and simple text formatting)
- Do NOT use markdown syntax like ** or ## or ### (use plain text with emojis instead)

Write the digest now:"""

    return prompt


def build_ideation_prompt(articles: List[Dict]) -> str:
    """
    Build prompt for organization-level strategic ideation
    Focus: Strategic initiatives requiring cross-functional teams and executive approval
    """
    now_iso = datetime.datetime.now().strftime("%Y-%m-%d %H:%M IST")

    prompt = f"""You are a strategic innovation consultant working for a media/entertainment organization (streaming platforms, content production, distribution). Your role is to transform news and trends into ORGANIZATION-LEVEL strategic initiatives.

YOUR MISSION: Generate 3-5 actionable strategic opportunities that:
1. Require organizational resources (cross-functional teams, budget, executive approval)
2. Create competitive advantages or address market opportunities
3. Drive business impact (revenue growth, cost reduction, market positioning)
4. Are implementable within 6-12 months with proper investment
5. Are specific to media/entertainment business models

CRITICAL FOCUS - ORGANIZATION LEVEL:
✅ Strategic initiatives requiring multiple departments (product, engineering, content, business)
✅ Platform/infrastructure investments that benefit the entire organization
✅ New product features or business models
✅ Competitive positioning moves
✅ Partnership strategies with technology vendors or content creators
✅ Market expansion or audience growth initiatives
✅ Operational efficiency improvements at scale
✅ Organizational capability building (new tech stacks, AI teams, data platforms)

❌ AVOID PERSONAL-LEVEL IDEAS:
❌ Individual productivity tips or tool recommendations
❌ Single-person tasks or small workflow improvements
❌ Personal skill development suggestions
❌ Minor feature tweaks that don't require cross-team coordination

MEDIA/ENTERTAINMENT BUSINESS CONTEXT:
- Revenue models: Subscriptions, advertising, pay-per-view, licensing
- Key metrics: Subscriber growth, engagement (watch time), churn reduction, content ROI
- Competitive landscape: Streaming wars, creator economy, AI-powered personalization
- Technology areas: Content recommendation, personalization, production efficiency, distribution, monetization
- Content types: Video (series, films, live), audio (music, podcasts), interactive content
- Audience segments: Demographics, genres, viewing behaviors, device preferences

FORMAT YOUR OUTPUT FOR EMAIL (use simple formatting that renders well in email clients):

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💡 STRATEGIC INNOVATION IDEAS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎯 STRATEGIC OPPORTUNITIES

[For each of 3-4 ideas, use this format:]

─────────────────────────────────────────
[NUMBER]. [INITIATIVE NAME IN CAPS]
[One-line value proposition]
─────────────────────────────────────────

📊 Business Context: [What trend/news sparked this opportunity? Why does it matter to the organization now?]

🚀 Strategic Initiative: [Describe the organization-level initiative in 2-3 sentences. What are we building/launching/changing? Who needs to be involved? What's the scope?]

💰 Business Impact:
  • Revenue/Growth: [How does this drive business results?]
  • Competitive Position: [How does this differentiate us or defend market share?]
  • Operational Benefit: [Any cost savings or efficiency gains?]

📅 Implementation Approach:
  • Phase 1 (Months 1-3): [Initial steps, team formation, pilot scope]
  • Phase 2 (Months 4-6): [Scale-up, integration, measurement]
  • Phase 3 (Months 7-12): [Full rollout, optimization]

👥 Cross-Functional Requirements:
  • Teams Needed: [Product, Engineering, Content, Data Science, Business Development, etc.]
  • Technology Stack: [Key technologies or vendors to evaluate]
  • Investment Level: [Rough estimate - Small/Medium/Large]

📈 Success Metrics: [2-3 measurable KPIs to track]


🧪 EXPERIMENTAL INITIATIVES (Quick Wins)

[2-3 smaller-scale experiments that can validate concepts quickly]
• [Experiment Name]: [1-2 sentence description] | Timeline: [weeks] | Team: [which department leads]


🤝 PARTNERSHIP & ECOSYSTEM OPPORTUNITIES

[1-2 strategic partnerships or vendor evaluations]
• [Partner Type]: [What kind of partnership and why it's strategic]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

TODAY'S NEWS ARTICLES (Use these to generate ideas):

"""

    for i, article in enumerate(articles, 1):
        prompt += f"""
[{i}] Title: {article.get('title')}
Source: {article.get('source')}
Published: {article.get('publishedAt')}
Description: {article.get('description')}
Relevance Score: {article.get('score', 0):.2f}

"""

    prompt += f"""
IMPORTANT GUIDELINES:
- Every idea must be STRATEGIC and ORGANIZATION-LEVEL (not personal productivity)
- Include specific business metrics and competitive context
- Make initiatives concrete enough to present to leadership
- Connect ideas directly to the news/trends provided above
- Focus on media/entertainment business applications
- Think about what would require a project team, budget approval, and 6-12 months to execute
- Ensure cross-functional collaboration is necessary
- Follow the email format EXACTLY as specified above (use emojis, unicode lines, and simple text formatting)
- Do NOT use markdown syntax like ** or ## or ### (use plain text with emojis and bullet points instead)

Generated: {now_iso}

Write the strategic ideation now:"""

    return prompt


def generate_innovation_ideas(articles: List[Dict]) -> str:
    """
    Generate organization-level strategic innovation ideas
    Returns formatted ideation section to append to digest
    """
    print("DEBUG: Generating organization-level strategic ideation...")

    ideation_prompt = build_ideation_prompt(articles)

    try:
        ideation_output = ask_openai(ideation_prompt)
        print("DEBUG: Successfully generated strategic ideation")
        return "\n\n" + ideation_output
    except Exception as e:
        print(f"WARNING: Ideation generation failed: {e}")
        return ""  # Fail gracefully - don't break the digest


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
            if line.startswith('━') or line.startswith('===') or line.startswith('##') or line.startswith('🔑'):
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
            elif line.startswith('━') or line.startswith('===') or line.startswith('📰'):
                break

    # Extract story titles only
    mobile_content.append("\n\n📰 STORIES (Tap for full digest):")
    story_count = 0
    in_stories = False
    for i, line in enumerate(lines):
        # Detect when we're in the DETAILED STORIES section
        if "DETAILED STORIES" in line.upper():
            in_stories = True
            continue

        # Look for story titles (lines that start with number followed by period)
        if in_stories and line.strip() and not line.startswith('─') and not line.startswith('━'):
            # Check if line starts with a number followed by period (e.g., "1. TITLE" or "2. TITLE")
            stripped = line.strip()
            if stripped and stripped[0].isdigit() and '. ' in stripped:
                # Extract just the title
                title = stripped.split('. ', 1)[1] if len(stripped.split('. ', 1)) > 1 else stripped
                mobile_content.append(f"  {story_count + 1}. {title[:60]}...")
                story_count += 1
                if story_count >= 5:  # Show max 5 stories in TL;DR
                    break
            # Stop if we hit the ideation or bottom line section
            elif "INNOVATION IDEAS" in stripped or "BOTTOM LINE" in stripped:
                break

    mobile_content.append(f"\n\n📖 {story_count}+ stories in full digest below")
    mobile_content.append("⏱️  3-min scan | Full read: 10-15 min")
    mobile_content.append("\n" + "="*50 + "\n")

    return "\n".join(mobile_content)


def save_digest_data(subject: str, body: str, digests_dir: str = "digests"):
    """Save digest to JSON file and update manifest for web viewer"""
    import json
    os.makedirs(digests_dir, exist_ok=True)

    date_str = datetime.datetime.now().strftime("%Y-%m-%d")
    digest_file = os.path.join(digests_dir, f"{date_str}.json")

    with open(digest_file, "w", encoding="utf-8") as f:
        json.dump({"date": date_str, "subject": subject, "body": body}, f, ensure_ascii=False, indent=2)

    manifest_file = os.path.join(digests_dir, "manifest.json")
    try:
        with open(manifest_file, "r", encoding="utf-8") as f:
            manifest = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        manifest = []

    # Remove existing entry for today if re-running
    manifest = [e for e in manifest if e.get("date") != date_str]
    manifest.append({"date": date_str, "subject": subject})
    manifest.sort(key=lambda e: e["date"], reverse=True)

    with open(manifest_file, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    print(f"DEBUG: Saved digest to {digest_file}")


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


def _esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _render_section_header(header: str) -> str:
    """Style a section header div based on its emoji/keyword."""
    h = header.upper()
    if "TOP INSIGHT" in h or "🎯" in header:
        bg, border = "#1e3a8a", "#3b82f6"
    elif "KEY THEMES" in h or "🔑" in header:
        bg, border = "#1e40af", "#60a5fa"
    elif "DETAILED STORIES" in h or "📰" in header:
        bg, border = "#1d4ed8", "#93c5fd"
    elif "BOTTOM LINE" in h or "📌" in header:
        bg, border = "#1e3a8a", "#3b82f6"
    elif any(x in h for x in ("STRATEGIC", "INNOVATION", "IDEATION")) or "💡" in header:
        bg, border = "#4c1d95", "#a78bfa"
    else:
        bg, border = "#374151", "#9ca3af"
    return (
        f'<div style="background:{bg};border-left:4px solid {border};'
        f'color:white;padding:12px 18px;border-radius:6px;'
        f'margin:28px 0 10px 0;font-size:15px;font-weight:700;'
        f'letter-spacing:.3px;">{_esc(header)}</div>'
    )


def convert_text_to_html_email(body: str, subject: str, mobile_tldr: Optional[str] = None) -> str:
    """
    Convert the AI-generated plain-text digest into a clean, newsletter-style
    HTML email.  Parses the ━━━/─── section structure and applies CSS styling.
    """
    now_str = datetime.datetime.now().strftime("%B %d, %Y")

    def parse_body(text: str) -> str:
        lines = text.split("\n")
        out = []
        i = 0
        while i < len(lines):
            raw = lines[i]
            stripped = raw.strip()

            # ── Major section separator + header + separator ────────────────
            if re.match(r"^━{5,}", stripped):
                i += 1
                if i < len(lines):
                    header = lines[i].strip()
                    i += 1
                    # consume closing separator if present
                    if i < len(lines) and re.match(r"^━{5,}", lines[i].strip()):
                        i += 1
                    if header:
                        out.append(_render_section_header(header))
                continue

            # ── Story sub-divider ─────────────────────────── ───────────────
            if re.match(r"^─{5,}", stripped):
                i += 1
                if i < len(lines):
                    story_title = lines[i].strip()
                    i += 1
                    # consume closing ─── if present
                    if i < len(lines) and re.match(r"^─{5,}", lines[i].strip()):
                        i += 1
                    if story_title:
                        out.append(
                            f'<div style="margin-top:22px;padding:12px 16px;'
                            f'background:#f8fafc;border-left:3px solid #2563eb;'
                            f'border-radius:0 6px 6px 0;">'
                            f'<p style="margin:0;font-size:16px;font-weight:700;'
                            f'color:#1e3a8a;">{_esc(story_title)}</p></div>'
                        )
                continue

            # ── Source/meta line ────────────────────────────────────────────
            if stripped.startswith("Source:"):
                out.append(
                    f'<p style="margin:4px 0 6px;font-size:12px;'
                    f'color:#6b7280;font-style:italic;">{_esc(stripped)}</p>'
                )
                i += 1
                continue

            # ── Link line ───────────────────────────────────────────────────
            if stripped.startswith("🔗"):
                url_m = re.search(r"(https?://\S+)", stripped)
                if url_m:
                    url = url_m.group(1).rstrip(".,)")
                    out.append(
                        f'<p style="margin:8px 0 4px;">'
                        f'<a href="{_esc(url)}" style="display:inline-block;'
                        f'background:#2563eb;color:white;text-decoration:none;'
                        f'padding:6px 16px;border-radius:4px;font-size:13px;'
                        f'font-weight:600;">Read Article →</a></p>'
                    )
                else:
                    out.append(f'<p style="margin:6px 0;">{_esc(stripped)}</p>')
                i += 1
                continue

            # ── Innovation angle ────────────────────────────────────────────
            if stripped.startswith("💡"):
                content = re.sub(r"^💡\s*(Innovation angle:)?\s*", "", stripped, flags=re.I)
                out.append(
                    f'<div style="background:#f0fdf4;border-left:3px solid #059669;'
                    f'padding:8px 14px;margin:8px 0;border-radius:0 5px 5px 0;'
                    f'font-size:13px;color:#065f46;">'
                    f'<strong>💡 Innovation:</strong> {_esc(content)}</div>'
                )
                i += 1
                continue

            # ── Bullet points ───────────────────────────────────────────────
            if stripped.startswith("•") or stripped.startswith("▸"):
                content = stripped.lstrip("•▸").strip()
                out.append(
                    f'<p style="margin:5px 0 5px 18px;position:relative;">'
                    f'<span style="position:absolute;left:-16px;color:#2563eb;'
                    f'font-weight:700;">▸</span>{_esc(content)}</p>'
                )
                i += 1
                continue

            # ── Empty line ──────────────────────────────────────────────────
            if not stripped:
                out.append('<div style="height:6px;"></div>')
                i += 1
                continue

            # ── Regular paragraph ───────────────────────────────────────────
            out.append(
                f'<p style="margin:7px 0;line-height:1.7;color:#374151;">'
                f'{_esc(stripped)}</p>'
            )
            i += 1

        return "\n".join(out)

    # ── Mobile TL;DR banner ─────────────────────────────────────────────────
    mobile_html = ""
    if mobile_tldr:
        tldr_lines = []
        for ln in mobile_tldr.split("\n"):
            s = ln.strip()
            if not s:
                continue
            if "=" * 8 in s or "─" * 8 in s:
                tldr_lines.append('<hr style="border:none;border-top:1px solid #bfdbfe;margin:6px 0;">')
            elif s.startswith("•") or s.startswith("  "):
                tldr_lines.append(f'<p style="margin:3px 0 3px 14px;font-size:13px;">{_esc(s)}</p>')
            else:
                tldr_lines.append(f'<p style="margin:4px 0;font-size:13px;font-weight:600;">{_esc(s)}</p>')
        mobile_html = (
            '<div style="background:#eff6ff;border:1px solid #bfdbfe;'
            'border-radius:8px;padding:16px 18px;margin-bottom:24px;">'
            '<p style="margin:0 0 8px;font-weight:700;font-size:14px;color:#1d4ed8;">'
            '📱 QUICK SCAN — TL;DR</p>'
            + "\n".join(tldr_lines)
            + "</div>"
        )

    body_html = parse_body(body)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1.0">
  <title>{_esc(subject)}</title>
</head>
<body style="margin:0;padding:0;background:#f1f5f9;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,'Helvetica Neue',Arial,sans-serif;">
<div style="max-width:680px;margin:0 auto;padding:24px 16px;">

  <!-- Header -->
  <div style="background:linear-gradient(135deg,#1e3a8a 0%,#1d4ed8 60%,#2563eb 100%);border-radius:12px 12px 0 0;padding:32px 30px 24px;text-align:center;">
    <p style="margin:0 0 8px;color:#93c5fd;font-size:11px;text-transform:uppercase;letter-spacing:2px;font-weight:600;">AI + Media Intelligence</p>
    <h1 style="margin:0 0 10px;color:white;font-size:22px;font-weight:800;line-height:1.35;">{_esc(subject)}</h1>
    <p style="margin:0;color:#bfdbfe;font-size:13px;">{now_str}</p>
  </div>

  <!-- Body card -->
  <div style="background:white;border-radius:0 0 12px 12px;padding:28px 30px 32px;box-shadow:0 4px 16px rgba(0,0,0,.08);">

    {mobile_html}

    {body_html}

    <!-- Footer -->
    <div style="margin-top:36px;padding-top:20px;border-top:1px solid #e5e7eb;text-align:center;">
      <p style="margin:0;color:#9ca3af;font-size:11px;letter-spacing:.5px;">
        DAILY AI DIGEST &nbsp;·&nbsp; Powered by OpenAI &amp; RSS
      </p>
    </div>
  </div>

</div>
</body>
</html>"""


def send_via_gmail(subject: str, body: str, mobile_tldr: Optional[str] = None):
    """Send email via Gmail SMTP with rich HTML and plain-text fallback."""
    if not (FROM_EMAIL and TO_EMAIL and GMAIL_APP_PASSWORD):
        raise ValueError("Missing FROM_EMAIL / TO_EMAIL / GMAIL_APP_PASSWORD env vars")

    msg = EmailMessage()
    msg["From"] = FROM_EMAIL
    msg["To"] = TO_EMAIL
    msg["Subject"] = subject

    # Plain-text fallback
    plain_text = (mobile_tldr + "\n\n" + body) if mobile_tldr else body
    msg.set_content(plain_text)

    # Beautiful HTML version
    html_body = convert_text_to_html_email(body, subject, mobile_tldr)
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

    # Generate organization-level strategic ideation if enabled
    if ENABLE_IDEATION:
        print("DEBUG: Generating organization-level strategic ideation...")
        ideation_section = generate_innovation_ideas(top_articles)
        if ideation_section:
            body = body + ideation_section
            print("DEBUG: Strategic ideation appended to digest")

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
            save_digest_data(subject, body)
        except Exception as e:
            error_msg = f"FAILED: {str(e)[:100]}"
            print(f"ERROR: Failed to send email: {e}")
            log_email_send(subject, error_msg)
            raise


if __name__ == "__main__":
    main()
