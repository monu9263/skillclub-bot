import telebot
from telebot import types
import json
import os
import re
from flask import Flask
from threading import Thread
import time
import random

# --- 1. कॉन्फ़िगरेशन (CONFIGURATION) ---
API_TOKEN = os.getenv('API_TOKEN')
ADMIN_ID = "8114779182"  #

bot = telebot.TeleBot(API_TOKEN)
app = Flask('')

# डेटा फाइल्स
DB_FILE = 'users.json'
COURSE_DB = 'courses.json'
SALES_FILE = 'sales_log.json'
WD_FILE = 'withdrawals_log.json'
SETTINGS_FILE = 'settings.json'

# डिफॉल्ट सेटिंग्स
ADMIN_UPI = "anand1312@fam" 
WELCOME_PHOTO = "https://files.catbox.moe/0v601y.png" 

# --- 2. भाषा और मैसेज (STRINGS) ---
STRINGS = {
    "hi": {
        "welcome": "नमस्ते {name}! <b>Skillclub</b> में आपका स्वागत है। 🙏\n\n🚀 <b>शुरू करने के लिए स्टेप्स:</b>\n1️⃣ '📚 कोर्स खरीदें' बटन दबाएं।\n2️⃣ पेमेंट करें।\n3️⃣ स्क्रीनशॉट भेजें।\n4️⃣ '🔗 इनवाइट लिंक' से लिंक बनाएं।",
        "profile": "👤 <b>नाम:</b> {name}\n🏆 <b>स्टेटस:</b> {status}\n💰 <b>बैलेंस:</b> ₹{bal}\n👥 <b>रेफरल:</b> {refs}\n📅 <b>जॉइन डेट:</b> {date}",
        "buy_menu": "🎓 <b>हमारे उपलब्ध कोर्सेस चुनें:</b>",
        "payment_instruction": "🚀 <b>कोर्स:</b> {cname}\n💰 <b>कीमत:</b> ₹{price}\n\n1. UPI: <code>{upi}</code> पर पेमेंट करें।\n2. स्क्रीनशॉट इसी बोट में भेजें।",
        "wallet_msg": "💰 <b>वॉलेट बैलेंस:</b> ₹{bal}\n📉 न्यूनतम विड्रॉल: ₹500",
        "invite": "🔥 <b>आपका लिंक:</b>\n{link}\n\nइसे प्रमोट करें और डेली अर्न करें!",
        "invite_locked": "❌ <b>लिंक लॉक है!</b>\nपहले <b>कम से कम एक कोर्स खरीदें</b>।",
        "support_msg": "📞 <b>सपोर्ट सेंटर:</b>\nनीचे दिए गए विकल्पों पर क्लिक करें:",
        "btns": ["👤 प्रोफाइल", "🔗 इनवाइट लिंक", "💰 वॉलेट", "📚 कोर्स खरीदें", "📞 सहायता", "⚙️ सेटिंग्स"]
    },
    "en": {
        "welcome": "Hello {name}! Welcome to <b>Skillclub</b>. 🙏",
        "profile": "👤 <b>Name:</b> {name}\n🏆 <b>Status:</b> {status}\n💰 <b>Balance:</b> ₹{bal}\n👥 <b>Referrals:</b> {refs}\n📅 <b>Joined:</b> {date}",
        "buy_menu": "🎓 <b>Available Courses:</b>",
        "payment_instruction": "🚀 <b>Course:</b> {cname}\n💰 <b>Price:</b> ₹{price}\n\nPay to UPI: <code>{upi}</code>",
        "wallet_msg": "💰 <b>Wallet Balance:</b> ₹{bal}",
        "invite": "🔥 <b>Your Link:</b>\n{link}",
        "invite_locked": "❌ <b>Locked!</b> Buy course first.",
        "support_msg": "📞 <b>Support Center:</b>",
        "btns": ["👤 Profile", "🔗 Invite Link", "💰 Wallet", "📚 Buy Course", "📞 Support", "⚙️ Settings"]
    }
}

# --- 3. डेटा मैनेजर ---
def load_json(filename):
    if not os.path.exists(filename):
        default = {"buttons": []} if filename == SETTINGS_FILE else {}
        with open(filename, 'w') as f: json.dump(default, f)
        return default
    try:
        with open(filename, 'r') as f: return json.load(f)
    except: return {}

def save_json(filename, data):
    with open(filename, 'w') as f: json.dump(data, f, indent=4)

def log_transaction(filename, amount):
    logs = load_json(filename)
    if not isinstance(logs, list): logs = []
    logs.append({"amount": amount, "date": time.strftime("%Y-%m-%d"), "month": time.strftime("%Y-%m")})
    save_json(filename, logs)

# --- 4. एडमिन स्टेट्स (Full Stats Logic) ---
def get_stats():
    data = load_json(DB_FILE)
    sales = load_json(SALES_FILE)
    today, month = time.strftime("%Y-%m-%d"), time.strftime("%Y-%m")
    t_sell, m_sell, l_sell = 0, 0, 0
    for s in (sales if isinstance(sales, list) else []):
        amt = s.get('amount', 0)
        l_sell += amt
        if s.get('date') == today: t_sell += amt
        if s.get('month') == month: m_sell += amt
    return (f"📊 <b>Skillclub Stats</b>\n\n💰 Today: ₹{t_sell}\n📅 Month: ₹{m_sell}\n📈 Total: ₹{l_sell}\n👥 Users: {len(data)}")

# --- 5. मेनू और स्टार्ट (Joined Date Fix Included) ---
def get_main_menu(uid, lang):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    b = STRINGS[lang]["btns"]
    markup.add(b[0], b[1]).add(b[2], b[3]).add(b[4], b[5])
    if str(uid) == ADMIN_ID: markup.add("🛠 Admin Panel")
    return markup

@bot.message_handler(commands=['start'])
def start_cmd(message):
    data, uid = load_json(DB_FILE), str(message.chat.id)
    if uid not in data:
        args = message.text.split()
        data[uid] = {"name": message.from_user.first_name, "balance": 0, "status": "Free", "referrals": 0, "lang": "hi", "purchased": [], "join_date": time.strftime("%Y-%m-%d")}
    
    # Fix: Always ensure date is present, not "Old"
    if data[uid].get("join_date") in ["Old", None]:
        data[uid]["join_date"] = time.strftime("%Y-%m-%d")
        
    save_json(DB_FILE, data)
    lang = data[uid].get("lang", "hi")
    bot.send_message(uid, STRINGS[lang]["welcome"].format(name=data[uid]["name"]), reply_markup=get_main_menu(uid, lang), parse_mode="HTML")

# --- 6. एडमिन फंक्शन्स (Broadcast, Add Course, Support Settings) ---
def process_broadcast(message):
    data = load_json(DB_FILE)
    count = 0
    for u in data:
        try:
            bot.copy_message(u, ADMIN_ID, message.message_id)
            count += 1
        except: continue
    bot.send_message(ADMIN_ID, f"✅ Broadcast sent to {count} users.")

# Step-by-step Course Adding
def add_course_start(message):
    msg = bot.send_message(ADMIN_ID, "📝 कोर्स का नाम (Course Name) लिखें:")
    bot.register_next_step_handler(msg, process_c_price)

def process_c_price(message):
    name = message.text
    msg = bot.send_message(ADMIN_ID, f"💰 '{name}' की कीमत (Price) लिखें:")
    bot.register_next_step_handler(msg, process_c_l1, name)

def process_c_l1(message, name):
    price = int(re.sub(r'\D', '', message.text))
    msg = bot.send_message(ADMIN_ID, "👥 Level 1 Commission (INR):")
    bot.register_next_step_handler(msg, process_c_l2, name, price)

def process_c_l2(message, name, price):
    l1 = int(re.sub(r'\D', '', message.text))
    msg = bot.send_message(ADMIN_ID, "👥 Level 2 Commission (INR):")
    bot.register_next_step_handler(msg, finalize_c, name, price, l1)

def finalize_c(message, name, price, l1):
    l2 = int(re.sub(r'\D', '', message.text))
    msg = bot.send_message(ADMIN_ID, "🔗 डाउनलोड लिंक भेजें:")
    bot.register_next_step_handler(msg, save_c, name, price, l1, l2)

def save_c(message, name, price, l1, l2):
    courses = load_json(COURSE_DB)
    cid = str(random.randint(1000, 9999))
    courses[cid] = {"name": name, "price": price, "l1": l1, "l2": l2, "link": message.text}
    save_json(COURSE_DB, courses)
    bot.send_message(ADMIN_ID, f"✅ कोर्स '{name}' सफलतापूर्वक जुड़ गया!")

# Support Button Adding
def add_supp_name(message):
    msg = bot.send_message(ADMIN_ID, "📝 बटन का नाम लिखें:")
    bot.register_next_step_handler(msg, add_supp_link)

def add_supp_link(message):
    name = message.text
    msg = bot.send_message(ADMIN_ID, f"🔗 '{name}' का URL भेजें:")
    bot.register_next_step_handler(msg, save_supp, name)

def save_supp(message, name):
    settings = load_json(SETTINGS_FILE)
    settings.setdefault("buttons", []).append({"name": name, "url": message.text})
    save_json(SETTINGS_FILE, settings)
    bot.send_message(ADMIN_ID, f"✅ बटन '{name}' जुड़ गया!")

# --- 7. मेन हैंडलर ---
@bot.message_handler(func=lambda m: True)
def handle_all(message):
    uid, text = str(message.chat.id), message.text
    data = load_json(DB_FILE)
    if uid not in data: return
    lang = data[uid].get("lang", "hi")

    # ADMIN PANEL
    if text == "🛠 Admin Panel" and uid == ADMIN_ID:
        m = types.ReplyKeyboardMarkup(resize_keyboard=True)
        m.add("📊 Stats", "📢 Broadcast").add("📥 Export Data", "➕ Add Course").add("📞 Support Settings", "🔙 वापस")
        bot.send_message(uid, "🛠 Admin Panel:", reply_markup=m)
    
    elif text == "📊 Stats" and uid == ADMIN_ID: bot.send_message(uid, get_stats(), parse_mode="HTML")
    elif text == "📢 Broadcast" and uid == ADMIN_ID:
        msg = bot.send_message(uid, "📢 मैसेज भेजें:")
        bot.register_next_step_handler(msg, process_broadcast)
    elif text == "➕ Add Course" and uid == ADMIN_ID: add_course_start(message)
    elif text == "📞 Support Settings" and uid == ADMIN_ID:
        m = types.InlineKeyboardMarkup()
        m.add(types.InlineKeyboardButton("➕ Add Button", callback_data="adm_add"), types.InlineKeyboardButton("🗑️ Clear All", callback_data="adm_clear"))
        bot.send_message(uid, "⚙️ सपोर्ट बटन सेटिंग्स:", reply_markup=m)
    elif text == "📥 Export Data" and uid == ADMIN_ID:
        bot.send_document(uid, open(DB_FILE, 'rb'))

    # USER BUTTONS
    elif text in ["👤 प्रोफाइल", "👤 Profile"]:
        p = data[uid]
        bot.send_message(uid, STRINGS[lang]["profile"].format(name=p['name'], status=p['status'], refs=p.get('referrals', 0), bal=p['balance'], date=p.get('join_date')), parse_mode="HTML")

    elif text in ["💰 वॉलेट", "💰 Wallet"]:
        bal = data[uid].get('balance', 0)
        bot.send_message(uid, STRINGS[lang]["wallet_msg"].format(bal=bal), parse_mode="HTML")

    elif text in ["📚 कोर्स खरीदें", "📚 Buy Course"]:
        courses = load_json(COURSE_DB)
        purchased = data[uid].get("purchased", [])
        m = types.InlineKeyboardMarkup()
        for cid, info in courses.items():
            if cid in purchased: m.add(types.InlineKeyboardButton(f"📥 Download {info['name']}", url=info['link']))
            else: m.add(types.InlineKeyboardButton(f"🛒 {info['name']} - ₹{info['price']}", callback_data=f"buyinfo_{cid}"))
        bot.send_message(uid, STRINGS[lang]["buy_menu"], reply_markup=m, parse_mode="HTML")

    elif text in ["📞 सहायता", "📞 Support"]:
        settings = load_json(SETTINGS_FILE)
        btns = settings.get("buttons", [])
        if not btns:
            bot.send_message(uid, "⚠️ कोई सपोर्ट उपलब्ध नहीं है।") # Now empty by default
        else:
            m = types.InlineKeyboardMarkup()
            for b in btns: m.add(types.InlineKeyboardButton(f"👉 {b['name']}", url=b['url']))
            bot.send_message(uid, STRINGS[lang]["support_msg"], reply_markup=m, parse_mode="HTML")

    elif text in ["⚙️ सेटिंग्स", "⚙️ Settings"]:
        m = types.InlineKeyboardMarkup()
        m.add(types.InlineKeyboardButton("Hindi", callback_data="set_hi"), types.InlineKeyboardButton("English", callback_data="set_en"))
        bot.send_message(uid, STRINGS[lang]["lang_select"], reply_markup=m)

    elif text in ["🔗 इनवाइट लिंक", "🔗 Invite Link"]:
        if not data[uid].get("purchased", []): bot.send_message(uid, STRINGS[lang]["invite_locked"], parse_mode="HTML")
        else:
            link = f"https://t.me/{bot.get_me().username}?start={uid}"
            bot.send_message(uid, STRINGS[lang]["invite"].format(link=link), parse_mode="HTML")

    elif text in ["🔙 वापस", "🔙 Back"]:
        bot.send_message(uid, "🔙 मुख्य मेनू", reply_markup=get_main_menu(uid, lang))

# --- 8. कॉल-बैक ---
@bot.callback_query_handler(func=lambda call: True)
def calls(call):
    uid, data = str(call.message.chat.id), load_json(DB_FILE)
    if call.data.startswith("set_"):
        data[uid]["lang"] = call.data.split('_')[1]
        save_json(DB_FILE, data)
        bot.send_message(uid, "✅ Language Updated!", reply_markup=get_main_menu(uid, data[uid]["lang"]))
    elif call.data == "adm_add": add_supp_name(call.message)
    elif call.data == "adm_clear":
        save_json(SETTINGS_FILE, {"buttons": []})
        bot.send_message(uid, "✅ साफ़ कर दिया गया!")
    elif call.data.startswith("buyinfo_"):
        cid = call.data.split('_')[1]
        c = load_json(COURSE_DB).get(cid)
        if c:
            bot.send_message(uid, STRINGS[data[uid].get("lang", "hi")]["payment_instruction"].format(cname=c['name'], price=c['price'], upi=ADMIN_UPI), parse_mode="HTML")

# --- 9. फोटो हैंडलर (Payment Approval) ---
@bot.message_handler(content_types=['photo'])
def handle_p(message):
    bot.send_photo(ADMIN_ID, message.photo[-1].file_id, caption=f"📩 <b>New Payment Screenshot</b>\nUser: {message.chat.id}", parse_mode="HTML")
    bot.send_message(message.chat.id, "✅ स्क्रीनशॉट मिल गया! एडमिन के अप्रूवल का इंतज़ार करें।")

# --- 10. रेंडर सर्वर ---
@app.route('/')
def home(): return "Bot Live"

def run(): app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))

if __name__ == "__main__":
    Thread(target=run).start()
    bot.polling(none_stop=True)
