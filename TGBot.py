import requests
from datetime import datetime
import pytz
import threading
import time
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import os

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
API_KEY = os.getenv("API_KEY", "").strip()
REGION_ID = "327"
CHATS = [
    {"CHAT_ID": "-1002642409946", "SITE_LINK": "https://msc-team-11a-class.pages.dev/"},
    {"CHAT_ID": "-1002101902414", "SITE_LINK": "https://msc-team-11b-class.pages.dev/"},
    {"CHAT_ID": "-1002744754617", "SITE_LINK": "https://msc-team-11v-class.pages.dev/"}
]
ALERT_MAP_LINK = "https://map.ukrainealarm.com/"
KYIV = pytz.timezone("Europe/Kyiv")

print("--- БОТ ЗАПУСКАЄТЬСЯ ---")
if not BOT_TOKEN:
    print("❌ ПОМИЛКА: BOT_TOKEN не знайдено в змінних оточення!")
if not API_KEY:
    print("❌ ПОМИЛКА: API_KEY не знайдено в змінних оточення!")
else:
    print(f"✅ Ключі завантажені (Ключ API починається на: {API_KEY[:5]}...)")

previous_alert = False
started_in_work_time = False

# Функція перевірки часу
def is_work_time():
    now = datetime.now(KYIV)
    weekday = now.weekday() # 0 = Понеділок, 6 = Неділя

    if weekday >= 5:
        return False # Вихідні дні
    
    start = now.replace(hour=8, minute=0, second=0)
    end = now.replace(hour=15, minute=40, second=0)

    return start <= now <= end

# Створення клавіатури для каналу
def build_inline_keyboard(SITE_LINK, is_clear=False):
    keyboard = InlineKeyboardMarkup()

    if is_clear:
        btn_site = InlineKeyboardButton(text="🔗 Посилання на сайт", url=SITE_LINK)
        keyboard.add(btn_site)
    else:
        btn_map = InlineKeyboardButton(text="🚀 Мапа повітряних тривог", url=ALERT_MAP_LINK, style="danger")
        btn_site = InlineKeyboardButton(text="🔗 Посилання на сайт", url=SITE_LINK)
        keyboard.add(btn_map)
        keyboard.add(btn_site)
    return keyboard

# Відправка повідомлення у всі канали
def send_telegram_message(text, is_clear=False):
    for channel in CHATS:
        keyboard = build_inline_keyboard(channel["SITE_LINK"], is_clear=is_clear)
        telegram_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": channel["CHAT_ID"],
            "text": text,
            "parse_mode": "HTML",
            "reply_markup": keyboard.to_dict()
        }
        requests.post(telegram_url, json=payload)

# Перевірка тривог
def check_alert():
    global previous_alert, started_in_work_time

    url = f"https://api.ukrainealarm.com/api/v3/alerts/{REGION_ID}"
    headers = {
        "accept": "application/json",
        "Authorization": API_KEY
    }

    now_str = datetime.now(KYIV).strftime("%H:%M:%S")
    print(f"[{now_str}] Виконується запит до API...")

    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        print(f"[{now_str}] Помилка API:", response.status_code)
        return

    
    data = response.json()

    if not data:
        return
    
    region = data[0]
    current_alert = bool(region["activeAlerts"])

    # Початок тривоги
    if current_alert and not previous_alert:
        if is_work_time():
            started_in_work_time = True
            send_telegram_message(
                "🔴 <b>Увага! Оголошено повітряну тривогу! Негайно пройдіть в найближче укриття!</b> 🔴"
            )

    # ✅ Відбій тривоги
    if not current_alert and previous_alert:
        if started_in_work_time:
            send_telegram_message("🟢 <b> Увага! Відбій повітряної тривоги!</b> 🟢", is_clear=True)
            started_in_work_time = False

    previous_alert = current_alert

# Основний цикл
while True:
    check_alert()

    time.sleep(30) # Перевірка кожні 30 секунд
