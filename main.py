import telebot
from telebot import types
import json
import os
import re
import time
import random
from flask import Flask, request

# --- 1. CONFIGURATION ---
API_TOKEN = os.getenv('API_TOKEN')
ADMIN_ID = "8114779182"
WEBHOOK_URL = os.getenv('RENDER_EXTERNAL_URL') 

bot = telebot.TeleBot(API_TOKEN)
app = Flask(__name__)

# DATA FILES
DB_FILE = 'users.json'
COURSE_DB = 'courses.json'
SALES_FILE = 'sales_log.json'
WD_FILE = 'withdrawals_log.json'
SETTINGS_FILE = 'settings.json'

# DEFAULT SETTINGS
DEFAULT_UPI = "anand1312@fam" 

# --- 2. STRINGS ---
STRINGS = {
    "hi": {
        "welcome": "नमस्ते {name}! <b>Skillclub</b> में आपका स्वागत है। 🙏\n\n🚀 <b>शुरू करने के लिए स्टेप्स:</b>\n1️⃣ '📚 कोर्स खरीदें' बटन दबाएं।\n2️⃣ पेमेंट करें।\n3️⃣ स्क्रीनशॉट भेजें।\n4️⃣ '🔗 इनवाइट लिंक' से लिंक बनाएं।",
        "lang_select": "🌐 <b>अपनी भाषा चुनें:</b>",
        "profile": "👤 <b>नाम:</b> {name}\n🏆 <b>स्टेटस:</b> {status}\n💰 <b>बैलेंस:</b> ₹{bal}\n👥 <b>रेफरल:</b> {refs}\n📅 <b>जॉइन डेट:</b> {date}",
        "buy_menu": "🎓 <b>हमारे उपलब्ध कोर्सेस चुनें:</b>",
        "payment_instruction": "🚀 <b>कोर्स:</b> {cname}\n💰 <b>कीमत:</b> ₹{price}\n\nℹ️ <b>पेमेंट निर्देश:</b>\n1. UPI: <code>{upi}</code> पर पेमेंट करें।\n2. स्क्रीनशॉट यहाँ भेजें।",
        "wallet_msg": "💰 <b>वॉलेट बैलेंस:</b> ₹{bal}\n⚠️ <b>न्यूनतम विड्रॉल:</b> ₹500",
        "invite": "🔥 <b>आपका लिंक:</b>\n{link}\n\nइसे प्रमोट करें और अर्न करें!",
        "invite_locked": "❌ <b>लिंक लॉक है!</b>\nलिंक जेनरेट करने के लिए पहले <b>कम से कम एक कोर्स खरीदें</b>।",
        "leaderboard": "🏆 <b>टॉप 10 लीडरबोर्ड:</b>\n\n{list}",
        "support_msg": "📞 <b>सपोर्ट सेंटर:</b>",
        "btns": ["👤 प्रोफाइल", "🔗 इनवाइट लिंक", "💰 वॉलेट", "📚 कोर्स खरीदें", "🏆 लीडरबोर्ड", "📞 सहायता", "⚙️ सेटिंग्स"]
    },
    "en": {
        "welcome": "Hello {name}! Welcome to <b>Skillclub</b>. 🙏",
        "lang_select": "🌐 <b>Choose language:</b>",
        "profile": "👤 <b>Name:</b> {name}\n🏆 <b>Status:</b> {status}\n💰 <b>Balance:</b> ₹{bal}\n👥 <b>Refs:</b> {refs}\n📅 <b>Joined:</b> {date}",
        "buy_menu": "🎓 <b>Available Courses:</b>",
        "payment_instruction": "🚀 <b>Course:</b> {cname}\n💰 <b>Price:</b> ₹{price}\n\nℹ️ Pay to <code>{upi}</code> and send screenshot.",
        "wallet_msg": "💰 <b>Balance:</b> ₹{bal}\n⚠️ <b>Min Withdrawal:</b> ₹500",
        "invite": "🔥 <b>Your Link:</b>\n{link}",
        "invite_locked": "❌ <b>Locked!</b> Buy a course first to get your link.",
        "leaderboard": "🏆 <b>Top 10:</b>\n\n{list}",
        "support_msg": "📞 <b>Support:</b>",
        "btns": ["👤 Profile", "🔗 Invite Link", "💰 Wallet", "📚 Buy Course", "🏆 Leaderboard", "📞 Support", "⚙️ Settings"]
    }
}

# --- 3. DATA MANAGER ---
def load_json(filename):
    if not os.path.exists(filename):
        default = {"upi": DEFAULT_UPI, "buttons": []} if filename == SETTINGS_FILE else {}
        if "log" in filename: default = []
        with open(filename, 'w') as f: json.dump(default, f)
        return default
    try:
        with open(filename, 'r') as f: return json.load(f)
    except: return {}

def save_json(filename, data):
    with open(filename, 'w') as f: json.dump(data, f, indent=4)

def get_upi():
    return load_json(SETTINGS_FILE).get("upi", DEFAULT_UPI)

# --- 4. KEYBOARDS ---
def get_main_menu(uid, lang):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    b = STRINGS[lang]["btns"]
    markup.add(b[0], b[1])
    markup.add(b[2], b[3])
    markup.add(b[4], b[5])
    markup.add(b[6]) # Settings
    if str(uid) == ADMIN_ID: markup.add("🛠 Admin Panel")
    return markup

# --- 5. HANDLERS ---
@bot.message_handler(commands=['start'])
def start_cmd(message):
    data, uid = load_json(DB_FILE), str(message.chat.id)
    if uid not in data:
        args = message.text.split()
        ref = args[1] if len(args) > 1 else None
        data[uid] = {
            "name": message.from_user.first_name, 
            "balance": 0, "referred_by": ref, 
            "status": "Free", "referrals": 0, 
            "lang": "hi", "purchased": [], 
            "join_date": time.strftime("%Y-%m-%d")
        }
        save_json(DB_FILE, data)
    
    # Auto-fix for old users missing join_date
    if not data[uid].get("join_date"):
        data[uid]["join_date"] = time.strftime("%Y-%m-%d")
        save_json(DB_FILE, data)

    lang = data[uid].get("lang", "hi")
    bot.send_message(uid, STRINGS[lang]["welcome"].format(name=data[uid]["name"]), reply_markup=get_main_menu(uid, lang), parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: True)
def callbacks(call):
    uid, data = str(call.message.chat.id), load_json(DB_FILE)
    if call.data.startswith("setlang_"):
        data[uid]["lang"] = call.data.split('_')[1]
        save_json(DB_FILE, data)
        bot.send_message(uid, "✅ Language Updated!", reply_markup=get_main_menu(uid, data[uid]["lang"]))
    
    elif call.data.startswith("buyinfo_"):
        cid = call.data.split('_')[1]
        c = load_json(COURSE_DB).get(cid)
        if c:
            data[uid]["pending_buy"] = cid
            save_json(DB_FILE, data)
            bot.send_message(uid, STRINGS[data[uid].get("lang", "hi")]["payment_instruction"].format(cname=c['name'], price=c['price'], upi=get_upi()), parse_mode="HTML")

    elif call.data.startswith("app_"):
        parts = call.data.split('_')
        t_id, cid = parts[1], parts[2]
        u_data = load_json(DB_FILE)
        course = load_json(COURSE_DB).get(cid)
        if t_id in u_data and course:
            u_data[t_id]["status"] = "Paid"
            if cid not in u_data[t_id].get("purchased", []):
                u_data[t_id].setdefault("purchased", []).append(cid)
            
            # Commission logic
            ref_id = u_data[t_id].get("referred_by")
            if ref_id and ref_id in u_data:
                u_data[ref_id]["balance"] += course.get("l1", 0)
                u_data[ref_id]["referrals"] = u_data[ref_id].get("referrals", 0) + 1
            
            save_json(DB_FILE, u_data)
            bot.send_message(t_id, "🥳 <b>Payment Approved!</b> Course unlocked.", parse_mode="HTML")
            bot.edit_message_caption("✅ APPROVED", ADMIN_ID, call.message.message_id)

@bot.message_handler(content_types=['photo'])
def handle_payment(message):
    uid = str(message.chat.id)
    data = load_json(DB_FILE)
    cid = data.get(uid, {}).get("pending_buy")
    if cid:
        c = load_json(COURSE_DB).get(cid)
        caption = f"💰 <b>Payment</b>\nUser: {message.from_user.first_name} ({uid})\nCourse: {c['name']}"
        m = types.InlineKeyboardMarkup()
        m.add(types.InlineKeyboardButton("✅ Approve", callback_data=f"app_{uid}_{cid}"))
        bot.send_photo(ADMIN_ID, message.photo[-1].file_id, caption=caption, reply_markup=m, parse_mode="HTML")
        bot.send_message(uid, "✅ Screenshot received! Wait for approval.")

@bot.message_handler(func=lambda m: True)
def handle_menu(message):
    uid, text = str(message.chat.id), message.text
    data = load_json(DB_FILE)
    if uid not in data: return
    lang = data[uid].get("lang", "hi")

    # --- PROFILE ---
    if text in ["👤 प्रोफाइल", "👤 Profile"]:
        p = data[uid]
        date = p.get("join_date", time.strftime("%Y-%m-%d"))
        bot.send_message(uid, STRINGS[lang]["profile"].format(name=p['name'], status=p['status'], refs=p.get('referrals', 0), bal=p['balance'], date=date), parse_mode="HTML")

    # --- INVITE LINK (STRICT) ---
    elif text in ["🔗 इनवाइट लिंक", "🔗 Invite Link"]:
        # यहाँ चेक होता है कि क्या कोई कोर्स खरीदा गया है
        if data[uid].get("purchased") and len(data[uid]["purchased"]) > 0:
            link = f"https://t.me/{bot.get_me().username}?start={uid}"
            bot.send_message(uid, STRINGS[lang]["invite"].format(link=link), parse_mode="HTML")
        else:
            bot.send_message(uid, STRINGS[lang]["invite_locked"], parse_mode="HTML")

    elif text in ["📚 कोर्स खरीदें", "📚 Buy Course"]:
        courses = load_json(COURSE_DB)
        m = types.InlineKeyboardMarkup()
        for cid, info in courses.items():
            m.add(types.InlineKeyboardButton(f"🛒 {info['name']} - ₹{info['price']}", callback_data=f"buyinfo_{cid}"))
        bot.send_message(uid, STRINGS[lang]["buy_menu"], reply_markup=m, parse_mode="HTML")

    elif text in ["⚙️ सेटिंग्स", "⚙️ Settings"]:
        m = types.InlineKeyboardMarkup()
        m.add(types.InlineKeyboardButton("🇮🇳 Hindi", callback_data="setlang_hi"), types.InlineKeyboardButton("🇺🇸 English", callback_data="setlang_en"))
        bot.send_message(uid, STRINGS[lang]["lang_select"], reply_markup=m, parse_mode="HTML")

    elif text == "🛠 Admin Panel" and uid == ADMIN_ID:
        m = types.ReplyKeyboardMarkup(resize_keyboard=True)
        m.add("📊 Stats", "📢 Broadcast")
        m.add("🔙 Back")
        bot.send_message(uid, "Admin Panel:", reply_markup=m)

# --- 6. WEBHOOK SETUP (FIXED) ---
@app.route('/' + API_TOKEN, methods=['POST'])
def getMessage():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "!", 200

@app.route("/")
def webhook():
    bot.remove_webhook() # पुराने सारे Conflict हटा देगा
    time.sleep(1)
    bot.set_webhook(url=WEBHOOK_URL + '/' + API_TOKEN)
    return "Bot is running perfectly!", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 10000)))
