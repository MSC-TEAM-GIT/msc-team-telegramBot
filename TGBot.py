import requests
from datetime import datetime
import pytz
import threading
import time
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import os

# --- НАЛАШТУВАННЯ ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
API_KEY = os.getenv("API_KEY")
REGION_ID = "327" # ID м. Самар (Новомосковськ)
CHATS = [
    {"CHAT_ID": "-1003798710531", "site_link": "https://msc-team-10a-class.netlify.app/"},
    {"CHAT_ID": "-1003785488166", "site_link": "https://msc-team-10b-class.netlify.app/"},
    {"CHAT_ID": "-1003598215535", "site_link": "https://msc-team-10v-class.netlify.app/"}
]
ALERT_MAP_LINK = "https://map.ukrainealarm.com/"
KYIV = pytz.timezone("Europe/Kyiv")

# Глобальні змінні статку
previous_alert = False
started_in_work_time = False

# --- ФУНКЦІЇ ---

def is_work_time():
    """Перевіряє, чи зараз робочий час (Пн-Сб, 01:00 - 23:59)"""
    now = datetime.now(KYIV)
    weekday = now.weekday() # 0 = Понеділок, 6 = Неділя

    if weekday >= 6: # Якщо неділя (індекс 6)
        return False
    
    start = now.replace(hour=1, minute=0, second=0, microsecond=0)
    end = now.replace(hour=23, minute=59, second=0, microsecond=0)

    return start <= now <= end

def build_inline_keyboard(site_link):
    """Створює кнопки під повідомленням"""
    keyboard = InlineKeyboardMarkup()
    btn_map = InlineKeyboardButton("🗺️ Мапа повітряних тривог", url=ALERT_MAP_LINK)
    btn_site = InlineKeyboardButton("🌐 Перейти на сайт класу", url=site_link)
    keyboard.add(btn_map)
    keyboard.add(btn_site)
    return keyboard

def send_telegram_message(text):
    """Відправляє повідомлення у всі вказані чати"""
    for channel in CHATS:
        keyboard = build_inline_keyboard(channel["site_link"])
        telegram_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": channel["CHAT_ID"],
            "text": text,
            "parse_mode": "HTML",
            "reply_markup": keyboard.to_dict()
        }
        try:
            res = requests.post(telegram_url, json=payload, timeout=10)
            if res.status_code != 200:
                print(f"Помилка Telegram ({channel['CHAT_ID']}): {res.text}")
        except Exception as e:
            print(f"Помилка відправки в Telegram: {e}")

def check_alert():
    """Основна логіка перевірки тривоги через API"""
    global previous_alert, started_in_work_time

    url = f"https://api.ukrainealarm.com/api/v3/alerts/{REGION_ID}"
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }

    try:
        response = requests.get(url, headers=headers, timeout=15)

        # Обробка помилки авторизації
        if response.status_code == 401:
            print("❌ Помилка 401: Невірний API_KEY. Перевірте налаштування оточення.")
            return
        
        if response.status_code != 200:
            print(f"⚠️ Помилка API: {response.status_code}")
            return
        
        data = response.json()
        
        # Визначаємо, чи є активна тривога в масиві даних
        # Якщо тривог немає, API зазвичай повертає []
        current_alert = False
        if isinstance(data, list) and len(data) > 0:
            for item in data:
                if item.get("activeAlerts"):
                    current_alert = True
                    break

        # ЛОГІКА ПОВІДОМЛЕНЬ
        
        # 1. Початок тривоги
        if current_alert and not previous_alert:
            if is_work_time():
                started_in_work_time = True
                send_telegram_message(
                    "🚨 <b>Увага! У м. Самар розпочалася повітряна тривога!</b>\nПройдіть в укриття!"
                )
            print(f"[{datetime.now(KYIV).strftime('%H:%M:%S')}] Тривога ПОЧАЛАСЯ")

        # 2. Відбій тривоги
        elif not current_alert and previous_alert:
            if started_in_work_time:
                send_telegram_message(
                    "✅ <b>Увага! У м. Самар ВІДБІЙ повітряної тривоги!</b>"
                )
                started_in_work_time = False
            print(f"[{datetime.now(KYIV).strftime('%H:%M:%S')}] Тривога ЗАКІНЧИЛАСЯ")

        previous_alert = current_alert

    except requests.exceptions.RequestException as e:
        print(f"🌐 Помилка з'єднання з API: {e}")
    except Exception as e:
        print(f"❗ Непередбачена помилка: {e}")

# --- ГОЛОВНИЙ ЦИКЛ ---
if __name__ == "__main__":
    print("🚀 Бот запущений і моніторить тривоги...")
    while True:
        check_alert()
        time.sleep(30) # Перевірка кожні 30 секунд
