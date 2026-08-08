import os
import time
import requests
from datetime import datetime, timezone

TELEGRAM_BOT_TOKEN  = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHANNEL_ID = os.environ["TELEGRAM_CHANNEL_ID"]

COINS = [
    ("bitcoin",      "BTC",  "🟡", 1000),
    ("ethereum",     "ETH",  "🔷", 100),
    ("binancecoin",  "BNB",  "🟠", 10),
    ("solana",       "SOL",  "🟣", 10),
]

MONTHS_FA = ["ژانویه","فوریه","مارس","آوریل","مه","ژوئن",
             "ژوئیه","اوت","سپتامبر","اکتبر","نوامبر","دسامبر"]

def get_prices():
    ids = ",".join(c[0] for c in COINS)
    r = requests.get(
        "https://api.coingecko.com/api/v3/simple/price",
        params={
            "ids": ids,
            "vs_currencies": "usd",
            "include_24hr_change": "true",
            "include_24hr_vol": "true",
        },
        timeout=15
    )
    return r.json()

def fmt(price, step):
    if step >= 100:
        return f"${price:,.0f}"
    elif step >= 1:
        return f"${price:,.1f}"
    else:
        return f"${price:,.2f}"

def get_levels(price, step):
    base  = round(price / step) * step
    s1    = base - step
    s2    = base - step * 2
    r1    = base + step
    r2    = base + step * 2
    return s1, s2, r1, r2

def get_scenario(change, price, s1, r1, r2, step, symbol):
    r1_fmt = fmt(r1, step)
    r2_fmt = fmt(r2, step)
    s1_fmt = fmt(s1, step)

    if change > 4:
        return f"مومنتوم صعودی قوی. تثبیت بالای {r1_fmt} = هدف بعدی {r2_fmt} 🎯"
    elif change > 1.5:
        return f"روند مثبت. شکست {r1_fmt} با حجم = سیگنال خرید 🎯"
    elif change < -4:
        return f"فشار فروش شدید. حفظ {s1_fmt} برای جلوگیری از ریزش بیشتر حیاتی ⚠️"
    elif change < -1.5:
        return f"اصلاح در جریان. ناحیه {s1_fmt} حمایت کلیدی است 🔍"
    else:
        return f"تجمیع بین {s1_fmt} و {r1_fmt}. شکست هر طرف جهت را مشخص می‌کند ⏳"

def get_signal_label(change):
    if change > 3:    return "🟢 سیگنال: صعودی قوی"
    elif change > 1:  return "🟡 سیگنال: صعودی محتاطانه"
    elif change < -3: return "🔴 سیگنال: نزولی — احتیاط"
    elif change < -1: return "🟠 سیگنال: اصلاح — صبر"
    else:             return "⚪️ سیگنال: خنثی — انتظار"

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
    print(f"📡 Signals bot started — {now.strftime('%Y-%m-%d %H:%M UTC')}")

    # Tehran time display
    tehran_hour = (now.hour + 3) % 24
    tehran_min  = now.minute + 30
    if tehran_min >= 60:
        tehran_hour = (tehran_hour + 1) % 24
        tehran_min -= 60
    time_str = f"{tehran_hour:02d}:{tehran_min:02d}"
    date_str = f"{now.day} {MONTHS_FA[now.month-1]} {now.year}"

    data = get_prices()

    lines = [
        "📡 <b>سیگنال‌های بازار کریپتو</b>",
        f"📅 {date_str} | ⏰ {time_str}",
        "",
        "━━━━━━━━━━━━━━━",
        "",
    ]

    for coin_id, symbol, emoji, step in COINS:
        coin = data.get(coin_id, {})
        price  = coin.get("usd", 0) or 0
        change = coin.get("usd_24h_change", 0) or 0

        if price == 0:
            continue

        s1, s2, r1, r2 = get_levels(price, step)
        scenario = get_scenario(change, price, s1, r1, r2, step, symbol)
        signal   = get_signal_label(change)
        arr      = "📈" if change >= 0 else "📉"

        lines += [
            f"{emoji} <b>{symbol}</b>  {fmt(price, step)}  {arr} {change:+.1f}%",
            f"🛡 حمایت: {fmt(s1, step)} | {fmt(s2, step)}",
            f"⚔️ مقاومت: {fmt(r1, step)} | {fmt(r2, step)}",
            f"📊 {scenario}",
            f"{signal}",
            "",
        ]

    lines += [
        "━━━━━━━━━━━━━━━",
        "⚠️ <i>این پیام صرفاً دیدگاه تحلیلی است و توصیه مالی نیست.</i>",
        "",
        "👥 @Crypto_Zone360",
        "به ما بپیوندید 🦈",
        "",
        "#سیگنال #تحلیل_تکنیکال #Bitcoin #Ethereum #کریپتو",
    ]

    message = "\n".join(line for line in lines if line is not None)

    if send_to_telegram(message):
        print("✅ Signals posted!")
    else:
        print("❌ Failed.")

if __name__ == "__main__":
    main()
