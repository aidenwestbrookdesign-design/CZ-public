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

# ===== Analysis Phrase Banks =====

TOPIC_PHRASES = {
    "etf_approval": [
        "تأیید ETF می‌تواند موج جدیدی از سرمایه‌گذاری نهادی را وارد بازار کند.",
        "این اتفاق دسترسی سرمایه‌گذاران سنتی به بازار کریپتو را به شکل چشمگیری آسان‌تر می‌کند.",
        "تأیید ETF یک نقطه عطف مهم برای پذیرش گسترده‌تر ارزهای دیجیتال است.",
        "ETF می‌تواند میلیاردها دلار سرمایه جدید را به اکوسیستم کریپتو جذب کند.",
        "این تصمیم اعتبار بازار کریپتو را نزد سرمایه‌گذاران محافظه‌کار افزایش می‌دهد.",
    ],
    "etf_general": [
        "ETF ابزاری قدرتمند برای ورود سرمایه‌های بزرگ به بازار کریپتو است.",
        "توجه نهادها به ETF نشانه‌ای از بلوغ بازار ارزهای دیجیتال است.",
        "این تحولات در حوزه ETF می‌تواند تعادل عرضه و تقاضا را تغییر دهد.",
        "ETF کریپتو همچنان یکی از داغ‌ترین موضوعات در میان سرمایه‌گذاران است.",
        "نگاه بازار به ETF نشان‌دهنده اشتیاق برای ابزارهای مالی رگوله‌شده است.",
    ],
    "sec_lawsuit": [
        "اقدام قانونی SEC فشار نظارتی بر صنعت کریپتو را افزایش می‌دهد و بازار را به احتیاط وا می‌دارد.",
        "این دعوای حقوقی ابهامات قانونی در بازار را بیشتر می‌کند و ممکن است سرمایه‌گذاران را نگران کند.",
        "اقدام SEC نشان می‌دهد که نهادهای نظارتی همچنان نگاه دقیقی به صنعت کریپتو دارند.",
        "این پرونده می‌تواند به عنوان پیشینه‌ای برای تنظیم مقررات آینده صنعت کریپتو عمل کند.",
        "چنین اقداماتی از سوی SEC معمولاً فشار کوتاه‌مدتی بر قیمت‌ها ایجاد می‌کند.",
    ],
    "sec_general": [
        "موضع‌گیری SEC تأثیر مستقیمی بر احساسات بازار و رفتار سرمایه‌گذاران خواهد داشت.",
        "نظارت SEC بر بازار کریپتو همچنان یکی از عوامل اصلی نوسانات قیمتی است.",
        "اظهارات نهادهای نظارتی مانند SEC همواره باید با دقت دنبال شود.",
        "این تحولات نظارتی چشم‌انداز قانونی بازار کریپتو را شکل می‌دهند.",
        "موضع‌گیری‌های SEC تعیین‌کننده مسیر آینده پذیرش کریپتو در آمریکاست.",
    ],
    "hack": [
        "این حمله امنیتی یادآور اهمیت انتخاب کیف‌پول‌های معتبر و نگهداری امن دارایی‌هاست.",
        "هک‌های بزرگ معمولاً فشار نزولی موقتی بر بازار ایجاد می‌کنند اما پروتکل‌های امنیتی را تقویت می‌کنند.",
        "این رویداد نشان می‌دهد که امنیت سایبری همچنان یکی از چالش‌های اصلی صنعت کریپتو است.",
        "سرمایه‌گذاران باید دارایی‌های خود را از صرافی‌ها خارج و در کیف‌پول سرد نگهداری کنند.",
        "این حادثه اهمیت ممیزی‌های امنیتی مستمر در پروتکل‌های بلاکچین را نشان می‌دهد.",
    ],
    "halving": [
        "هاوینگ با کاهش عرضه جدید بیت‌کوین، معمولاً زمینه را برای افزایش قیمت در بلندمدت فراهم می‌کند.",
        "تاریخچه نشان می‌دهد که هاوینگ‌های قبلی با رشد قابل توجه قیمت همراه بوده‌اند.",
        "هاوینگ یکی از مهم‌ترین رویدادهای اقتصادی در چرخه بیت‌کوین به شمار می‌رود.",
        "با نزدیک شدن به هاوینگ، توجه نهادی و خرده‌فروشی به بیت‌کوین افزایش می‌یابد.",
        "اثر هاوینگ بر قیمت معمولاً با تأخیر چند ماهه خود را نشان می‌دهد.",
    ],
    "regulation": [
        "قوانین جدید می‌توانند در کوتاه‌مدت نوسان ایجاد کنند اما در بلندمدت به ثبات بازار کمک می‌کنند.",
        "وضوح قانونی یکی از مهم‌ترین عوامل برای جذب سرمایه‌گذاری نهادی است.",
        "این تحولات قانونی نشان‌دهنده تلاش دولت‌ها برای یکپارچه‌سازی کریپتو در سیستم مالی است.",
        "مقررات جدید همیشه دو روی سکه دارند: محدودیت برای برخی و فرصت برای سازگاران.",
        "سرمایه‌گذاران باید تحولات قانونی را با دقت دنبال کنند زیرا مستقیماً بر بازار اثر می‌گذارند.",
    ],
    "ban": [
        "ممنوعیت‌ها معمولاً اثر کوتاه‌مدت دارند زیرا ماهیت غیرمتمرکز کریپتو را نمی‌توان به راحتی محدود کرد.",
        "این اقدام ممکن است سرمایه را به سمت مناطق با قوانین دوستانه‌تر هدایت کند.",
        "تاریخ نشان داده که ممنوعیت‌ها اغلب موقتی هستند و بازار پس از آن قوی‌تر باز می‌گردد.",
        "این خبر در کوتاه‌مدت احساسات منفی ایجاد می‌کند اما تأثیر بلندمدت آن محدود است.",
        "واکنش بازار به ممنوعیت‌ها اغلب اغراق‌آمیز است و فرصت خرید ایجاد می‌کند.",
    ],
    "partnership": [
        "این همکاری می‌تواند پذیرش گسترده‌تر فناوری بلاکچین را در صنایع سنتی تسریع کند.",
        "اشتراک‌گذاری میان شرکت‌های بزرگ و پروژه‌های کریپتو نشانه‌ای مثبت برای آینده صنعت است.",
        "این نوع همکاری‌ها اعتبار پروژه را نزد سرمایه‌گذاران نهادی افزایش می‌دهد.",
        "ادغام فناوری‌های Web3 با کسب‌وکارهای سنتی روندی رو به رشد و پایدار است.",
        "این اعلام نشان‌دهنده اعتماد فزاینده شرکت‌های بزرگ به زیرساخت‌های بلاکچین است.",
    ],
    "price_surge": [
        "این رشد قیمتی می‌تواند نقطه شروع یک روند صعودی پایدار باشد اما تأیید حجم معاملات لازم است.",
        "سیگنال‌های تکنیکال صعودی هستند اما سرمایه‌گذاران باید مراقب پولبک‌های احتمالی باشند.",
        "این جهش قیمتی توجه سرمایه‌گذاران جدید را جلب می‌کند که خود می‌تواند روند را تقویت کند.",
        "رشد قوی قیمت نشانه‌ای از افزایش تقاضا و اعتماد بازار است.",
        "در چنین شرایطی مدیریت ریسک و تعیین حد ضرر اهمیت ویژه‌ای دارد.",
    ],
    "price_crash": [
        "این افت قیمت فرصتی برای خرید پله‌ای بلندمدت ایجاد می‌کند اما باید منتظر تثبیت بود.",
        "سطوح حمایتی کلیدی باید با دقت دنبال شوند تا از ادامه روند نزولی جلوگیری شود.",
        "در شرایط نزولی، مدیریت سرمایه و حفظ نقدینگی اولویت اصلی سرمایه‌گذاران است.",
        "این اصلاح قیمتی در بلندمدت می‌تواند پایه محکم‌تری برای رشد آینده ایجاد کند.",
        "بازار کریپتو سابقه بازگشت قوی پس از اصلاح‌های شدید را دارد.",
    ],
    "adoption": [
        "پذیرش گسترده‌تر کریپتو توسط کسب‌وکارها نشانه‌ای قوی از بلوغ این بازار است.",
        "هر قدم به سوی پذیرش جریان اصلی، ارزش بلندمدت اکوسیستم کریپتو را افزایش می‌دهد.",
        "این نوع اخبار معمولاً تأثیر مثبت پایداری بر اعتماد سرمایه‌گذاران دارد.",
        "گسترش استفاده واقعی از کریپتو در تجارت و مالیه، پشتوانه قوی‌تری برای قیمت‌ها ایجاد می‌کند.",
        "این تحول نشان می‌دهد که کریپتو دیگر فقط یک ابزار سرمایه‌گذاری نیست بلکه یک فناوری کاربردی است.",
    ],
    "defi": [
        "DeFi همچنان در حال تغییر ساختار سیستم مالی سنتی است و این اخبار نشان‌دهنده رشد این بخش است.",
        "پروتکل‌های DeFi با ارائه خدمات مالی بدون واسطه، فرصت‌های جدیدی برای سرمایه‌گذاران ایجاد می‌کنند.",
        "رشد DeFi نشان‌دهنده تقاضای واقعی برای سیستم‌های مالی غیرمتمرکز است.",
        "این تحولات در DeFi می‌تواند نقدینگی قابل توجهی را وارد اکوسیستم کریپتو کند.",
        "DeFi به عنوان یکی از نوآورانه‌ترین بخش‌های صنعت کریپتو همچنان در حال تکامل است.",
    ],
    "general": [
        "این خبر می‌تواند تأثیر قابل توجهی بر احساسات کلی بازار در روزهای آینده داشته باشد.",
        "سرمایه‌گذاران باید این تحول را در کنار سایر شاخص‌های بازار بررسی کنند.",
        "تحلیل دقیق‌تر این خبر نیازمند بررسی داده‌های بیشتری از بازار است.",
        "این رویداد یکی از عوامل متعددی است که در کوتاه‌مدت بر قیمت‌ها تأثیر می‌گذارد.",
        "بازار کریپتو همواره به اخبار با حساسیت بالایی واکنش نشان می‌دهد.",
    ],
}

DIRECTION_BULLISH = [
    "سیگنال‌های صعودی در کوتاه‌مدت قوی به نظر می‌رسند.",
    "چشم‌انداز کوتاه‌مدت مثبت است اما مدیریت ریسک فراموش نشود.",
    "این خبر می‌تواند محرک خوبی برای ادامه روند صعودی باشد.",
    "بازار واکنش مثبتی به این خبر نشان داده و روند صعودی محتمل است.",
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
    "این خبر در کوتاه‌مدت تأثیر محدودی خواهد داشت اما در بلندمدت اهمیت دارد.",
    "سرمایه‌گذاران باید با دید بلندمدت به این تحولات نگاه کنند.",
    "تحلیلگران دیدگاه‌های متفاوتی دارند و باید داده‌های بیشتری منتظر ماند.",
    "در چنین شرایطی تنوع‌بخشی به سبد سرمایه‌گذاری اهمیت ویژه‌ای دارد.",
]

POSTED_FILE = "posted_urls.json"
MAX_SUMMARY_LENGTH = 200


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

# ===== Smart Rule-Based Analysis =====

def get_ai_analysis(title, summary):
    text = (title + " " + summary).lower()

    # Detect topic
    if "etf" in text and ("approval" in text or "approve" in text or "approv" in text):
        topic = random.choice(TOPIC_PHRASES["etf_approval"])
    elif "etf" in text:
        topic = random.choice(TOPIC_PHRASES["etf_general"])
    elif "sec" in text and ("lawsuit" in text or "sue" in text or "charge" in text or "action" in text):
        topic = random.choice(TOPIC_PHRASES["sec_lawsuit"])
    elif "sec" in text or "cftc" in text:
        topic = random.choice(TOPIC_PHRASES["sec_general"])
    elif "hack" in text or "exploit" in text or "breach" in text or "stolen" in text:
        topic = random.choice(TOPIC_PHRASES["hack"])
    elif "halving" in text or "halvening" in text:
        topic = random.choice(TOPIC_PHRASES["halving"])
    elif "ban" in text or "banned" in text or "prohibit" in text:
        topic = random.choice(TOPIC_PHRASES["ban"])
    elif "regulation" in text or "regulate" in text or "law" in text or "bill" in text:
        topic = random.choice(TOPIC_PHRASES["regulation"])
    elif "partner" in text or "collaboration" in text or "integration" in text:
        topic = random.choice(TOPIC_PHRASES["partnership"])
    elif "defi" in text or "decentralized finance" in text:
        topic = random.choice(TOPIC_PHRASES["defi"])
    elif "adopt" in text or "launch" in text or "accept" in text:
        topic = random.choice(TOPIC_PHRASES["adoption"])
    elif any(w in text for w in ["surge", "rally", "soar", "breakout", "ath", "all-time high"]):
        topic = random.choice(TOPIC_PHRASES["price_surge"])
    elif any(w in text for w in ["crash", "plunge", "collapse", "dump", "sell-off"]):
        topic = random.choice(TOPIC_PHRASES["price_crash"])
    else:
        topic = random.choice(TOPIC_PHRASES["general"])

    # Detect direction
    title_lower = title.lower()
    bullish = any(w in title_lower for w in BULLISH_WORDS)
    bearish = any(w in title_lower for w in BEARISH_WORDS)
    if bullish and not bearish:
        direction = random.choice(DIRECTION_BULLISH)
    elif bearish and not bullish:
        direction = random.choice(DIRECTION_BEARISH)
    else:
        direction = random.choice(DIRECTION_NEUTRAL)

    return f"{topic} {direction}"

# ===== Crypto Prices =====

def get_prices():
    try:
        url = "https://api.coingecko.com/api/v3/simple/price"
        params = {
            "ids": "bitcoin,ethereum",
            "vs_currencies": "usd",
            "include_24hr_change": "true"
        }
        r = requests.get(url, params=params, timeout=10)
        data = r.json()
        btc = data["bitcoin"]
        eth = data["ethereum"]
        btc_change = btc.get("usd_24h_change", 0)
        eth_change = eth.get("usd_24h_change", 0)
        btc_emoji = "📈" if btc_change >= 0 else "📉"
        eth_emoji = "📈" if eth_change >= 0 else "📉"
        return (
            f"{btc_emoji} BTC: ${btc['usd']:,.0f} ({btc_change:+.1f}%)\n"
            f"{eth_emoji} ETH: ${eth['usd']:,.0f} ({eth_change:+.1f}%)"
        )
    except Exception as e:
        print("Price fetch failed:", e)
        return None

# ===== Translation =====

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

# ===== Telegram =====

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

def format_message(article, fa_title, fa_summary, analysis, prices):
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
        lines += [
            "💰 <b>قیمت لحظه‌ای:</b>",
            prices,
            "",
        ]

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

        message = format_message(article, fa_title, fa_summary, analysis, prices)
        if send_to_telegram(message):
            posted.add(url)
            sent += 1
            time.sleep(3)

    save_posted(posted)
    print(f"✅ Done — {sent} new articles posted.")

if __name__ == "__main__":
    main()
