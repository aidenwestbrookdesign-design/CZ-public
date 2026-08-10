import os
import time
import requests
from datetime import datetime, timezone

TELEGRAM_BOT_TOKEN  = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHANNEL_ID = os.environ["TELEGRAM_CHANNEL_ID"]

MONTHS_FA = ["ژانویه","فوریه","مارس","آوریل","مه","ژوئن",
             "ژوئیه","اوت","سپتامبر","اکتبر","نوامبر","دسامبر"]

RISK_LABELS = {
    "high":   "🔴 ریسک بالا",
    "medium": "🟡 ریسک متوسط",
    "low":    "🟢 ریسک پایین",
}

def get_trending():
    """Top trending coins on CoinGecko right now."""
    try:
        r = requests.get(
            "https://api.coingecko.com/api/v3/search/trending",
            timeout=15
        )
        data = r.json()
        coins = []
        for entry in data.get("coins", [])[:5]:
            item = entry.get("item", {})
            price_data = item.get("data", {})
            change = price_data.get("price_change_percentage_24h", {})
            change_usd = change.get("usd", 0) if isinstance(change, dict) else 0
            coins.append({
                "name":   item.get("name", ""),
                "symbol": item.get("symbol", "").upper(),
                "rank":   item.get("market_cap_rank", "N/A"),
                "price":  price_data.get("price", "N/A"),
                "change": change_usd,
            })
        return coins
    except Exception as e:
        print("Trending fetch failed:", e)
        return []

def get_small_cap_gainers():
    """Small cap coins with big 24h gains — potential movers."""
    try:
        r = requests.get(
            "https://api.coingecko.com/api/v3/coins/markets",
            params={
                "vs_currency": "usd",
                "order": "market_cap_asc",
                "per_page": 250,
                "page": 1,
                "sparkline": False,
                "price_change_percentage": "24h",
            },
            timeout=15
        )
        all_coins = r.json()
        picks = [
            c for c in all_coins
            if c.get("market_cap") and
               5_000_000 < c["market_cap"] < 300_000_000 and
               (c.get("price_change_percentage_24h") or 0) > 10
        ]
        picks.sort(key=lambda x: x.get("price_change_percentage_24h", 0), reverse=True)
        return picks[:3]
    except Exception as e:
        print("Small cap fetch failed:", e)
        return []

def get_new_listings():
    """Recently listed coins on CoinGecko with market activity."""
    try:
        r = requests.get(
            "https://api.coingecko.com/api/v3/coins/markets",
            params={
                "vs_currency": "usd",
                "order": "id_asc",
                "per_page": 50,
                "page": 1,
                "sparkline": False,
                "price_change_percentage": "24h",
            },
            timeout=15
        )
        # Filter coins with low market cap rank (new/small) but good volume
        coins = [
            c for c in r.json()
            if c.get("market_cap_rank") and c["market_cap_rank"] > 300
            and (c.get("total_volume") or 0) > 500_000
            and (c.get("price_change_percentage_24h") or 0) > 5
        ]
        coins.sort(key=lambda x: x.get("price_change_percentage_24h", 0), reverse=True)
        return coins[:3]
    except Exception as e:
        print("New listings fetch failed:", e)
        return []

def risk_label(market_cap):
    if market_cap < 20_000_000:
        return RISK_LABELS["high"]
    elif market_cap < 100_000_000:
        return RISK_LABELS["medium"]
    else:
        return RISK_LABELS["low"]

def fmt_price(p):
    if p >= 1000:   return f"${p:,.0f}"
    elif p >= 1:    return f"${p:,.2f}"
    elif p >= 0.01: return f"${p:.4f}"
    else:           return f"${p:.8f}"

def fmt_mcap(v):
    if v >= 1_000_000_000: return f"${v/1_000_000_000:.1f}B"
    elif v >= 1_000_000:   return f"${v/1_000_000:.1f}M"
    else:                  return f"${v/1_000:.0f}K"

def send_to_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id":    TELEGRAM_CHANNEL_ID,
        "text":       message,
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
    print(f"🔍 Discover bot started — {now.strftime('%Y-%m-%d %H:%M UTC')}")

    date_str  = f"{now.day} {MONTHS_FA[now.month-1]} {now.year}"
    trending  = get_trending()
    gainers   = get_small_cap_gainers()
    new_coins = get_new_listings()

    numbers = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣"]

    lines = [
        "🔍 <b>کشف کوین‌های پرپتانسیل</b>",
        f"📅 {date_str}",
        "",
        "━━━━━━━━━━━━━━━",
        "",
        "🔥 <b>ترندینگ امروز</b>",
        "<i>داغ‌ترین کوین‌های ۲۴ ساعت گذشته</i>",
        "",
    ]

    for i, coin in enumerate(trending):
        change = coin["change"]
        arr    = "📈" if change >= 0 else "📉"
        rank   = f"رتبه #{coin['rank']}" if coin['rank'] != "N/A" else ""
        lines.append(
            f"{numbers[i]} <b>{coin['symbol']}</b> ({coin['name']})  "
            f"{coin['price']}  {arr} {change:+.1f}%  {rank}"
        )

    if gainers:
        lines += [
            "",
            "━━━━━━━━━━━━━━━",
            "",
            "💎 <b>کوین‌های کم‌ارزش با رشد بالا</b>",
            "<i>مارکت کپ کوچک + رشد قوی = پتانسیل بالا</i>",
            "",
        ]
        for i, coin in enumerate(gainers):
            name   = coin.get("name", "")
            symbol = coin.get("symbol", "").upper()
            price  = coin.get("current_price", 0)
            change = coin.get("price_change_percentage_24h", 0)
            mcap   = coin.get("market_cap", 0)
            risk   = risk_label(mcap)
            lines += [
                f"{numbers[i]} <b>{symbol}</b> ({name})",
                f"💰 {fmt_price(price)}  📈 <b>+{change:.1f}%</b>",
                f"🏦 مارکت کپ: {fmt_mcap(mcap)}  {risk}",
                "",
            ]

    if new_coins:
        lines += [
            "━━━━━━━━━━━━━━━",
            "",
            "🆕 <b>کوین‌های تازه با حجم بالا</b>",
            "<i>لیست‌شده‌های جدید که بازار به آن‌ها توجه کرده</i>",
            "",
        ]
        for i, coin in enumerate(new_coins):
            name   = coin.get("name", "")
            symbol = coin.get("symbol", "").upper()
            price  = coin.get("current_price", 0)
            change = coin.get("price_change_percentage_24h", 0)
            vol    = coin.get("total_volume", 0)
            arr    = "📈" if change >= 0 else "📉"
            lines += [
                f"{numbers[i]} <b>{symbol}</b> ({name})",
                f"💰 {fmt_price(price)}  {arr} {change:+.1f}%",
                f"📊 حجم ۲۴ساعته: {fmt_mcap(vol)}",
                "",
            ]

    lines += [
        "━━━━━━━━━━━━━━━",
        "",
        "⚠️ <i>این پست توصیه مالی نیست. قبل از خرید تحقیق کنید (DYOR).</i>",
        "🔴 <i>کوین‌های کم‌ارزش ریسک بسیار بالایی دارند.</i>",
        "",
        "👥 @Crypto_Zone360",
        "به ما بپیوندید 🦈",
        "",
        "#ترندینگ #کوین_جدید #آلت_کوین #کریپتو #ارز_دیجیتال #DYOR",
    ]

    message = "\n".join(line for line in lines if line is not None)

    if send_to_telegram(message):
        print("✅ Discover post sent!")
    else:
        print("❌ Failed.")

if __name__ == "__main__":
    main()
