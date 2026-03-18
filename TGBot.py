import requests
from datetime import datetime
import pytz
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from js import Response

REGION_ID = "327"
CHATS = [
    {"CHAT_ID": "-1003798710531", "SITE_LINK": "https://msc-team-10a-class.netlify.app/"},
    {"CHAT_ID": "-1003785488166", "SITE_LINK": "https://msc-team-10b-class.netlify.app/"},
    {"CHAT_ID": "-1003598215535", "SITE_LINK": "https://msc-team-10v-class.netlify.app/"}
]
ALERT_MAP_LINK = "https://map.ukrainealarm.com/"
KYIV = pytz.timezone("Europe/Kyiv")

previous_alert = False
started_in_work_time = False

# Функція перевірки часу
def is_work_time():
    now = datetime.now(KYIV)
    weekday = now.weekday() # 0 = Понеділок, 6 = Неділя

    if weekday >= 5:
        return False # Вихідні дні
    
    start = now.replace(hour=8, minute=0, second=0)
    end = now.replace(hour=23, minute=40, second=0)

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
def send_telegram_message(text, BOT_TOKEN, is_clear=False):
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
def check_alert(env):
    global previous_alert, started_in_work_time

    BOT_TOKEN = env.BOT_TOKEN
    API_KEY = env.API_KEY

    url = f"https://api.ukrainealarm.com/api/v3/alerts/{REGION_ID}"
    headers = {
        "accept": "application/json",
        "Authorization": API_KEY
    }

    now_str = datetime.now(KYIV).strftime("%H:%M:%S")
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
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
                "🔴 <b>Увага! Оголошено повітряну тривогу! Негайно пройдіть в найближче укриття!</b> 🔴",
                BOT_TOKEN
            )

    # ✅ Відбій тривоги
    if not current_alert and previous_alert:
        if started_in_work_time:
            send_telegram_message("🟢 <b> Увага! Відбій повітряної тривоги!</b> 🟢", BOT_TOKEN, is_clear=True)
            started_in_work_time = False

    previous_alert = current_alert

async def on_fetch(request, env):
    check_alert(env)
    return Response.new("Перевірка тривоги виконана успішно")
