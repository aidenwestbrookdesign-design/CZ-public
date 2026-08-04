import os
import time
import random
import requests
from datetime import datetime, timezone

TELEGRAM_BOT_TOKEN  = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHANNEL_ID = os.environ["TELEGRAM_CHANNEL_ID"]

MONTHS_FA = ["ژانویه","فوریه","مارس","آوریل","مه","ژوئن",
             "ژوئیه","اوت","سپتامبر","اکتبر","نوامبر","دسامبر"]

# ===== Data Fetching =====

def get_global_data():
    r = requests.get("https://api.coingecko.com/api/v3/global", timeout=15)
    return r.json().get("data", {})

def get_top_coins():
    r = requests.get(
        "https://api.coingecko.com/api/v3/coins/markets",
        params={
            "vs_currency": "usd",
            "order": "market_cap_desc",
            "per_page": 20,
            "page": 1,
            "sparkline": False,
            "price_change_percentage": "24h"
        },
        timeout=15
    )
    return {c["id"]: c for c in r.json()}

def fmt_mcap(v):
    if v >= 1_000_000_000_000:
        return f"${v/1_000_000_000_000:.2f}T"
    elif v >= 1_000_000_000:
        return f"${v/1_000_000_000:.1f}B"
    else:
        return f"${v/1_000_000:.0f}M"

def arrow(change):
    if change > 0.3:   return "📈"
    elif change < -0.3: return "📉"
    else:               return "➡️"

def pct(change, decimals=2):
    sign = "+" if change >= 0 else ""
    return f"{sign}{change:.{decimals}f}%"

# ===== Technical Commentary =====

def analyze_total(mcap, change):
    phrases_up = [
        "کل بازار در فاز صعودی قرار دارد. حجم معاملات روند را تأیید می‌کند.",
        "مومنتوم صعودی قوی است. شکست مقاومت‌های بالاتر محتمل به نظر می‌رسد.",
        "روند کلی بازار مثبت است. MA50 بالاتر از MA200 قرار دارد.",
        "تقاضا در بازار قوی است. سطوح بالاتر در دسترس هستند.",
    ]
    phrases_down = [
        "بازار در فاز اصلاح است. سطوح حمایتی کلیدی باید حفظ شوند.",
        "فشار فروش افزایش یافته. صبر برای تثبیت قبل از ورود توصیه می‌شود.",
        "روند نزولی کوتاه‌مدت ادامه دارد. مدیریت ریسک اولویت است.",
        "اصلاح سالم بازار است اما باید مراقب شکست حمایت‌ها بود.",
    ]
    phrases_neutral = [
        "بازار در فاز تجمیع قرار دارد. شکست این محدوده جهت بعدی را مشخص می‌کند.",
        "بازار بلاتکلیف است. منتظر کاتالیست قوی‌تر برای جهت‌گیری باشید.",
        "نوسان کم نشانه آماده شدن برای یک حرکت بزرگ است.",
    ]
    if change > 1: return random.choice(phrases_up)
    elif change < -1: return random.choice(phrases_down)
    else: return random.choice(phrases_neutral)

def analyze_btc_d(val, change):
    if val > 60:
        base = "سلطه BTC بسیار بالاست. آلت‌کوین‌ها در فشار شدید هستند. هنوز زمان آلت سیزن نیست."
    elif val > 55:
        base = "سلطه BTC بالاست. سرمایه به سمت بیت‌کوین جریان دارد. احتیاط در آلت‌کوین‌ها."
    elif val > 50:
        base = "سلطه BTC در محدوده متعادل. بازار بین BTC و آلت‌کوین‌ها تقسیم شده."
    elif val > 45:
        base = "سلطه BTC در حال کاهش. پول در حال چرخش به سمت آلت‌کوین‌هاست."
    else:
        base = "سلطه BTC پایین است. احتمال آلت‌کوین سیزن بالاست."

    if change > 0.3:
        trend = " BTC در حال کسب سهم بیشتر از بازار است."
    elif change < -0.3:
        trend = " آلت‌کوین‌ها در حال کسب سهم از BTC هستند."
    else:
        trend = " سلطه BTC تغییر قابل توجهی نداشته."
    return base + trend

def analyze_eth_d(val, change):
    if val > 20:
        base = "ETH سهم بزرگی از بازار دارد. اتریوم در موضع قدرت است."
    elif val > 15:
        base = "سهم ETH در محدوده معمول قرار دارد."
    elif val > 10:
        base = "سهم ETH نسبتاً پایین است. ممکن است ETH عقب مانده باشد."
    else:
        base = "سهم ETH از بازار کاهش قابل توجهی داشته."

    if change > 0.2:
        trend = " ETH در حال کسب سهم بیشتر از بازار است."
    elif change < -0.2:
        trend = " سهم ETH از بازار در حال کاهش است."
    else:
        trend = " سهم ETH تغییر زیادی نداشته."
    return base + trend

def analyze_ethbtc(val, change):
    if change > 2:
        return f"ETH نسبت به BTC عملکرد بهتری دارد. نسبت {val:.4f} در حال صعود. ETH قوی‌تر از BTC معامله می‌شود."
    elif change < -2:
        return f"BTC نسبت به ETH قوی‌تر عمل می‌کند. نسبت {val:.4f} در حال نزول. سرمایه از ETH به BTC می‌رود."
    else:
        return f"نسبت ETH/BTC در محدوده {val:.4f} در تجمیع است. هیچ‌کدام برتری واضحی ندارند."

def analyze_total2(mcap, change):
    phrases_up = [
        "آلت‌کوین‌ها در حال جذب سرمایه هستند. روند مثبت برای آلت‌ها.",
        "سرمایه به سمت آلت‌کوین‌ها حرکت می‌کند. مومنتوم مثبت دارند.",
        "بازار آلت‌کوین‌ها سالم است. فرصت‌های خوبی در آلت‌ها وجود دارد.",
    ]
    phrases_down = [
        "آلت‌کوین‌ها در فشار فروش هستند. سرمایه به سمت BTC یا خروج از بازار.",
        "بازار آلت‌کوین‌ها ضعیف است. احتیاط در ورود به پوزیشن‌های جدید.",
        "خروج سرمایه از آلت‌کوین‌ها مشهود است.",
    ]
    phrases_neutral = [
        "بازار آلت‌کوین‌ها در تجمیع است. منتظر سیگنال واضح‌تر باشید.",
        "آلت‌کوین‌ها بلاتکلیف هستند. BTC.D را دنبال کنید.",
    ]
    if change > 1: return random.choice(phrases_up)
    elif change < -1: return random.choice(phrases_down)
    else: return random.choice(phrases_neutral)

def analyze_others(mcap, change):
    phrases_up = [
        "کوین‌های کوچک‌تر در حال صعود هستند. ریسک‌پذیری بازار افزایش یافته.",
        "آلت‌کوین‌های کوچک مومنتوم مثبت دارند. دقت در انتخاب ضروری است.",
        "پول به آلت‌کوین‌های کوچک‌تر می‌رود. نشانه احتمالی آلت سیزن.",
    ]
    phrases_down = [
        "آلت‌کوین‌های کوچک در فشار فروش شدید هستند. ریسک بالاست.",
        "سرمایه از کوین‌های کوچک‌تر خارج می‌شود. احتیاط کنید.",
        "OTHERS ضعیف است — نشانه عدم تمایل بازار به ریسک.",
    ]
    phrases_neutral = [
        "OTHERS در تجمیع است. صبر کنید تا BTC.D جهت مشخص کند.",
        "بازار کوین‌های کوچک‌تر بلاتکلیف است.",
    ]
    if change > 1: return random.choice(phrases_up)
    elif change < -1: return random.choice(phrases_down)
    else: return random.choice(phrases_neutral)

def analyze_usdt_d(val, change):
    if val > 8:
        base = "USDT.D بسیار بالاست. مقدار زیادی پول نقد در کنار بازار منتظر است — پتانسیل صعود بالا."
    elif val > 6:
        base = "USDT.D بالاست. سرمایه‌گذاران محتاط هستند اما نقدینگی برای ورود آماده است."
    elif val > 4:
        base = "USDT.D در محدوده متعادل. تعادل بین نقدینگی و سرمایه‌گذاری."
    elif val > 2:
        base = "USDT.D پایین است. اکثر سرمایه در بازار. ریسک اصلاح در افق."
    else:
        base = "USDT.D بسیار پایین است. تقریباً همه سرمایه در بازار — احتیاط!"

    if change > 0.2:
        trend = " سرمایه‌گذاران در حال تبدیل دارایی به USDT هستند — خروج از بازار."
    elif change < -0.2:
        trend = " USDT در حال تبدیل به ارز دیجیتال — ورود سرمایه به بازار."
    else:
        trend = " جریان نقدینگی تغییر قابل توجهی ندارد."
    return base + trend

# ===== Market Summary Signal =====

def get_market_signal(btc_d, usdt_d, total_change, btc_d_change):
    if usdt_d > 6 and total_change > 0:
        return "🟢 سیگنال کلی: صعودی — نقدینگی بالا + روند مثبت"
    elif usdt_d < 3 and total_change < 0:
        return "🔴 سیگنال کلی: نزولی — نقدینگی کم + فشار فروش"
    elif btc_d > 58 and btc_d_change > 0:
        return "🟡 سیگنال کلی: خنثی/BTC محور — آلت‌کوین‌ها در فشار"
    elif btc_d < 48 and btc_d_change < 0:
        return "🟢 سیگنال کلی: احتمال آلت‌کوین سیزن — BTC.D در حال کاهش"
    elif total_change > 2:
        return "🟢 سیگنال کلی: بازار در روند صعودی"
    elif total_change < -2:
        return "🔴 سیگنال کلی: بازار در روند نزولی"
    else:
        return "🟡 سیگنال کلی: خنثی — منتظر سیگنال واضح‌تر"

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
            r = requests.post(url, data=payload, timeout=10)
            if r.status_code == 200:
                return True
            print(f"Telegram error ({r.status_code}):", r.text)
        except Exception as e:
            print(f"Attempt {attempt+1} failed:", e)
        time.sleep(2)
    return False

# ===== Main =====

def main():
    print(f"📊 Market analysis started — {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")

    global_data = get_global_data()
    coins       = get_top_coins()

    # Raw values
    total_mcap    = global_data.get("total_market_cap", {}).get("usd", 0)
    total_change  = global_data.get("market_cap_change_percentage_24h_usd", 0)
    btc_d         = global_data.get("market_cap_percentage", {}).get("btc", 0)
    eth_d         = global_data.get("market_cap_percentage", {}).get("eth", 0)
    usdt_d        = global_data.get("market_cap_percentage", {}).get("usdt", 0)

    btc  = coins.get("bitcoin", {})
    eth  = coins.get("ethereum", {})

    btc_price    = btc.get("current_price", 0)
    eth_price    = eth.get("current_price", 0)
    btc_mcap     = btc.get("market_cap", 0)
    eth_mcap     = eth.get("market_cap", 0)
    btc_change   = btc.get("price_change_percentage_24h", 0) or 0
    eth_change   = eth.get("price_change_percentage_24h", 0) or 0

    # TOTAL2 = total minus BTC
    total2       = total_mcap - btc_mcap
    total2_change = total_change - (btc_change - total_change) * (btc_mcap / total_mcap) if total_mcap else 0

    # OTHERS = total minus top 5 coins by mcap
    top5_ids     = ["bitcoin","ethereum","tether","binancecoin","ripple"]
    top5_mcap    = sum(coins.get(c, {}).get("market_cap", 0) for c in top5_ids)
    others_mcap  = total_mcap - top5_mcap
    others_change = total_change  # rough approximation

    # ETHBTC
    ethbtc        = eth_price / btc_price if btc_price > 0 else 0
    ethbtc_change = eth_change - btc_change

    # Dominance changes (approximate)
    btc_d_change  = btc_change - total_change
    eth_d_change  = eth_change - total_change
    usdt_d_change = -total_change * 0.5  # USDT.D moves inverse to market

    now = datetime.now(timezone.utc)
    date_str = f"{now.day} {MONTHS_FA[now.month-1]} {now.year}"

    signal = get_market_signal(btc_d, usdt_d, total_change, btc_d_change)

    lines = [
        "📊 <b>تحلیل تکنیکال ساختار بازار</b>",
        f"📅 {date_str} | ⏰ ۰۹:۰۰",
        "",
        f"<b>{signal}</b>",
        "",
        "━━━━━━━━━━━━━━━",
        "",

        f"🌐 <b>TOTAL</b>  {fmt_mcap(total_mcap)}  {arrow(total_change)} {pct(total_change)}",
        f"<i>{analyze_total(total_mcap, total_change)}</i>",
        "",

        f"📊 <b>TOTAL2</b>  {fmt_mcap(total2)}  {arrow(total2_change)} {pct(total2_change)}",
        f"<i>{analyze_total2(total2, total2_change)}</i>",
        "",

        f"🔵 <b>BTC.D</b>  {btc_d:.2f}%  {arrow(btc_d_change)} {pct(btc_d_change)}",
        f"<i>{analyze_btc_d(btc_d, btc_d_change)}</i>",
        "",

        f"🔷 <b>ETH.D</b>  {eth_d:.2f}%  {arrow(eth_d_change)} {pct(eth_d_change)}",
        f"<i>{analyze_eth_d(eth_d, eth_d_change)}</i>",
        "",

        f"💱 <b>ETH/BTC</b>  {ethbtc:.4f}  {arrow(ethbtc_change)} {pct(ethbtc_change)}",
        f"<i>{analyze_ethbtc(ethbtc, ethbtc_change)}</i>",
        "",

        f"🌊 <b>OTHERS</b>  {fmt_mcap(others_mcap)}  {arrow(others_change)} {pct(others_change)}",
        f"<i>{analyze_others(others_mcap, others_change)}</i>",
        "",

        f"💵 <b>USDT.D</b>  {usdt_d:.2f}%  {arrow(usdt_d_change)} {pct(usdt_d_change)}",
        f"<i>{analyze_usdt_d(usdt_d, usdt_d_change)}</i>",
        "",

        "━━━━━━━━━━━━━━━",
        "",
        "👥 @Crypto_Zone360",
        "به ما بپیوندید 🦈",
        "",
        "#تحلیل_تکنیکال #BTC_Dominance #کریپتو #ارز_دیجیتال #بازار",
    ]

    message = "\n".join(line for line in lines if line is not None)

    if send_to_telegram(message):
        print("✅ Market analysis sent!")
    else:
        print("❌ Failed to send.")

if __name__ == "__main__":
    main()
