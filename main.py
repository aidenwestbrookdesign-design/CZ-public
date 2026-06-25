import os
import json
import time
import re
import feedparser
import requests
from deep_translator import GoogleTranslator
from datetime import datetime, timezone

# ===== Config =====
TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHANNEL_ID = os.environ["TELEGRAM_CHANNEL_ID"]

# ===== RSS Sources =====
RSS_FEEDS = [
    ("CoinTelegraph",    "https://cointelegraph.com/rss"),
    ("CoinDesk",         "https://coindesk.com/arc/outboundfeeds/rss/"),
    ("Decrypt",          "https://decrypt.co/feed"),
    ("Bitcoin Magazine", "https://bitcoinmagazine.com/.rss/full/"),
]

# ===== Keywords =====
KEYWORDS = [
    "Bitcoin", "Ethereum", "SEC", "ETF", "Ripple", "Binance", "Solana",
    "crypto", "cryptocurrency", "regulation", "altcoin", "blockchain",
    "Coinbase", "Grayscale", "BTC", "ETH", "XRP", "USDT", "stablecoin",
    "DeFi", "NFT", "Web3", "halving", "mining", "wallet", "exchange",
]

BULLISH_WORDS = ["surge", "rally", "bullish", "gain", "rise", "soar", "pump",
                 "breakout", "ath", "all-time high", "recover", "approval"]
BEARISH_WORDS = ["crash", "drop", "bearish", "fall", "plunge", "dump", "ban",
                 "lawsuit", "hack", "scam", "fear", "loss", "decline", "sell-off"]

# ===== Tag Map (keyword → hashtags) =====
TAG_MAP = {
    "bitcoin":        ["#Bitcoin", "#BTC", "#ارز_دیجیتال", "#کریپتو"],
    "btc":            ["#Bitcoin", "#BTC", "#ارز_دیجیتال", "#کریپتو"],
    "ethereum":       ["#Ethereum", "#ETH", "#ارز_دیجیتال", "#کریپتو"],
    "eth":            ["#Ethereum", "#ETH", "#ارز_دیجیتال", "#کریپتو"],
    "binance":        ["#Binance", "#BNB", "#صرافی", "#کریپتو"],
    "bnb":            ["#BNB", "#Binance", "#صرافی", "#کریپتو"],
    "ripple":         ["#Ripple", "#XRP", "#ارز_دیجیتال", "#کریپتو"],
    "xrp":            ["#XRP", "#Ripple", "#ارز_دیجیتال", "#کریپتو"],
    "solana":         ["#Solana", "#SOL", "#ارز_دیجیتال", "#کریپتو"],
    "sol":            ["#SOL", "#Solana", "#ارز_دیجیتال", "#کریپتو"],
    "coinbase":       ["#Coinbase", "#صرافی", "#کریپتو", "#ارز_دیجیتال"],
    "grayscale":      ["#Grayscale", "#Bitcoin", "#ETF", "#کریپتو"],
    "sec":            ["#SEC", "#قانون_گذاری", "#کریپتو", "#ارز_دیجیتال"],
    "etf":            ["#ETF", "#Bitcoin", "#سرمایه_گذاری", "#کریپتو"],
    "defi":           ["#DeFi", "#امورمالی_غیرمتمرکز", "#Ethereum", "#کریپتو"],
    "nft":            ["#NFT", "#توکن_غیرمثلی", "#Ethereum", "#کریپتو"],
    "web3":           ["#Web3", "#بلاکچین", "#کریپتو", "#ارز_دیجیتال"],
    "blockchain":     ["#بلاکچین", "#Blockchain", "#کریپتو", "#ارز_دیجیتال"],
    "usdt":           ["#USDT", "#Tether", "#استیبل_کوین", "#کریپتو"],
    "stablecoin":     ["#استیبل_کوین", "#USDT", "#کریپتو", "#ارز_دیجیتال"],
    "halving":        ["#هاوینگ", "#Bitcoin", "#BTC", "#کریپتو"],
    "mining":         ["#ماینینگ", "#Mining", "#Bitcoin", "#کریپتو"],
    "regulation":     ["#قانون_گذاری", "#کریپتو", "#SEC", "#ارز_دیجیتال"],
    "hack":           ["#هک", "#امنیت", "#کریپتو", "#ارز_دیجیتال"],
    "altcoin":        ["#آلت_کوین", "#Altcoin", "#کریپتو", "#ارز_دیجیتال"],
    "crypto":         ["#کریپتو", "#ارز_دیجیتال", "#Crypto", "#بلاکچین"],
    "cryptocurrency": ["#ارز_دیجیتال", "#کریپتو", "#Crypto", "#بلاکچین"],
    "exchange":       ["#صرافی", "#Exchange", "#کریپتو", "#ارز_دیجیتال"],
    "wallet":         ["#کیف_پول", "#Wallet", "#کریپتو", "#ارز_دیجیتال"],
    "bullish":        ["#صعودی", "#Bullish", "#کریپتو", "#بازار"],
    "bearish":        ["#نزولی", "#Bearish", "#کریپتو", "#بازار"],
    "surge":          ["#صعودی", "#رشد", "#کریپتو", "#بازار"],
    "crash":          ["#نزولی", "#سقوط", "#کریپتو", "#بازار"],
    "etf approval":   ["#ETF", "#Bitcoin", "#SEC", "#سرمایه_گذاری"],
}

POSTED_FILE = "posted_urls.json"
MAX_SUMMARY_LENGTH = 200


def clean_html(text):
    text = re.sub(r"<[^>]+>", "", text or "")
    text = re.sub(r"&[a-zA-Z]+;", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

def truncate(text, max_len):
    if len(text) <= max_len:
        return text
    return text[:max_len].rsplit(" ", 1)[0] + "…"

def is_important(title):
    title_lower = title.lower()
    for kw in KEYWORDS:
        if re.search(r'\b' + re.escape(kw.lower()) + r'\b', title_lower):
            return True
    return False

def get_sentiment_emoji(title):
    title_lower = title.lower()
    bullish = any(w in title_lower for w in BULLISH_WORDS)
    bearish = any(w in title_lower for w in BEARISH_WORDS)
    if bullish and not bearish:
        return "🟢"
    if bearish and not bullish:
        return "🔴"
    return "⚪️"

def get_tags(title, summary=""):
    """Pick top 5 unique hashtags based on title and summary keywords."""
    text = (title + " " + summary).lower()
    collected = []
    seen = set()

    for keyword, tags in TAG_MAP.items():
        if keyword in text:
            for tag in tags:
                if tag not in seen:
                    seen.add(tag)
                    collected.append(tag)

    # Always include #کریپتو and #ارز_دیجیتال as fallback
    for fallback in ["#کریپتو", "#ارز_دیجیتال"]:
        if fallback not in seen:
            collected.append(fallback)

    return collected[:5]

def translate(text):
    if not text:
        return ""
    text = truncate(text, 400)
    for attempt in range(3):
        try:
            result = GoogleTranslator(source='en', target='fa').translate(text)
            return result or ""
        except Exception as e:
            print(f"Translation attempt {attempt+1} failed:", e)
            time.sleep(2)
    return ""

def send_to_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHANNEL_ID,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }
    for attempt in range(3):
        try:
            response = requests.post(url, data=payload, timeout=10)
            if response.status_code == 200:
                return True
            print(f"Telegram error ({response.status_code}):", response.text)
        except Exception as e:
            print(f"Telegram attempt {attempt+1} failed:", e)
        time.sleep(2)
    return False

def load_posted():
    if os.path.exists(POSTED_FILE):
        with open(POSTED_FILE, "r") as f:
            return set(json.load(f))
    return set()

def save_posted(posted):
    with open(POSTED_FILE, "w") as f:
        json.dump(list(posted)[-1000:], f)

def fetch_news():
    articles = []
    for source_name, feed_url in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:10]:
                title   = clean_html(entry.get("title", "")).strip()
                summary = clean_html(entry.get("summary", "")).strip()
                url     = entry.get("link", "").strip()
                if title and url:
                    articles.append({
                        "source":  source_name,
                        "title":   title,
                        "summary": truncate(summary, MAX_SUMMARY_LENGTH),
                        "url":     url,
                    })
        except Exception as e:
            print(f"RSS fetch error ({source_name}):", e)
    return articles

def format_message(article, fa_title, fa_summary):
    sentiment = get_sentiment_emoji(article["title"])
    tags      = get_tags(article["title"], article["summary"])
    tags_line = " ".join(tags)

    lines = [
        f"{sentiment} <b>{fa_title}</b>",
        "",
        f"📝 {fa_summary}" if fa_summary else "",
        "",
        f"📰 منبع: {article['source']}",
        f'🔗 <a href="{article["url"]}">مطالعه کامل خبر</a>',
        "",
        tags_line,
        "",
        "━━━━━━━━━━━━━━━",
        "👥 @Crypto_Zone360 | به ما بپیوندید 🦈",
    ]
    return "\n".join(line for line in lines if line is not None)

def main():
    now = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
    print(f"🚀 Bot started — {now}")

    posted   = load_posted()
    articles = fetch_news()
    print(f"📥 Fetched {len(articles)} articles")

    sent = 0
    for article in articles:
        url   = article["url"]
        title = article["title"]

        if url in posted:
            continue
        if not is_important(title):
            continue

        print(f"📌 [{article['source']}] {title}")

        fa_title   = translate(title)
        fa_summary = translate(article["summary"])

        if not fa_title:
            print("⚠️ Skipping — translation failed")
            continue

        message = format_message(article, fa_title, fa_summary)
        if send_to_telegram(message):
            posted.add(url)
            sent += 1
            time.sleep(3)

    save_posted(posted)
    print(f"✅ Done — {sent} new articles posted.")

if __name__ == "__main__":
    main()
