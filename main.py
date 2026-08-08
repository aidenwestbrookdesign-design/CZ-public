import os
import json
import time
import re
import random
import feedparser
import requests
from deep_translator import GoogleTranslator
from datetime import datetime, timezone

# ===== Config =====
TELEGRAM_BOT_TOKEN  = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHANNEL_ID = os.environ["TELEGRAM_CHANNEL_ID"]

MAX_POSTS_PER_RUN = 5

# ===== RSS Sources =====
RSS_FEEDS = [
    ("CoinTelegraph",    "https://cointelegraph.com/rss"),
    ("CoinDesk",         "https://coindesk.com/arc/outboundfeeds/rss/"),
    ("Decrypt",          "https://decrypt.co/feed"),
    ("Bitcoin Magazine", "https://bitcoinmagazine.com/.rss/full/"),
]

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
}

# ===== News Category Images =====
NEWS_IMAGES = {
    "bitcoin": [
        "https://images.unsplash.com/photo-1590283603385-17ffb3a7f29f?w=800&q=80&fit=crop",
        "https://images.unsplash.com/photo-1622630998477-20aa696ecb05?w=800&q=80&fit=crop",
        "https://images.unsplash.com/photo-1518546305927-5a555bb7020d?w=800&q=80&fit=crop",
        "https://images.unsplash.com/photo-1516245834210-c4c142787335?w=800&q=80&fit=crop",
        "https://images.unsplash.com/photo-1605792657660-596af9009e82?w=800&q=80&fit=crop",
        "https://images.unsplash.com/photo-1523961131990-5ea7c61b2107?w=800&q=80&fit=crop",
    ],
    "ethereum": [
        "https://images.unsplash.com/photo-1639762681485-074b7f938ba0?w=800&q=80&fit=crop",
        "https://images.unsplash.com/photo-1622630998477-20aa696ecb05?w=800&q=80&fit=crop",
        "https://images.unsplash.com/photo-1642790551116-18e4f97a7f33?w=800&q=80&fit=crop",
        "https://images.unsplash.com/photo-1516245834210-c4c142787335?w=800&q=80&fit=crop",
    ],
    "hack": [
        "https://images.unsplash.com/photo-1550751827-4bd374c3f58b?w=800&q=80&fit=crop",
        "https://images.unsplash.com/photo-1563013544-824ae1b704d3?w=800&q=80&fit=crop",
        "https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?w=800&q=80&fit=crop",
        "https://images.unsplash.com/photo-1558494949-ef010cbdcc31?w=800&q=80&fit=crop",
        "https://images.unsplash.com/photo-1544197150-b99a580bb7a8?w=800&q=80&fit=crop",
        "https://images.unsplash.com/photo-1555949963-aa79dcee981c?w=800&q=80&fit=crop",
    ],
    "regulation": [
        "https://images.unsplash.com/photo-1589829545856-d10d557cf95f?w=800&q=80&fit=crop",
        "https://images.unsplash.com/photo-1450101499163-c8848c66ca85?w=800&q=80&fit=crop",
        "https://images.unsplash.com/photo-1521791055366-0d553872952f?w=800&q=80&fit=crop",
        "https://images.unsplash.com/photo-1454165804606-c3d57bc86b40?w=800&q=80&fit=crop",
        "https://images.unsplash.com/photo-1507679799987-c73779587ccf?w=800&q=80&fit=crop",
        "https://images.unsplash.com/photo-1436450412741-6b308b7c6b7f?w=800&q=80&fit=crop",
    ],
    "etf": [
        "https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?w=800&q=80&fit=crop",
        "https://images.unsplash.com/photo-1460925895917-afdab827c52f?w=800&q=80&fit=crop",
        "https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=800&q=80&fit=crop",
        "https://images.unsplash.com/photo-1579621970563-ebec7560ff3e?w=800&q=80&fit=crop",
        "https://images.unsplash.com/photo-1504711434969-e33886168f5c?w=800&q=80&fit=crop",
        "https://images.unsplash.com/photo-1526304640581-d334cdbbf45e?w=800&q=80&fit=crop",
    ],
    "bullish": [
        "https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?w=800&q=80&fit=crop",
        "https://images.unsplash.com/photo-1569025690938-a00729c9e1f9?w=800&q=80&fit=crop",
        "https://images.unsplash.com/photo-1642790551116-18e4f97a7f33?w=800&q=80&fit=crop",
        "https://images.unsplash.com/photo-1559526324-593bc073d938?w=800&q=80&fit=crop",
        "https://images.unsplash.com/photo-1535320903710-d993d3d77d29?w=800&q=80&fit=crop",
        "https://images.unsplash.com/photo-1591696205602-2f950c417cb9?w=800&q=80&fit=crop",
    ],
    "bearish": [
        "https://images.unsplash.com/photo-1535320903710-d993d3d77d29?w=800&q=80&fit=crop",
        "https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?w=800&q=80&fit=crop",
        "https://images.unsplash.com/photo-1569025690938-a00729c9e1f9?w=800&q=80&fit=crop",
        "https://images.unsplash.com/photo-1579621970563-ebec7560ff3e?w=800&q=80&fit=crop",
        "https://images.unsplash.com/photo-1460925895917-afdab827c52f?w=800&q=80&fit=crop",
    ],
    "defi": [
        "https://images.unsplash.com/photo-1639762681485-074b7f938ba0?w=800&q=80&fit=crop",
        "https://images.unsplash.com/photo-1642790551116-18e4f97a7f33?w=800&q=80&fit=crop",
        "https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=800&q=80&fit=crop",
        "https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?w=800&q=80&fit=crop",
    ],
    "general": [
        "https://images.unsplash.com/photo-1642790551116-18e4f97a7f33?w=800&q=80&fit=crop",
        "https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?w=800&q=80&fit=crop",
        "https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=800&q=80&fit=crop",
        "https://images.unsplash.com/photo-1460925895917-afdab827c52f?w=800&q=80&fit=crop",
        "https://images.unsplash.com/photo-1559526324-593bc073d938?w=800&q=80&fit=crop",
        "https://images.unsplash.com/photo-1569025690938-a00729c9e1f9?w=800&q=80&fit=crop",
        "https://images.unsplash.com/photo-1579621970563-ebec7560ff3e?w=800&q=80&fit=crop",
        "https://images.unsplash.com/photo-1504711434969-e33886168f5c?w=800&q=80&fit=crop",
    ],
}

# ===== Terms to protect from translation =====
PRESERVE_TERMS = sorted([
    "BlackRock", "MicroStrategy", "Coinbase", "Grayscale", "Binance", "Tether",
    "Ripple Labs", "Circle", "Kraken", "Gemini", "PayPal", "Fidelity",
    "SEC", "CFTC", "FDIC", "Federal Reserve", "Fed",
    "Bitcoin ETF", "Spot ETF", "Futures ETF", "ETF",
    "Bitcoin", "BTC", "Ethereum", "ETH", "Solana", "SOL",
    "Ripple", "XRP", "Binance", "BNB", "Cardano", "ADA",
    "Dogecoin", "DOGE", "Avalanche", "AVAX", "Chainlink", "LINK",
    "Polkadot", "DOT", "Litecoin", "LTC", "USDT", "USDC",
    "Tron", "TRX", "DeFi", "NFT", "Web3", "DAO", "DEX", "CEX",
    "blockchain", "Blockchain", "halving", "Halving",
    "stablecoin", "altcoin", "mining", "airdrop",
    "MACD", "RSI", "ATH", "ATL",
], key=len, reverse=True)

POSTED_FILE = "posted_urls.json"
MAX_SUMMARY_LENGTH = 200

# ===== Analysis Phrase Banks =====
TOPIC_PHRASES = {
    "etf_approval": [
        "تأیید ETF می‌تواند موج جدیدی از سرمایه‌گذاری نهادی را وارد بازار کند.",
        "این اتفاق دسترسی سرمایه‌گذاران سنتی به بازار کریپتو را آسان‌تر می‌کند.",
        "ETF می‌تواند میلیاردها دلار سرمایه جدید را به اکوسیستم کریپتو جذب کند.",
        "این تصمیم اعتبار بازار کریپتو را نزد سرمایه‌گذاران محافظه‌کار افزایش می‌دهد.",
        "تأیید ETF یک نقطه عطف مهم برای پذیرش گسترده‌تر ارزهای دیجیتال است.",
    ],
    "etf_general": [
        "ETF ابزاری قدرتمند برای ورود سرمایه‌های بزرگ به بازار کریپتو است.",
        "توجه نهادها به ETF نشانه‌ای از بلوغ بازار ارزهای دیجیتال است.",
        "نگاه بازار به ETF نشان‌دهنده اشتیاق برای ابزارهای مالی رگوله‌شده است.",
        "این تحولات در حوزه ETF می‌تواند تعادل عرضه و تقاضا را تغییر دهد.",
        "ETF کریپتو همچنان یکی از داغ‌ترین موضوعات در میان سرمایه‌گذاران است.",
    ],
    "sec": [
        "اقدام SEC فشار نظارتی بر صنعت کریپتو را افزایش می‌دهد.",
        "این دعوای حقوقی ابهامات قانونی در بازار را بیشتر می‌کند.",
        "موضع‌گیری SEC تأثیر مستقیمی بر احساسات بازار خواهد داشت.",
        "این پرونده می‌تواند پیشینه‌ای برای تنظیم مقررات آینده باشد.",
        "نظارت SEC بر بازار کریپتو همچنان یکی از عوامل اصلی نوسانات است.",
    ],
    "hack": [
        "این حمله امنیتی یادآور اهمیت نگهداری امن دارایی‌هاست.",
        "هک‌های بزرگ فشار نزولی موقتی ایجاد می‌کنند اما پروتکل‌های امنیتی را تقویت می‌کنند.",
        "سرمایه‌گذاران باید دارایی‌های خود را در کیف‌پول سرد نگهداری کنند.",
        "این رویداد نشان می‌دهد که امنیت سایبری چالش اصلی صنعت کریپتو است.",
        "این حادثه اهمیت ممیزی‌های امنیتی مستمر را نشان می‌دهد.",
    ],
    "halving": [
        "Halving با کاهش عرضه Bitcoin، زمینه افزایش قیمت در بلندمدت را فراهم می‌کند.",
        "تاریخچه نشان می‌دهد Halvingهای قبلی با رشد قابل توجه همراه بوده‌اند.",
        "با نزدیک شدن به Halving، توجه نهادی به Bitcoin افزایش می‌یابد.",
        "اثر Halving بر قیمت معمولاً با تأخیر چند ماهه خود را نشان می‌دهد.",
        "Halving یکی از مهم‌ترین رویدادهای اقتصادی در چرخه Bitcoin است.",
    ],
    "regulation": [
        "قوانین جدید در کوتاه‌مدت نوسان ایجاد می‌کنند اما در بلندمدت به ثبات کمک می‌کنند.",
        "وضوح قانونی یکی از مهم‌ترین عوامل برای جذب سرمایه‌گذاری نهادی است.",
        "مقررات جدید همیشه دو روی سکه دارند: محدودیت و فرصت.",
        "این تحولات قانونی نشان‌دهنده تلاش دولت‌ها برای یکپارچه‌سازی کریپتو است.",
        "سرمایه‌گذاران باید تحولات قانونی را با دقت دنبال کنند.",
    ],
    "ban": [
        "ممنوعیت‌ها معمولاً اثر کوتاه‌مدت دارند زیرا کریپتو غیرمتمرکز است.",
        "واکنش بازار به ممنوعیت‌ها اغلب اغراق‌آمیز است و فرصت خرید ایجاد می‌کند.",
        "تاریخ نشان داده که ممنوعیت‌ها اغلب موقتی هستند.",
        "این اقدام ممکن است سرمایه را به مناطق با قوانین دوستانه‌تر هدایت کند.",
        "این خبر در کوتاه‌مدت احساسات منفی ایجاد می‌کند اما تأثیر بلندمدت آن محدود است.",
    ],
    "price_surge": [
        "رشد قوی قیمت نشانه‌ای از افزایش تقاضا و اعتماد بازار است.",
        "این جهش قیمتی توجه سرمایه‌گذاران جدید را جلب می‌کند.",
        "سیگنال‌های تکنیکال صعودی هستند اما باید مراقب پولبک‌های احتمالی بود.",
        "در چنین شرایطی مدیریت ریسک و تعیین حد ضرر اهمیت ویژه‌ای دارد.",
        "این رشد می‌تواند نقطه شروع یک روند صعودی پایدار باشد.",
    ],
    "price_crash": [
        "این افت قیمت فرصتی برای خرید پله‌ای بلندمدت ایجاد می‌کند.",
        "در شرایط نزولی، مدیریت سرمایه و حفظ نقدینگی اولویت است.",
        "سطوح حمایتی کلیدی باید با دقت دنبال شوند.",
        "این اصلاح قیمتی می‌تواند پایه محکم‌تری برای رشد آینده ایجاد کند.",
        "بازار کریپتو سابقه بازگشت قوی پس از اصلاح‌های شدید را دارد.",
    ],
    "general": [
        "این خبر می‌تواند تأثیر قابل توجهی بر احساسات بازار داشته باشد.",
        "سرمایه‌گذاران باید این تحول را در کنار سایر شاخص‌های بازار بررسی کنند.",
        "بازار کریپتو همواره به اخبار با حساسیت بالایی واکنش نشان می‌دهد.",
        "این رویداد یکی از عوامل متعددی است که بر قیمت‌ها تأثیر می‌گذارد.",
        "تحلیل دقیق‌تر این خبر نیازمند بررسی داده‌های بیشتری است.",
    ],
}

DIRECTION_BULLISH = [
    "سیگنال‌های صعودی در کوتاه‌مدت قوی به نظر می‌رسند.",
    "چشم‌انداز کوتاه‌مدت مثبت است اما مدیریت ریسک فراموش نشود.",
    "این خبر می‌تواند محرک خوبی برای ادامه روند صعودی باشد.",
    "بازار واکنش مثبتی نشان داده و روند صعودی محتمل است.",
    "فشار خرید افزایش یافته و کف‌های قیمتی محکم‌تر شده‌اند.",
]
DIRECTION_BEARISH = [
    "احتیاط در کوتاه‌مدت توصیه می‌شود و باید منتظر تثبیت بازار ماند.",
    "فشار نزولی محتمل است؛ مدیریت ریسک اولویت داشته باشد.",
    "سرمایه‌گذاران باید با دقت بیشتری وارد پوزیشن‌های جدید شوند.",
    "در این شرایط حفظ نقدینگی می‌تواند استراتژی هوشمندانه‌ای باشد.",
    "بازار در حال هضم این خبر است و نوسانات بیشتری محتمل است.",
]
DIRECTION_NEUTRAL = [
    "بازار در انتظار سیگنال‌های بیشتر برای تعیین جهت است.",
    "در چنین شرایطی تنوع‌بخشی به سبد سرمایه‌گذاری اهمیت ویژه‌ای دارد.",
    "این خبر در کوتاه‌مدت تأثیر محدودی خواهد داشت اما در بلندمدت اهمیت دارد.",
    "سرمایه‌گذاران باید با دید بلندمدت به این تحولات نگاه کنند.",
    "تحلیلگران دیدگاه‌های متفاوتی دارند و باید داده‌های بیشتری منتظر ماند.",
]


# ===== Helpers =====

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

def score_article(title):
    score = 0
    title_lower = title.lower()
    high   = ["etf", "sec", "regulation", "ban", "lawsuit", "hack",
              "halving", "all-time high", "ath", "crash", "approval"]
    medium = ["bitcoin", "ethereum", "binance", "coinbase", "btc", "eth"]
    for word in high:
        if word in title_lower:
            score += 3
    for word in medium:
        if word in title_lower:
            score += 1
    if any(w in title_lower for w in BULLISH_WORDS + BEARISH_WORDS):
        score += 2
    return score

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
    text = (title + " " + summary).lower()
    collected = []
    seen = set()
    for keyword, tags in TAG_MAP.items():
        if keyword in text:
            for tag in tags:
                if tag not in seen:
                    seen.add(tag)
                    collected.append(tag)
    for fallback in ["#کریپتو", "#اخبار_کریپتو", "#ارز_دیجیتال"]:
        if fallback not in seen:
            collected.append(fallback)
    return collected[:5]

# ===== Image Picker =====

def get_image_url(title, summary):
    text = (title + " " + summary).lower()
    if "hack" in text or "exploit" in text or "stolen" in text or "breach" in text:
        return random.choice(NEWS_IMAGES["hack"])
    elif "sec" in text or "cftc" in text or "regulation" in text or "ban" in text or "law" in text:
        return random.choice(NEWS_IMAGES["regulation"])
    elif "etf" in text:
        return random.choice(NEWS_IMAGES["etf"])
    elif "bitcoin" in text or "btc" in text:
        return random.choice(NEWS_IMAGES["bitcoin"])
    elif "ethereum" in text or "eth" in text:
        return random.choice(NEWS_IMAGES["ethereum"])
    elif "defi" in text or "nft" in text or "web3" in text:
        return random.choice(NEWS_IMAGES["defi"])
    elif any(w in text for w in BULLISH_WORDS):
        return random.choice(NEWS_IMAGES["bullish"])
    elif any(w in text for w in BEARISH_WORDS):
        return random.choice(NEWS_IMAGES["bearish"])
    else:
        return random.choice(NEWS_IMAGES["general"])

# ===== Translation =====

def protect_terms(text):
    placeholders = {}
    protected = text
    for i, term in enumerate(PRESERVE_TERMS):
        placeholder = f"XX{i}XX"
        pattern = re.compile(re.escape(term), re.IGNORECASE)
        if pattern.search(protected):
            match = pattern.search(protected)
            placeholders[placeholder] = match.group(0)
            protected = pattern.sub(placeholder, protected)
    return protected, placeholders

def restore_terms(text, placeholders):
    for placeholder, original in placeholders.items():
        text = text.replace(placeholder, original)
    return text

def translate(text):
    if not text:
        return ""
    text = truncate(text, 400)
    protected, placeholders = protect_terms(text)
    for attempt in range(3):
        try:
            result = GoogleTranslator(source='en', target='fa').translate(protected)
            if result:
                return restore_terms(result, placeholders).strip()
        except Exception as e:
            print(f"Translation attempt {attempt+1} failed:", e)
            time.sleep(2)
    return ""

# ===== Analysis =====

def get_ai_analysis(title, summary):
    text = (title + " " + summary).lower()
    if "etf" in text and ("approval" in text or "approve" in text):
        topic = random.choice(TOPIC_PHRASES["etf_approval"])
    elif "etf" in text:
        topic = random.choice(TOPIC_PHRASES["etf_general"])
    elif "sec" in text or "cftc" in text:
        topic = random.choice(TOPIC_PHRASES["sec"])
    elif "hack" in text or "exploit" in text or "stolen" in text:
        topic = random.choice(TOPIC_PHRASES["hack"])
    elif "halving" in text:
        topic = random.choice(TOPIC_PHRASES["halving"])
    elif "ban" in text or "prohibit" in text:
        topic = random.choice(TOPIC_PHRASES["ban"])
    elif "regulation" in text or "law" in text or "bill" in text:
        topic = random.choice(TOPIC_PHRASES["regulation"])
    elif any(w in text for w in ["surge", "rally", "soar", "ath", "all-time high"]):
        topic = random.choice(TOPIC_PHRASES["price_surge"])
    elif any(w in text for w in ["crash", "plunge", "collapse", "dump"]):
        topic = random.choice(TOPIC_PHRASES["price_crash"])
    else:
        topic = random.choice(TOPIC_PHRASES["general"])

    title_lower = title.lower()
    if any(w in title_lower for w in BULLISH_WORDS):
        direction = random.choice(DIRECTION_BULLISH)
    elif any(w in title_lower for w in BEARISH_WORDS):
        direction = random.choice(DIRECTION_BEARISH)
    else:
        direction = random.choice(DIRECTION_NEUTRAL)

    return f"{topic} {direction}"

# ===== Prices =====

def get_prices():
    try:
        r = requests.get(
            "https://api.coingecko.com/api/v3/simple/price",
            params={"ids": "bitcoin,ethereum", "vs_currencies": "usd",
                    "include_24hr_change": "true"},
            timeout=10
        )
        data = r.json()
        btc = data["bitcoin"]
        eth = data["ethereum"]
        btc_change = btc.get("usd_24h_change", 0)
        eth_change = eth.get("usd_24h_change", 0)
        btc_emoji = "📈" if btc_change >= 0 else "📉"
        eth_emoji = "📈" if eth_change >= 0 else "📉"
        return (f"{btc_emoji} BTC: ${btc['usd']:,.0f} ({btc_change:+.1f}%)\n"
                f"{eth_emoji} ETH: ${eth['usd']:,.0f} ({eth_change:+.1f}%)")
    except:
        return None

# ===== Telegram =====

def send_photo(image_url, caption):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
    payload = {
        "chat_id":    TELEGRAM_CHANNEL_ID,
        "photo":      image_url,
        "caption":    caption,
        "parse_mode": "HTML",
    }
    try:
        r = requests.post(url, data=payload, timeout=15)
        return r.status_code == 200
    except:
        return False

def send_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id":              TELEGRAM_CHANNEL_ID,
        "text":                 message,
        "parse_mode":           "HTML",
        "disable_web_page_preview": True,
    }
    for attempt in range(3):
        try:
            r = requests.post(url, data=payload, timeout=10)
            if r.status_code == 200:
                return True
        except:
            pass
        time.sleep(2)
    return False

# ===== Persistence =====

def load_posted():
    if os.path.exists(POSTED_FILE):
        with open(POSTED_FILE, "r") as f:
            return set(json.load(f))
    return set()

def save_posted(posted):
    with open(POSTED_FILE, "w") as f:
        json.dump(list(posted)[-1000:], f)

# ===== Fetch News =====

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

# ===== Format Message =====

def build_message(article, fa_title, fa_summary, analysis, prices):
    tags      = get_tags(article["title"], article["summary"])
    tags_line = " ".join(tags)
    sentiment = get_sentiment_emoji(article["title"])

    lines = [
        f"{sentiment} <b>{fa_title}</b>",
        "",
        f"📝 {fa_summary}" if fa_summary else "",
        "",
        "🧠 <b>تحلیل:</b>",
        analysis,
        "",
    ]
    if prices:
        lines += ["💰 <b>قیمت لحظه‌ای:</b>", prices, ""]

    lines += [
        f'🔗 <a href="{article["url"]}">ادامه مطلب</a>',
        "",
        "👥 @Crypto_Zone360",
        "به ما بپیوندید 🦈",
        "",
        tags_line,
    ]
    return "\n".join(line for line in lines if line is not None)

# ===== Main =====

def main():
    now = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
    print(f"🚀 Bot started — {now}")

    posted   = load_posted()
    articles = fetch_news()
    prices   = get_prices()
    print(f"📥 Fetched {len(articles)} articles")

    articles.sort(key=lambda a: score_article(a["title"]), reverse=True)

    sent = 0
    for article in articles:
        if sent >= MAX_POSTS_PER_RUN:
            break

        url   = article["url"]
        title = article["title"]

        if url in posted:
            continue
        if not is_important(title):
            continue

        print(f"📌 [{article['source']}] {title}")

        fa_title   = translate(title)
        fa_summary = translate(article["summary"])
        analysis   = get_ai_analysis(title, article["summary"])

        if not fa_title:
            print("⚠️ Skipping — translation failed")
            continue

        message   = build_message(article, fa_title, fa_summary, analysis, prices)
        image_url = get_image_url(title, article["summary"])

        # Try sending with image first (caption limit 1024 chars)
        caption   = truncate(message, 1020)
        success   = send_photo(image_url, caption)

        # Fallback to text only
        if not success:
            print("📷 Image failed, sending text only")
            success = send_message(message)

        if success:
            posted.add(url)
            sent += 1
            time.sleep(3)

    save_posted(posted)
    print(f"✅ Done — {sent} new articles posted.")

if __name__ == "__main__":
    main()
