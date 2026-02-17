import requests
from datetime import datetime
import pytz
import threading
import time
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import os

BOT_TOKEN = os.getenv("BOT_TOKEN")
API_KEY = os.getenv("API_KEY")
REGION_ID = "327"
CHATS = [
    {"CHAT_ID": "-1003798710531", "site_link": "https://msc-team-10a-class.netlify.app/"},
    {"CHAT_ID": "-1003785488166", "site_link": "https://msc-team-10b-class.netlify.app/"},
    {"CHAT_ID": "-1003598215535", "site_link": "https://msc-team-10v-class.netlify.app/"}
]
ALERT_MAP_LINK = "https://map.ukrainealarm.com/"
KYIV = pytz.timezone("Europe/Kyiv")

previous_alert = False
started_in_work_time = False

# Функція перевірки часу
def is_work_time():
    now = datetime.now(KYIV)
    weekday = now.weekday() # 0 = Понеділок, 6 = Неділя

    if weekday >= 7:
        return False # Вихідні дні
    
    start = now.replace(hour=1, minute=0, second=0)
    end = now.replace(hour=23, minute=59, second=0)

    return start <= now <= end

# Створення клавіатури для каналу
def build_inline_keyboard(site_link):
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("🗺️ Мапа повітряних тривог", url=ALERT_MAP_LINK))
    keyboard.add(InlineKeyboardButton("🌐 Перейти на сайт класу", url=site_link))
    return keyboard

# Відправка повідомлення у всі канали
def send_telegram_message(text):
    for channel in CHATS:
        keyboard = build_inline_keyboard(channel["site_link"])
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
        "Authorization": f"Bearer {API_KEY}"
    }

    try:
        response = requests.get(url, headers=headers)
        
        if response.status_code == 401:
            print("❌ Помилка 401: Невірний API-ключ!")
            return
        
        if response.status_code != 200:
            print(f"Помилка API: {response.status_code}")
            return
        
        data = response.json()

        # Якщо масив не порожній — є активні тривоги
        # Згідно з документацією v3, якщо тривог немає, приходить []
        current_alert = len(data) > 0

    # Початок тривоги
    if current_alert and not previous_alert:
        if is_work_time():
            started_in_work_time = True
            send_telegram_message(
                "🚨 Увага! У м. Самар розпочалася повітряна тривога! Тестування бота!"
            )

    # ✅ Відбій тривоги
    if not current_alert and previous_alert:
        if started_in_work_time:
            send_telegram_message(
                "✅ Увага! У м. Самар відбій повітряної тривоги! Тестування бота!"
            )
            started_in_work_time = False

    previous_alert = current_alert

# Основний цикл
while True:
    check_alert()

    time.sleep(30) # Перевірка кожні 30 секунд


print("API_KEY value:", API_KEY)







