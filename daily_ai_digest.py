#!/usr/bin/env python3
"""
daily_ai_digest.py
Final production-ready script with debug prints and robust fetching.

Behavior:
- Fetches RSS feeds (requests + feedparser with User-Agent)
- Filters for AI-related items using KEYWORDS
- Builds a strict, no-hallucination prompt and calls OpenAI via OpenAI client
- Sends email via Gmail SMTP using an App Password (or previews via DRY_RUN)
- Emits debug logs (safe: does not print secret values)
"""

import os
import datetime
import feedparser
import requests
import smtplib
from email.message import EmailMessage
from typing import List, Dict, Optional
from openai import OpenAI
# from dotenv import load_dotenv

# # Load local .env for local testing (ignored in GH Actions)
# load_dotenv()

# ---------- Configuration from environment ----------
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")            # REQUIRED
OPENAI_BASE_URL = os.environ.get("OPENAI_BASE_URL")          # OPTIONAL (for custom endpoints)
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini") # default model

TO_EMAIL = os.environ.get("TO_EMAIL")                        # REQUIRED
FROM_EMAIL = os.environ.get("FROM_EMAIL")                    # REQUIRED (your Gmail address)
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD")    # REQUIRED (Gmail app password)

# curated default feeds (used if FEEDS env is empty)
DEFAULT_FEEDS = [
    "https://www.technologyreview.com/feed/",
    "https://www.theverge.com/rss/ai/index.xml",
    "https://venturebeat.com/category/ai/feed/",
    "https://techcrunch.com/tag/artificial-intelligence/feed/",
    "https://www.wired.com/feed/rss",
    "http://feeds.bbci.co.uk/news/technology/rss.xml",
    "https://rss.nytimes.com/services/xml/rss/nyt/Technology.xml",
    "https://www.reuters.com/technology/rss",
    "https://feeds.arstechnica.com/arstechnica/technology-lab",
    "https://spectrum.ieee.org/rss/robotics/artificial-intelligence",
]

FEEDS = os.environ.get("FEEDS") or ",".join(DEFAULT_FEEDS)     # comma-separated RSS feed URLs
# safe parse: empty or missing -> default 10
MAX_ARTICLES = int(os.environ.get("MAX_ARTICLES") or "10")
KEYWORDS = os.environ.get(
    "KEYWORDS",
    "ai,artificial intelligence,machine learning,llm,chatbot,deep learning,neural network,gen ai,genai"
).lower().split(",")
TIMEOUT_SECONDS = int(os.environ.get("HTTP_TIMEOUT") or "15")
DRY_RUN = os.environ.get("DRY_RUN", "false").lower() in ("1", "true", "yes")

# ---------- OpenAI client init (supports custom base url) ----------
# If OPENAI_API_KEY is None the client will fail later with a clear message
client = OpenAI(
    api_key=OPENAI_API_KEY,
    base_url=OPENAI_BASE_URL if OPENAI_BASE_URL else None
)

# ---------- Utility functions ----------
def fetch_from_feeds(feeds: List[str], max_items: int) -> List[Dict]:
    """
    Fetch feeds using requests (with a browser-like User-Agent) then parse with feedparser.
    Returns list of dicts with keys: source, title, description, url, publishedAt
    """
    items: List[Dict] = []
    headers = {"User-Agent": "Mozilla/5.0 (compatible; DailyAIDigest/1.0; +https://example.com)"}
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
            # prefer 'summary', then 'content', then 'description'
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

            link = (entry.get("link") or "").strip()
            published = entry.get("published", entry.get("published_parsed", ""))
            items.append({
                "source": source_title,
                "title": title,
                "description": summary,
                "url": link,
                "publishedAt": published
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
    # Call OpenAI via client
    resp = client.chat.completions.create(
        model=model_to_use,
        messages=[
            {"role": "system", "content": "You are a concise, factual tech journalist."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.0,
        max_tokens=900,
    )

    # Parse response (new-style objects)
    try:
        return resp.choices[0].message.content.strip()
    except Exception:
        try:
            return resp["choices"][0]["message"]["content"].strip()
        except Exception as e:
            raise RuntimeError(f"Unable to parse OpenAI response: {e}")

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
        raise SystemExit("OPENAI_API_KEY not set. Add it to GitHub Secrets or your .env for local testing.")

    # build feed list
    feed_list = [u.strip() for u in FEEDS.split(",") if u.strip()]

    raw_items = fetch_from_feeds(feed_list, max_items=MAX_ARTICLES)
    top_articles = select_top_items(raw_items, MAX_ARTICLES, KEYWORDS)

    # ---------------- DEBUG OUTPUT (safe: does not print secrets) ----------------
    print("DEBUG: feed_list count:", len(feed_list))
    for i, f in enumerate(feed_list[:12], 1):
        print(f"DEBUG: feed[{i}] = {f}")

    print("DEBUG: total raw items fetched:", len(raw_items))
    for i, it in enumerate(raw_items[:8], 1):
        print(f"DEBUG: raw[{i}] title:", (it.get('title') or '').strip()[:200])
        print("DEBUG: raw desc snippet:", (it.get('description') or '').strip()[:240].replace("\n", " "))

    print("DEBUG: top_articles count:", len(top_articles))
    for i, it in enumerate(top_articles[:8], 1):
        print(f"DEBUG: top[{i}] title:", (it.get('title') or '').strip()[:200])

    # ---------------- build prompt and preview ----------------
    if not top_articles:
        fallback_prompt = (
            "You are a factual tech journalist. No AI articles were detected in the provided RSS feeds today."
            " Provide a short neutral 3-sentence industry summary (no invented facts) and sign-off."
        )
        prompt_used = fallback_prompt
    else:
        prompt_used = build_prompt(top_articles)

    # print a prompt preview (safe)
    print("DEBUG: prompt preview (first 800 chars):")
    print(prompt_used[:800].replace("\n", "\\n"))

    # Call OpenAI
    try:
        ai_out = ask_openai(prompt_used)
    except Exception as e:
        # If OpenAI call fails, log error and exit with message
        raise RuntimeError(f"OpenAI request failed: {e}")

    subject, body = parse_subject_and_body(ai_out)

    if DRY_RUN:
        print("\n--- DRY RUN (email preview) ---")
        print("Subject:", subject)
        print(body)
        print("--- END PREVIEW ---\n")
    else:
        send_via_gmail(subject, body)
        print("Sent:", subject)

if __name__ == "__main__":
    main()
