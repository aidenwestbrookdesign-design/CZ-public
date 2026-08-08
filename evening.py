import os
import time
import requests
from datetime import datetime, timezone

TELEGRAM_BOT_TOKEN  = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHANNEL_ID = os.environ["TELEGRAM_CHANNEL_ID"]

MONTHS_FA = ["ژانویه","فوریه","مارس","آوریل","مه","ژوئن",
             "ژوئیه","اوت","سپتامبر","اکتبر","نوامبر","دسامبر"]

def get_fear_greed():
    r = requests.get("https://api.alternative.me/fng/", timeout=10)
    data = r.json()["data"][0]
    return int(data["value"])

def fear_label(v):
    if v >= 75: return "😱 طمع شدید"
    elif v >= 55: return "😏 طمع"
    elif v >= 45: return "😐 خنثی"
    elif v >= 25: return "😨 ترس"
    else:         return "🥶 ترس شدید"

def fear_bar(v):
    filled = round(v / 10)
    bar = "█" * filled + "░" * (10 - filled)
    return f"[{bar}] {v}/100"

def fear_analysis(v):
    if v >= 75:
        return "بازار در طمع شدید! تاریخاً احتمال اصلاح بالاست. سود بگیرید و احتیاط کنید."
    elif v >= 55:
        return "احساسات مثبت اما مراقب باشید. مدیریت ریسک را فراموش نکنید."
    elif v >= 45:
        return "بازار خنثی است. منتظر سیگنال واضح‌تر باشید."
    elif v >= 25:
        return "ترس در بازار فرصت خرید تدریجی ایجاد می‌کند. DCA مناسب است."
    else:
        return "ترس شدید! تاریخاً بهترین زمان برای تجمیع تدریجی بوده است."

def get_gainers_losers():
    r = requests.get(
        "https://api.coingecko.com/api/v3/coins/markets",
        params={
            "vs_currency": "usd",
            "order": "market_cap_desc",
            "per_page": 100,
            "sparkline": False,
            "price_change_percentage": "24h",
        },
        timeout=15
    )
    coins = [
        c for c in r.json()
        if c.get("price_change_percentage_24h") is not None
        and c.get("market_cap", 0) > 50_000_000  # Filter tiny coins
    ]
    sorted_coins = sorted(coins, key=lambda x: x["price_change_percentage_24h"], reverse=True)
    gainers = sorted_coins[:3]
    losers  = list(reversed(sorted_coins[-3:]))
    return gainers, losers

def fmt_price(p):
    if p >= 1000:   return f"${p:,.0f}"
    elif p >= 1:    return f"${p:,.2f}"
    else:           return f"${p:.4f}"

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
            r = requests.post(url, data=payload, timeout=10)
            if r.status_code == 200:
                return True
            print(f"Telegram error ({r.status_code}):", r.text)
        except Exception as e:
            print(f"Attempt {attempt+1} failed:", e)
        time.sleep(2)
    return False

def main():
    now = datetime.now(timezone.utc)
    print(f"🌙 Evening bot started — {now.strftime('%Y-%m-%d %H:%M UTC')}")

    date_str = f"{now.day} {MONTHS_FA[now.month-1]} {now.year}"

    fg_value       = get_fear_greed()
    gainers, losers = get_gainers_losers()

    lines = [
        "🌙 <b>گزارش عصرگاهی بازار</b>",
        f"📅 {date_str}",
        "",
        "━━━━━━━━━━━━━━━",
        "",

        # Fear & Greed
        "😱 <b>شاخص ترس و طمع</b>",
        f"<b>{fear_label(fg_value)}</b>",
        f"<code>{fear_bar(fg_value)}</code>",
        f"<i>{fear_analysis(fg_value)}</i>",
        "",
        "━━━━━━━━━━━━━━━",
        "",

        # Gainers
        "🚀 <b>برترین صعودی‌های امروز</b>",
    ]

    for i, coin in enumerate(gainers):
        name   = coin.get("name", "")
        symbol = coin.get("symbol", "").upper()
        price  = coin.get("current_price", 0)
        change = coin.get("price_change_percentage_24h", 0)
        lines.append(f"{'🥇🥈🥉'[i]} <b>{symbol}</b> ({name})  {fmt_price(price)}  📈 <b>+{change:.1f}%</b>")

    lines += [
        "",
        "━━━━━━━━━━━━━━━",
        "",
        "💀 <b>برترین نزولی‌های امروز</b>",
    ]

    for i, coin in enumerate(losers):
        name   = coin.get("name", "")
        symbol = coin.get("symbol", "").upper()
        price  = coin.get("current_price", 0)
        change = coin.get("price_change_percentage_24h", 0)
        lines.append(f"{'🥇🥈🥉'[i]} <b>{symbol}</b> ({name})  {fmt_price(price)}  📉 <b>{change:.1f}%</b>")

    lines += [
        "",
        "━━━━━━━━━━━━━━━",
        "",
        "👥 @Crypto_Zone360",
        "به ما بپیوندید 🦈",
        "",
        "#ترس_و_طمع #بازار #کریپتو #گینر #لوزر #ارز_دیجیتال",
    ]

    message = "\n".join(line for line in lines if line is not None)

    if send_to_telegram(message):
        print("✅ Evening report posted!")
    else:
        print("❌ Failed.")

if __name__ == "__main__":
    main()
