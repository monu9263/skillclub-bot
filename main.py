import telebot  # 'i' को छोटा किया गया है
from telebot import types
import json
import os
from flask import Flask
from threading import Thread

# --- 1. कॉन्फ़िगरेशन ---
import os
import telebot

# पुरानी टोकन वाली लाइन को हटाकर ये 3 लाइनें लिखें:
API_TOKEN = os.getenv('API_TOKEN')
ADMIN_ID = os.getenv('ADMIN_ID')
bot = telebot.TeleBot(API_TOKEN)
DB_FILE = 'users.json'
COURSE_LINK = "https://drive.google.com/drive/folders/1b2BchlaXprjfro5DB7i7cBN5Jp5Xq_80"

# --- 2. भाषा और मैसेज (HTML Mode) ---
STRINGS = {
    "hi": {
        "welcome": "नमस्ते {name}! <b>Skillclub</b> में आपका स्वागत है।",
        "profile": "👤 <b>नाम:</b> {name}\n🏆 <b>स्टेटस:</b> {status}\n👥 <b>कुल रेफरल:</b> {refs}",
        "buy": "🚀 <b>कोर्स पेमेंट प्रक्रिया:</b>\n\n1. UPI: <code>anand1312@fam</code> पर ₹300 भेजें।\n2. स्क्रीनशॉट इसी बोट में भेजें।",
        "download": "✅ <b>आपका कोर्स तैयार है!</b>\nनीचे बटन दबाकर एक्सेस करें।",
        "download_btn": "📥 कोर्स डाउनलोड करें",
        "success_msg": "🥳 <b>मुबारक हो!</b> आपका पेमेंट अप्रूव हो गया है। नीचे बटन दबाकर कोर्स डाउनलोड करें।",
        "wallet": "💰 <b>वॉलेट बैलेंस:</b> ₹{bal}\n📉 न्यूनतम विड्रॉल: ₹500",
        "invite": "🔥 <b>आपका इनवाइट लिंक:</b>\n{link}",
        "not_paid": "❌ पहले कोर्स खरीदें।",
        "btns": ["👤 प्रोफाइल", "🔗 इनवाइट लिंक", "💰 वॉलेट", "📚 कोर्स खरीदें", "⚙️ सेटिंग्स"]
    },
    "en": {
        "welcome": "Hello {name}! Welcome to <b>Skillclub</b>.",
        "profile": "👤 <b>Name:</b> {name}\n🏆 <b>Status:</b> {status}\n👥 <b>Referrals:</b> {refs}",
        "buy": "🚀 <b>Payment:</b> \n1. Send ₹300 to UPI: <code>anand1312@fam</code>.\n2. Send screenshot here.",
        "download": "✅ <b>Your Course is Ready!</b>\nClick below to access.",
        "download_btn": "📥 Download Course",
        "success_msg": "🥳 <b>Success!</b> Payment approved. Click below to download.",
        "wallet": "💰 <b>Wallet Balance:</b> ₹{bal}\n📉 Min. Withdrawal: ₹500",
        "invite": "🔥 <b>Your Invite Link:</b>\n{link}",
        "not_paid": "❌ Purchase course first.",
        "btns": ["👤 Profile", "🔗 Invite Link", "💰 Wallet", "📚 Buy Course", "⚙️ Settings"]
    }
}

# --- 3. डेटा मैनेजर ---
def load_data():
    if not os.path.exists(DB_FILE):
        with open(DB_FILE, 'w') as f: json.dump({}, f)
        return {}
    try:
        with open(DB_FILE, 'r') as f: return json.load(f)
    except: return {}

def save_data(data):
    with open(DB_FILE, 'w') as f: json.dump(data, f, indent=4)

# --- 4. वेब सर्वर (24/7) ---
app = Flask('')
@app.route('/')
def home(): return "Skillclub Online!"
def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive():
    t = Thread(target=run)
    t.start()

# --- 5. मुख्य फंक्शन्स ---
def get_menu(uid, lang):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    b = STRINGS[lang]["btns"]
    markup.add(b[0], b[1])
    markup.add(b[2], b[3])
    markup.add(b[4])
    if str(uid) == ADMIN_ID: markup.add("🛠 Admin Panel")
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    data = load_data()
    uid = str(message.chat.id)
    if uid not in data:
        args = message.text.split()
        ref_id = args[1] if len(args) > 1 else None
        data[uid] = {"name": message.from_user.first_name, "balance": 0, "referred_by": ref_id, "status": "Free", "referrals": 0, "lang": "hi"}
        save_data(data)
    lang = data[uid].get("lang", "hi")
    bot.send_message(uid, STRINGS[lang]["welcome"].format(name=message.from_user.first_name), reply_markup=get_menu(uid, lang), parse_mode="HTML")

# --- 6. अप्रूवल और विड्रॉल लॉजिक ---
@bot.callback_query_handler(func=lambda call: True)
def callbacks(call):
    data = load_data()
    action = call.data.split('_')[0]
    uid = str(call.data.split('_')[-1])

    if action == "app":
        if uid in data and data[uid]["status"] == "Free":
            data[uid]["status"] = "Paid"
            lang = data[uid].get("lang", "hi")
            s = STRINGS[lang]
            p_id = data[uid].get("referred_by")
            if p_id and p_id in data:
                data[p_id]["balance"] += 200
                data[p_id].setdefault("referrals", 0)
                data[p_id]["referrals"] += 1
            save_data(data)
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton(s["download_btn"], url=COURSE_LINK))
            bot.send_message(uid, s["success_msg"], reply_markup=markup, parse_mode="HTML")
            bot.edit_message_caption("✅ <b>APPROVED</b>", ADMIN_ID, call.message.message_id, parse_mode="HTML")
        else:
            bot.answer_callback_query(call.id, "Already Paid!")

    elif action == "setlang":
        new_lang = call.data.split("_")[1]
        data[uid]["lang"] = new_lang
        save_data(data)
        bot.send_message(uid, "✅ Done!", reply_markup=get_menu(uid, new_lang))

    elif action == "ask_wd":
        if data[uid]["balance"] < 500:
            bot.answer_callback_query(call.id, "Min ₹500 required!", show_alert=True)
        else:
            msg = bot.send_message(uid, "📝 अपनी UPI ID भेजें:")
            bot.register_next_step_handler(msg, save_wd, data[uid]["balance"])

# --- 7. बटन्स का काम (The Missing Logic) ---
@bot.message_handler(func=lambda m: True)
def handle_menu(message):
    data = load_data()
    uid = str(message.chat.id)
    user = data.get(uid, {"lang": "hi", "status": "Free", "balance": 0})
    lang = user.get("lang", "hi")
    s = STRINGS[lang]
    text = message.text

    if text in ["👤 प्रोफाइल", "👤 Profile"]:
        bot.send_message(uid, s["profile"].format(name=user['name'], status=user['status'], refs=user.get('referrals', 0)), parse_mode="HTML")

    elif text in ["📚 कोर्स खरीदें", "📚 Buy Course"]:
        if user['status'] == "Paid":
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton(s["download_btn"], url=COURSE_LINK))
            bot.send_message(uid, s["download"], reply_markup=markup, parse_mode="HTML")
        else:
            bot.send_message(uid, s["buy"], parse_mode="HTML")

    elif text in ["💰 वॉलेट", "💰 Wallet"]:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("💸 Withdrawal", callback_data=f"ask_wd_{uid}"))
        bot.send_message(uid, s["wallet"].format(bal=user['balance']), reply_markup=markup, parse_mode="HTML")

    elif text in ["🔗 इनवाइट लिंक", "🔗 Invite Link"]:
        if user['status'] == "Paid":
            bot_info = bot.get_me()
            link = f"https://t.me/{bot_info.username}?start={uid}"
            bot.send_message(uid, s["invite"].format(link=link), parse_mode="HTML")
        else:
            bot.send_message(uid, s["not_paid"], parse_mode="HTML")

    elif text in ["⚙️ सेटिंग्स", "⚙️ Settings"]:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("Hindi 🇮🇳", callback_data="setlang_hi"),
                   types.InlineKeyboardButton("English 🇺🇸", callback_data="setlang_en"))
        bot.send_message(uid, "भाषा चुनें / Choose Language:", reply_markup=markup)

# --- 8. फोटो हैंडलर ---
@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    uid = str(message.chat.id)
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("✅ Approve", callback_data=f"app_{uid}"),
               types.InlineKeyboardButton("❌ Reject", callback_data=f"rej_{uid}"))
    bot.send_photo(ADMIN_ID, message.photo[-1].file_id, caption=f"📩 <b>नया पेमेंट!</b>\nID: <code>{uid}</code>", reply_markup=markup, parse_mode="HTML")
    bot.send_message(uid, "✅ स्क्रीनशॉट मिल गया! अप्रूवल का इंतज़ार करें।")

def save_wd(message, amt):
    bot.send_message(ADMIN_ID, f"🔔 <b>WD Request!</b>\nID: <code>{message.chat.id}</code>\nAmt: ₹{amt}\nUPI: {message.text}", parse_mode="HTML")
    bot.send_message(message.chat.id, "✅ रिक्वेस्ट भेज दी गई है।")

if __name__ == "__main__":
    print("🚀 Bot is starting...")
    keep_alive() # Ye UptimeRobot ko reply deta hai

    import time
    while True:
        try:
            # none_stop=True se error aane par bhi bot band nahi hota
            bot.polling(none_stop=True, interval=0, timeout=20)
        except Exception as e:
            print(f"⚠️ Polling Error: {e}")
            time.sleep(5) # 5 second baad apne aap restart hoga
