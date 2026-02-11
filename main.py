import telebot
from telebot import types
import json
import os
import re
from flask import Flask
from threading import Thread
import time

# --- 1. कॉन्फ़िगरेशन ---
API_TOKEN = os.getenv('API_TOKEN')
ADMIN_ID = os.getenv('ADMIN_ID')
bot = telebot.TeleBot(API_TOKEN)

DB_FILE = 'users.json'
COURSE_DB = 'courses.json'
SALES_FILE = 'sales_log.json'
WD_FILE = 'withdrawals_log.json'
ADMIN_UPI = "anand1312@fam" 
WELCOME_PHOTO = "https://files.catbox.moe/0v601y.png" 

# --- 2. भाषा और मैसेज ---
STRINGS = {
    "hi": {
        "welcome": "नमस्ते {name}! <b>Skillclub</b> में आपका स्वागत है। 🙏\n\n🚀 <b>स्टेप्स:</b>\n1️⃣ कोर्स चुनें\n2️⃣ पेमेंट करें\n3️⃣ स्क्रीनशॉट भेजें: Send your payment screenshot in bot here.\n4️⃣ इनवाइट लिंक जनरेट करें।\n\n🔥 <b>Daily Earn:</b> लिंक रेफर करें और रोज़ कमाएं! 💰",
        "lang_select": "🌐 अपनी भाषा चुनें / Choose language:",
        "lang_updated": "✅ भाषा <b>Hindi</b> में बदल दी गई है।",
        "profile": "👤 नाम: {name}\n🏆 स्टेटस: {status}\n👥 रेफरल: {refs}",
        "wallet_msg": "💰 वॉलेट बैलेंस: ₹{bal}\n📉 न्यूनतम विड्रॉल: ₹500",
        "invite": "🔥 आपका लिंक:\n{link}",
        "leaderboard_header": "🏆 Skillclub Top 10 Leaders 🏆\n\n",
        "btns": ["👤 प्रोफाइल", "🔗 इनवाइट लिंक", "💰 वॉलेट", "📚 कोर्स खरीदें", "🏆 लीडरबोर्ड", "⚙️ सेटिंग्स"]
    },
    "en": {
        "welcome": "Hello {name}! Welcome to <b>Skillclub</b>. 🙏\n\n🚀 <b>Steps:</b>\n1️⃣ Select Course\n2️⃣ Make Payment\n3️⃣ Send Screenshot: Send your payment screenshot in bot here.\n4️⃣ Generate Invite Link.\n\n🔥 <b>Daily Earn:</b> Refer and earn daily! 💰",
        "lang_select": "🌐 Choose language / अपनी भाषा चुनें:",
        "lang_updated": "✅ Language updated to <b>English</b>.",
        "profile": "👤 Name: {name}\n🏆 Status: {status}\n👥 Referrals: {refs}",
        "wallet_msg": "💰 Wallet Balance: ₹{bal}\n📉 Min. Withdrawal: ₹500",
        "invite": "🔥 Your Link:\n{link}",
        "leaderboard_header": "🏆 Skillclub Top 10 Leaders 🏆\n\n",
        "btns": ["👤 Profile", "🔗 Invite Link", "💰 Wallet", "📚 Buy Course", "🏆 Leaderboard", "⚙️ Settings"]
    }
}

# --- 3. डेटा मैनेजर ---
def load_json(filename):
    if not os.path.exists(filename): return [] if "log" in filename else {}
    try:
        with open(filename, 'r') as f: return json.load(f)
    except: return [] if "log" in filename else {}

def save_json(filename, data):
    with open(filename, 'w') as f: json.dump(data, f, indent=4)

def log_tx(filename, amount):
    logs = load_json(filename)
    if not isinstance(logs, list): logs = []
    logs.append({"amount": amount, "date": time.strftime("%Y-%m-%d"), "month": time.strftime("%Y-%m")})
    save_json(filename, logs)

# --- 4. एडमिन स्टेट्स लॉजिक ---
def get_stats():
    data = load_json(DB_FILE)
    sales = load_json(SALES_FILE)
    wd = load_json(WD_FILE)
    today, month = time.strftime("%Y-%m-%d"), time.strftime("%Y-%m")
    
    t_sell, m_sell, l_sell = 0, 0, 0
    for s in (sales if isinstance(sales, list) else []):
        l_sell += s['amount']
        if s['date'] == today: t_sell += s['amount']
        if s['month'] == month: m_sell += s['amount']
        
    t_wd, l_wd = 0, 0
    for w in (wd if isinstance(wd, list) else []):
        l_wd += w['amount']
        if w['date'] == today: t_wd += w['amount']

    return (f"📊 <b>Skillclub Stats</b>\n\n"
            f"💰 Today Sell: ₹{t_sell}\n"
            f"📅 Monthly: ₹{m_sell}\n"
            f"📈 Lifetime: ₹{l_sell}\n\n"
            f"💸 Today WD: ₹{t_wd}\n"
            f"🏧 Lifetime WD: ₹{l_wd}\n"
            f"👥 Users: {len(data)}")

# --- 5. मुख्य हैंडलर्स ---
@bot.callback_query_handler(func=lambda call: True)
def callback_router(call):
    data, courses = load_json(DB_FILE), load_json(COURSE_DB)
    uid, action = str(call.message.chat.id), call.data.split('_')[0]

    if action == "setlang":
        lang = call.data.split('_')[1]
        data[uid]["lang"] = lang
        save_json(DB_FILE, data)
        bot.send_message(uid, STRINGS[lang]["lang_updated"], reply_markup=get_main_menu(uid, lang), parse_mode="HTML")
    
    elif action == "app":
        t_id, cid = call.data.split('_')[1], "_".join(call.data.split('_')[2:])
        if t_id in data and cid in courses:
            c = courses[cid]
            if cid not in data[t_id].get("purchased", []):
                log_tx(SALES_FILE, c['price'])
                data[t_id].setdefault("purchased", []).append(cid)
                data[t_id]["status"] = "Paid"
                l1 = data[t_id].get("referred_by")
                if l1 and l1 in data:
                    data[l1]["balance"] += c.get("l1", 0)
                    data[l1]["referrals"] = data[l1].get("referrals", 0) + 1
                    l2 = data[l1].get("referred_by")
                    if l2 and l2 in data: data[l2]["balance"] += c.get("l2", 0)
            save_json(DB_FILE, data)
            bot.send_message(t_id, "🥳 Approved!", parse_mode="HTML")
            bot.edit_message_caption("✅ APPROVED", ADMIN_ID, call.message.message_id)

    elif action == "wdpay":
        t_id, amt = call.data.split('_')[1], int(call.data.split('_')[2])
        log_tx(WD_FILE, amt)
        data[t_id]["balance"] -= amt
        save_json(DB_FILE, data)
        bot.send_message(t_id, "🥳 Payout Done!", parse_mode="HTML")
        bot.edit_message_caption(f"✅ PAID ₹{amt}", ADMIN_ID, call.message.message_id)

@bot.message_handler(commands=['start'])
def start_cmd(message):
    data, uid = load_json(DB_FILE), str(message.chat.id)
    if uid not in data:
        ref = message.text.split()[1] if len(message.text.split()) > 1 else None
        data[uid] = {"name": message.from_user.first_name, "balance": 0, "referred_by": ref, "status": "Free", "referrals": 0, "lang": "hi", "purchased": []}
        save_json(DB_FILE, data)
    lang = data[uid].get("lang", "hi")
    bot.send_photo(uid, WELCOME_PHOTO, caption=STRINGS[lang]["welcome"].format(name=data[uid]["name"]), reply_markup=get_main_menu(uid, lang), parse_mode="HTML")

def get_main_menu(uid, lang):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    b = STRINGS[lang]["btns"]
    markup.add(b[0], b[1]).add(b[2], b[3]).add(b[4], b[5])
    if str(uid) == ADMIN_ID: markup.add("🛠 Admin Panel")
    return markup

@bot.message_handler(func=lambda m: True)
def menu_handler(message):
    data, uid = load_json(DB_FILE), str(message.chat.id)
    if uid not in data: return
    text, lang = message.text, data[uid].get("lang", "hi")

    if text == "🛠 Admin Panel" and uid == ADMIN_ID:
        m = types.ReplyKeyboardMarkup(resize_keyboard=True)
        m.add("📊 Stats", "📢 Broadcast").add("📥 Export Data", "🔙 Main Menu")
        bot.send_message(uid, "🛠 Admin Panel:", reply_markup=m)
    elif text == "📊 Stats" and uid == ADMIN_ID: bot.send_message(uid, get_stats(), parse_mode="HTML")
    elif text == "⚙️ सेटिंग्स" or text == "⚙️ Settings":
        m = types.InlineKeyboardMarkup()
        m.add(types.InlineKeyboardButton("🇮🇳 Hindi", callback_data="setlang_hi"), types.InlineKeyboardButton("🇺🇸 English", callback_data="setlang_en"))
        bot.send_message(uid, STRINGS[lang]["lang_select"], reply_markup=m, parse_mode="HTML")
    elif text in ["🏆 लीडरボード", "🏆 Leaderboard"]:
        u_list = sorted(data.items(), key=lambda x: x[1].get('referrals', 0), reverse=True)[:10]
        res = STRINGS[lang]["leaderboard_header"]
        for i, (k, v) in enumerate(u_list, 1): res += f"{i}. {v['name']} - {v.get('referrals', 0)} Refs\n"
        bot.send_message(uid, res, parse_mode="HTML")
    # ... बाकी बटन्स का लॉजिक ...

# --- 6. वेब सर्वर और रनिंग ---
app = Flask('')
@app.route('/')
def home(): return "Live"
def keep_alive(): Thread(target=lambda: app.run(host='0.0.0.0', port=8080)).start()

if __name__ == "__main__":
    keep_alive()
    bot.remove_webhook()
    time.sleep(1)
    while True: # Conflict और क्रैश रोकने के लिए लूप
        try:
            bot.polling(none_stop=True, skip_pending=True, timeout=60)
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(5)
            
