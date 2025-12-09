#!/usr/bin/env python3
"""
daily_ai_digest_clean.py
Cleaned, production-ready RSS-only daily AI digest.
- dotenv support
- OpenAI client with BASE_URL + MODEL env support
- Robust response parsing
- Expanded, trusted default RSS FEEDS (override via FEEDS env)
- Dry-run mode to preview email locally without sending
- Gmail SMTP (App Password) sending; can swap to SendGrid if preferred
"""

import os
import datetime
import feedparser
import openai
import smtplib
from email.message import EmailMessage
from typing import List, Dict, Optional
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# ---------- Configuration from environment ----------
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")            # REQUIRED
OPENAI_BASE_URL = os.environ.get("OPENAI_BASE_URL")          # OPTIONAL (for custom endpoints)
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4.1-mini")

TO_EMAIL = os.environ.get("TO_EMAIL")                        # REQUIRED
FROM_EMAIL = os.environ.get("FROM_EMAIL")                    # REQUIRED (your Gmail address)
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD")    # REQUIRED (Gmail app password)

# If FEEDS env is not set, use a curated list of reliable, well-known tech & AI feeds
DEFAULT_FEEDS = [
    "https://www.technologyreview.com/feed/",  # MIT Technology Review
    "https://www.theverge.com/rss/ai/index.xml",  # The Verge - AI
    "https://venturebeat.com/category/ai/feed/",  # VentureBeat - AI
    "https://techcrunch.com/tag/artificial-intelligence/feed/",  # TechCrunch - AI
    "https://www.wired.com/feed/rss",  # Wired
    "http://feeds.bbci.co.uk/news/technology/rss.xml",  # BBC Technology
    "https://rss.nytimes.com/services/xml/rss/nyt/Technology.xml",  # NYTimes Technology
    "https://www.reuters.com/technology/rss",  # Reuters Technology
    "https://feeds.arstechnica.com/arstechnica/technology-lab",  # Ars Technica - Tech
    "https://spectrum.ieee.org/rss/robotics/artificial-intelligence",  # IEEE Spectrum - AI (category)
]

FEEDS = os.environ.get("FEEDS", ",".join(DEFAULT_FEEDS))                          # comma-separated RSS feed URLs
MAX_ARTICLES = int(os.environ.get("MAX_ARTICLES", "10"))      # default max items to include

KEYWORDS = os.environ.get(
    "KEYWORDS",
    "ai,artificial intelligence,machine learning,llm,chatbot,deep learning,neural network,gen ai,genai"
).lower().split(",")

TIMEOUT_SECONDS = int(os.environ.get("HTTP_TIMEOUT", "15"))
DRY_RUN = os.environ.get("DRY_RUN", "false").lower() in ("1", "true", "yes")

# ---------- OpenAI client init (supports custom base url) ----------
client = OpenAI(
    api_key=OPENAI_API_KEY,
    base_url=OPENAI_BASE_URL if OPENAI_BASE_URL else None,
)

# ---------- Utility functions ----------
def fetch_from_feeds(feeds: List[str], max_items: int) -> List[Dict]:
    items: List[Dict] = []
    for url in feeds:
        try:
            d = feedparser.parse(url)
        except Exception:
            continue
        for entry in d.entries:
            title = entry.get("title", "").strip()
            summary = entry.get("summary", entry.get("description", "")).strip()
            link = entry.get("link", "").strip()
            published = entry.get("published", entry.get("published_parsed", ""))
            items.append({
                "source": d.feed.get("title", "") or url,
                "title": title,
                "description": summary,
                "url": link,
                "publishedAt": published,
            })
            if len(items) >= max_items * 3:
                break
        if len(items) >= max_items * 3:
            break
    return items


def is_ai_related(item: Dict, keywords: List[str]) -> bool:
    text = (item.get("title", "") + " " + item.get("description", "")).lower()
    for k in keywords:
        if k.strip() and k.strip().lower() in text:
            return True
    return False


def select_top_items(items: List[Dict], max_items: int, keywords: List[str]) -> List[Dict]:
    filtered = [it for it in items if is_ai_related(it, keywords)]
    seen = set()
    unique: List[Dict] = []
    for it in filtered:
        key = (it.get("url") or it.get("title") or "").strip()
        if not key or key in seen:
            continue
        seen.add(key)
        unique.append(it)
        if len(unique) >= max_items:
            break
    return unique


def build_prompt(articles: List[Dict]) -> str:
    now_iso = datetime.datetime.now().strftime("%Y-%m-%d %H:%M IST")
    prompt = (
        "You are an objective, factual tech journalist. You WILL ONLY use the information"
        " provided below (title, description, url, publishedAt, source). DO NOT invent"
        " facts, numbers, quotes, or events. If the description lacks detail, say"
        " 'No further details available.' Do not speculate. Keep each story summary to 1 sentence."
        "\n\nFormat the output exactly as follows:\n"
        "Subject: <short subject line (<=8 words)>\n\n"
        "Body:\n- 2-3 bullet highlights (each 1 sentence)\n\n"
        "Summary:\n<two short paragraphs (total 4-6 sentences)>\n\n"
        "Top stories:\n[1] Title (Source) - 1-sentence summary. Link: <url>\n[2] ...\n\n"
        "Why it matters:\n<one or two sentences>\n\n"
        "Sign-off:\n<one short friendly line>\n\n"
        f"Date: {now_iso}\n\n"
        "Articles (most recent first):\n"
    )
    for i, a in enumerate(articles, 1):
        prompt += (
            f"\n[{i}] Title: {a.get('title')}\n"
            f"Source: {a.get('source')}\n"
            f"PublishedAt: {a.get('publishedAt')}\n"
            f"URL: {a.get('url')}\n"
            f"Desc: {a.get('description')}\n"
        )
    prompt += "\n\nWrite the email now following the format exactly. No extra sections. Be concise."
    return prompt


def ask_openai(prompt: str, model: Optional[str] = None) -> str:
    model_to_use = model or OPENAI_MODEL
    # Use the client.chat.completions.create API and parse reliably
    resp = client.chat.completions.create(
        model=model_to_use,
        messages=[
            {"role": "system", "content": "You are a concise, factual tech journalist."},
            {"role": "user", "content": prompt},
        ],
    )

    # New-style response objects expose choices[].message.content
    try:
        return resp.choices[0].message.content.strip()
    except Exception:
        # Fallback to dict-like access if needed
        try:
            return resp["choices"][0]["message"]["content"].strip()
        except Exception:
            raise RuntimeError("Unable to parse OpenAI response; inspect raw response")


def parse_subject_and_body(ai_text: str):
    lines = ai_text.splitlines()
    subject = "Daily AI Digest"
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


def send_via_gmail(subject: str, body: str):
    if not (FROM_EMAIL and TO_EMAIL and GMAIL_APP_PASSWORD):
        raise ValueError("Missing FROM_EMAIL / TO_EMAIL / GMAIL_APP_PASSWORD env vars")
    msg = EmailMessage()
    msg["From"] = FROM_EMAIL
    msg["To"] = TO_EMAIL
    msg["Subject"] = subject
    msg.set_content(body)
    msg.add_alternative("<pre>" + (body.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")) + "</pre>", subtype="html")

    with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=30) as smtp:
        try:
            smtp.login(FROM_EMAIL, GMAIL_APP_PASSWORD)
            smtp.send_message(msg)
        except smtplib.SMTPAuthenticationError as e:
            raise RuntimeError(
                "SMTPAuthenticationError: Gmail rejected the credentials. "
                "Check App Password, ensure 2FA is ON, FROM_EMAIL matches the account, "
                "and remove quotes/spaces from the secret. Original: " + str(e)
            )


# ---------- Main flow ----------
def main():
    if not OPENAI_API_KEY:
        raise SystemExit("OPENAI_API_KEY not set.")

    feed_list = [u.strip() for u in FEEDS.split(",") if u.strip()]
    raw_items = fetch_from_feeds(feed_list, max_items=MAX_ARTICLES)
    top_articles = select_top_items(raw_items, MAX_ARTICLES, KEYWORDS)

    if not top_articles:
        fallback_prompt = (
            "You are a factual tech journalist. No AI articles were detected in the provided RSS feeds today."
            " Provide a short neutral 3-sentence industry summary (no invented facts) and sign-off."
        )
        ai_out = ask_openai(fallback_prompt)
    else:
        prompt = build_prompt(top_articles)
        ai_out = ask_openai(prompt)

    subject, body = parse_subject_and_body(ai_out)

    if DRY_RUN:
        print("--- DRY RUN (email preview) ---")
        print("Subject:", subject)
        print(body)
        print("--- END PREVIEW ---")
    else:
        send_via_gmail(subject, body)
        print("Sent:", subject)


if __name__ == "__main__":
    main()
