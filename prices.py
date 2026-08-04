import os
import time
import requests
from datetime import datetime, timezone

TELEGRAM_BOT_TOKEN  = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHANNEL_ID = os.environ["TELEGRAM_CHANNEL_ID"]

NUMBERS = ["1️⃣","2️⃣","3️⃣","4️⃣","5️⃣","6️⃣","7️⃣","8️⃣","9️⃣","🔟"]

MONTHS_FA = ["ژانویه","فوریه","مارس","آوریل","مه","ژوئن",
             "ژوئیه","اوت","سپتامبر","اکتبر","نوامبر","دسامبر"]

def get_farsi_date():
    now = datetime.now(timezone.utc)
    return f"{now.day} {MONTHS_FA[now.month - 1]} {now.year}"

def get_top10():
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {
        "vs_currency": "usd",
        "order": "market_cap_desc",
        "per_page": 10,
        "page": 1,
        "sparkline": False,
        "price_change_percentage": "24h"
    }
    for attempt in range(3):
        try:
            r = requests.get(url, params=params, timeout=15)
            return r.json()
        except Exception as e:
            print(f"CoinGecko attempt {attempt+1} failed:", e)
            time.sleep(3)
    return []

def format_price(price):
    if price >= 1000:
        return f"${price:,.0f}"
    elif price >= 1:
        return f"${price:,.2f}"
    else:
        return f"${price:.4f}"

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

def main():
    print(f"💹 Prices bot started — {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")

    coins = get_top10()
    if not coins:
        print("Failed to fetch prices.")
        return

    date_str = get_farsi_date()
    lines = [
        "💹 <b>قیمت لحظه‌ای ارزهای دیجیتال</b>",
        f"📅 {date_str} | ⏰ ۰۸:۳۰",
        "",
        "━━━━━━━━━━━━━━━",
        "",
    ]

    for i, coin in enumerate(coins):
        name   = coin.get("name", "")
        symbol = coin.get("symbol", "").upper()
        price  = coin.get("current_price", 0)
        change = coin.get("price_change_percentage_24h", 0) or 0

        if change > 0.5:
            arrow = "📈"
            sign  = "+"
        elif change < -0.5:
            arrow = "📉"
            sign  = ""
        else:
            arrow = "➡️"
            sign  = "+"

        price_str  = format_price(price)
        change_str = f"{sign}{change:.2f}%"
        num        = NUMBERS[i]

        lines.append(f"{num} <b>{symbol}</b>  {price_str}  {arrow} {change_str}")

    lines += [
        "",
        "━━━━━━━━━━━━━━━",
        "",
        "👥 @Crypto_Zone360",
        "به ما بپیوندید 🦈",
        "",
        "#قیمت_کریپتو #بازار #Bitcoin #Ethereum #کریپتو",
    ]

    message = "\n".join(lines)

    if send_to_telegram(message):
        print("✅ Prices posted!")
    else:
        print("❌ Failed to post prices.")

if __name__ == "__main__":
    main()
