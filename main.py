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
# Render automatically provides this URL
WEBHOOK_URL = os.getenv('RENDER_EXTERNAL_URL') 

if not API_TOKEN:
    print("❌ ERROR: API_TOKEN not found!")

bot = telebot.TeleBot(API_TOKEN)
app = Flask(__name__)

# FILES
DB_FILE = 'users.json'
COURSE_DB = 'courses.json'
SALES_FILE = 'sales_log.json'
WD_FILE = 'withdrawals_log.json'
SETTINGS_FILE = 'settings.json'

# DEFAULTS
DEFAULT_UPI = "anand1312@fam" 
WELCOME_PHOTO = "https://files.catbox.moe/0v601y.png" 

# --- 2. STRINGS ---
STRINGS = {
    "hi": {
        "welcome": "नमस्ते {name}! <b>Skillclub</b> में आपका स्वागत है। 🙏\n\n🚀 <b>शुरू करने के लिए स्टेप्स:</b>\n1️⃣ '📚 कोर्स खरीदें' बटन दबाएं।\n2️⃣ पेमेंट करें।\n3️⃣ स्क्रीनशॉट भेजें।\n4️⃣ '🔗 इनवाइट लिंक' से लिंक बनाएं。",
        "lang_select": "🌐 <b>अपनी भाषा चुनें:</b>",
        "lang_updated": "✅ भाषा <b>Hindi</b> में बदल दी गई है।",
        "profile": "👤 <b>नाम:</b> {name}\n🏆 <b>स्टेटस:</b> {status}\n💰 <b>बैलेंस:</b> ₹{bal}\n👥 <b>रेफरल:</b> {refs}\n📅 <b>जॉइन डेट:</b> {date}",
        "buy_menu": "🎓 <b>हमारे उपलब्ध कोर्सेस चुनें:</b>",
        "payment_instruction": "🚀 <b>कोर्स:</b> {cname}\n💰 <b>कीमत:</b> ₹{price}\n\nℹ️ <b>पेमेंट निर्देश:</b>\n1. नीचे दी गई UPI ID पर पेमेंट करें:\n   👉 <code>{upi}</code>\n\n2. पेमेंट का <b>स्क्रीनशॉट (Screenshot)</b> लें।\n3. वह स्क्रीनशॉट <b>इसी बोट में भेजें।</b>",
        "wallet_msg": "💰 <b>वॉलेट बैलेंस:</b> ₹{bal}\n⚠️ <b>न्यूनतम विड्रॉल:</b> ₹500",
        "invite": "🔥 <b>आपका लिंक:</b>\n{link}\n\nइसे प्रमोट करें और डेली अर्न करें!",
        "invite_locked": "❌ <b>लिंक लॉक है!</b>\nपहले <b>कम से कम एक कोर्स खरीदें</b>।",
        "wd_success": "🥳 <b>Payout Successful!</b>",
        "support_msg": "📞 <b>सपोर्ट सेंटर:</b>\nनीचे दिए गए विकल्पों पर क्लिक करें:",
        "leaderboard": "🏆 <b>टॉप 10 लीडरबोर्ड (Top Referrers):</b>\n\n{list}",
        "btns": ["👤 प्रोफाइल", "🔗 इनवाइट लिंक", "💰 वॉलेट", "📚 कोर्स खरीदें", "🏆 लीडरबोर्ड", "📞 सहायता"]
    },
    "en": {
        "welcome": "Hello {name}! Welcome to <b>Skillclub</b>. 🙏\n\n🚀 <b>Steps to Start:</b>\n1️⃣ Click '📚 Buy Course'.\n2️⃣ Pay via UPI.\n3️⃣ Send Screenshot here.",
        "lang_select": "🌐 <b>Choose your language:</b>",
        "lang_updated": "✅ Language updated to <b>English</b>.",
        "profile": "👤 <b>Name:</b> {name}\n🏆 <b>Status:</b> {status}\n💰 <b>Balance:</b> ₹{bal}\n👥 <b>Referrals:</b> {refs}\n📅 <b>Joined:</b> {date}",
        "buy_menu": "🎓 <b>Available Courses:</b>",
        "payment_instruction": "🚀 <b>Course:</b> {cname}\n💰 <b>Price:</b> ₹{price}\n\nℹ️ <b>Instructions:</b>\n1. Pay to UPI: <code>{upi}</code>\n2. Take a Screenshot.\n3. <b>Send the screenshot here.</b>",
        "wallet_msg": "💰 <b>Wallet Balance:</b> ₹{bal}\n⚠️ <b>Min Withdrawal:</b> ₹500",
        "invite": "🔥 <b>Your Link:</b>\n{link}",
        "invite_locked": "❌ <b>Locked!</b> Buy course first.",
        "wd_success": "🥳 <b>Payout Successful!</b>",
        "support_msg": "📞 <b>Support Center:</b>",
        "leaderboard": "🏆 <b>Top 10 Leaderboard:</b>\n\n{list}",
        "btns": ["👤 Profile", "🔗 Invite Link", "💰 Wallet", "📚 Buy Course", "🏆 Leaderboard", "📞 Support"]
    }
}

# --- 3. DATA MANAGER ---
def load_json(filename):
    if not os.path.exists(filename):
        if filename == SETTINGS_FILE: default = {"upi": DEFAULT_UPI, "buttons": []}
        elif "log" in filename: default = []
        else: default = {}
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

def get_upi():
    return load_json(SETTINGS_FILE).get("upi", DEFAULT_UPI)

# --- 4. ADMIN STATS ---
def get_stats():
    data = load_json(DB_FILE)
    sales = load_json(SALES_FILE)
    wd = load_json(WD_FILE)
    today, month = time.strftime("%Y-%m-%d"), time.strftime("%Y-%m")
    
    t_sell, m_sell, l_sell = 0, 0, 0
    for s in (sales if isinstance(sales, list) else []):
        amt = s.get('amount', 0)
        l_sell += amt
        if s.get('date') == today: t_sell += amt
        if s.get('month') == month: m_sell += amt
        
    t_wd, l_wd = 0, 0
    for w in (wd if isinstance(wd, list) else []):
        amt = w.get('amount', 0)
        l_wd += amt
        if w.get('date') == today: t_wd += amt

    return (f"📊 <b>Skillclub Master Stats</b>\n\n"
            f"💰 <b>Today Sales:</b> ₹{t_sell}\n"
            f"📅 <b>Monthly Sales:</b> ₹{m_sell}\n"
            f"📈 <b>Total Sales:</b> ₹{l_sell}\n\n"
            f"💸 <b>Today Payout:</b> ₹{t_wd}\n"
            f"🏧 <b>Total Payout:</b> ₹{l_wd}\n\n"
            f"👥 <b>Total Users:</b> {len(data)}\n"
            f"✅ <b>Paid Users:</b> {sum(1 for u in data.values() if u.get('status') == 'Paid')}")
    # --- 5. MAIN MENU ---
def get_main_menu(uid, lang):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    b = STRINGS[lang]["btns"]
    markup.add(b[0], b[1])
    markup.add(b[2], b[3])
    markup.add(b[4], b[5])
    if str(uid) == ADMIN_ID: markup.add("🛠 Admin Panel")
    return markup

@bot.message_handler(commands=['start'])
def start_cmd(message):
    data, uid = load_json(DB_FILE), str(message.chat.id)
    if uid not in data:
        args = message.text.split()
        ref = args[1] if len(args) > 1 else None
        data[uid] = {"name": message.from_user.first_name, "balance": 0, "referred_by": ref, "status": "Free", "referrals": 0, "lang": "hi", "purchased": [], "join_date": time.strftime("%Y-%m-%d")}
    
    if data[uid].get("join_date") in ["Old", None]:
        data[uid]["join_date"] = time.strftime("%Y-%m-%d")
        
    save_json(DB_FILE, data)
    lang = data[uid].get("lang", "hi")
    
    try:
        bot.send_photo(uid, WELCOME_PHOTO, caption=STRINGS[lang]["welcome"].format(name=data[uid]["name"]), reply_markup=get_main_menu(uid, lang), parse_mode="HTML")
    except:
        bot.send_message(uid, STRINGS[lang]["welcome"].format(name=data[uid]["name"]), reply_markup=get_main_menu(uid, lang), parse_mode="HTML")

# --- 6. ADMIN FUNCTIONS ---

def process_broadcast(message):
    data = load_json(DB_FILE)
    count = 0
    bot.send_message(ADMIN_ID, "⏳ Broadcasting...")
    for uid in data:
        try:
            if message.content_type == 'text':
                text = f"📢 <b>ANNOUNCEMENT</b> 📢\n\n{message.text}"
                bot.send_message(uid, text, parse_mode="HTML")
            elif message.content_type == 'photo':
                caption = f"📢 <b>ANNOUNCEMENT</b> 📢\n\n{message.caption if message.caption else ''}"
                bot.send_photo(uid, message.photo[-1].file_id, caption=caption, parse_mode="HTML")
            count += 1
            time.sleep(0.05)
        except: continue
    bot.send_message(ADMIN_ID, f"✅ Sent to {count} users.")

def add_course_start(message):
    msg = bot.send_message(ADMIN_ID, "📝 Course Name:")
    bot.register_next_step_handler(msg, process_c_price)

def process_c_price(message):
    name = message.text
    msg = bot.send_message(ADMIN_ID, f"💰 Price for '{name}':")
    bot.register_next_step_handler(msg, process_c_l1, name)

def process_c_l1(message, name):
    try: price = int(re.sub(r'\D', '', message.text))
    except: price = 0
    msg = bot.send_message(ADMIN_ID, "👥 Level 1 Commission:")
    bot.register_next_step_handler(msg, process_c_l2, name, price)

def process_c_l2(message, name, price):
    try: l1 = int(re.sub(r'\D', '', message.text))
    except: l1 = 0
    msg = bot.send_message(ADMIN_ID, "👥 Level 2 Commission:")
    bot.register_next_step_handler(msg, finalize_c, name, price, l1)

def finalize_c(message, name, price, l1):
    try: l2 = int(re.sub(r'\D', '', message.text))
    except: l2 = 0
    msg = bot.send_message(ADMIN_ID, "🔗 Download Link:")
    bot.register_next_step_handler(msg, save_c, name, price, l1, l2)

def save_c(message, name, price, l1, l2):
    courses = load_json(COURSE_DB)
    cid = str(random.randint(1000, 9999))
    courses[cid] = {"name": name, "price": price, "l1": l1, "l2": l2, "link": message.text}
    save_json(COURSE_DB, courses)
    bot.send_message(ADMIN_ID, f"✅ Course '{name}' Added!")

def add_supp_name(message):
    name = message.text
    msg = bot.send_message(ADMIN_ID, f"🔗 Enter Link (URL) for '{name}':")
    bot.register_next_step_handler(msg, add_supp_link, name)

def add_supp_link(message, name):
    link = message.text
    settings = load_json(SETTINGS_FILE)
    settings.setdefault("buttons", []).append({"name": name, "url": link})
    save_json(SETTINGS_FILE, settings)
    bot.send_message(ADMIN_ID, f"✅ Button '{name}' Added!")

def change_upi_process(message):
    new_upi = message.text.strip()
    settings = load_json(SETTINGS_FILE)
    settings["upi"] = new_upi
    save_json(SETTINGS_FILE, settings)
    bot.send_message(ADMIN_ID, f"✅ <b>UPI Updated!</b>\nNew UPI: <code>{new_upi}</code>", parse_mode="HTML")

def search_by_id(message):
    uid = message.text.strip()
    data = load_json(DB_FILE)
    user = data.get(uid)
    if user:
        bot.send_message(ADMIN_ID, f"🔍 <b>Found:</b>\nName: {user['name']}\nBal: {user['balance']}", parse_mode="HTML")
    else:
        bot.send_message(ADMIN_ID, "❌ User ID not found.")

def search_by_name(message):
    name_query = message.text.lower().strip()
    data = load_json(DB_FILE)
    found = []
    for uid, info in data.items():
        if name_query in info['name'].lower():
            found.append(f"🆔 {uid} | {info['name']}")
    if found:
        res = "\n".join(found[:10]) 
        bot.send_message(ADMIN_ID, f"🔍 <b>Results:</b>\n\n{res}", parse_mode="HTML")
    else:
        bot.send_message(ADMIN_ID, "❌ No user found.")

# --- 7. HANDLERS ---
@bot.callback_query_handler(func=lambda call: True)
def callbacks(call):
    uid, data = str(call.message.chat.id), load_json(DB_FILE)
    
    # LANGUAGE
    if call.data.startswith("setlang_"):
        data[uid]["lang"] = call.data.split('_')[1]
        save_json(DB_FILE, data)
        bot.send_message(uid, "✅ Language Updated!", reply_markup=get_main_menu(uid, data[uid]["lang"]))
    
    # ADMIN SUPPORT
    elif call.data == "adm_add": 
        msg = bot.send_message(uid, "📝 Button Name:")
        bot.register_next_step_handler(msg, add_supp_name)
    
    # DELETE LOGIC
    elif call.data == "adm_del_menu":
        settings = load_json(SETTINGS_FILE)
        btns = settings.get("buttons", [])
        if not btns:
            bot.send_message(uid, "❌ No buttons to delete.")
            return
        
        m = types.InlineKeyboardMarkup()
        for i, b in enumerate(btns):
            m.add(types.InlineKeyboardButton(f"🗑️ Delete: {b['name']}", callback_data=f"del_supp_{i}"))
        bot.send_message(uid, "👇 Select button to delete:", reply_markup=m)

    elif call.data.startswith("del_supp_"):
        try:
            idx = int(call.data.split('_')[2])
            settings = load_json(SETTINGS_FILE)
            if 0 <= idx < len(settings["buttons"]):
                removed = settings["buttons"].pop(idx)
                save_json(SETTINGS_FILE, settings)
                bot.send_message(uid, f"✅ Button '{removed['name']}' Deleted!")
            else:
                bot.send_message(uid, "❌ Button already deleted.")
        except:
            bot.send_message(uid, "❌ Error deleting button.")

    # MANAGE COURSES
    elif call.data == "c_add":
        add_course_start(call.message)
    elif call.data == "c_del":
        courses = load_json(COURSE_DB)
        if not courses:
            bot.send_message(uid, "❌ No courses to delete.")
            return
        m = types.InlineKeyboardMarkup()
        for cid, info in courses.items():
            m.add(types.InlineKeyboardButton(f"🗑️ {info['name']}", callback_data=f"cdelconf_{cid}"))
        bot.send_message(uid, "Select course to delete:", reply_markup=m)
    
    elif call.data.startswith("cdelconf_"):
        cid = call.data.split('_')[1]
        courses = load_json(COURSE_DB)
        if cid in courses:
            name = courses[cid]['name']
            del courses[cid]
            save_json(COURSE_DB, courses)
            bot.send_message(uid, f"✅ Course '{name}' Deleted.")
        else:
            bot.send_message(uid, "❌ Error: Course not found.")

    # SEARCH USER
    elif call.data == "s_id":
        msg = bot.send_message(uid, "🔍 Enter User ID:")
        bot.register_next_step_handler(msg, search_by_id)
    elif call.data == "s_name":
        msg = bot.send_message(uid, "🔍 Enter Name:")
        bot.register_next_step_handler(msg, search_by_name)

    # BUY INFO
    elif call.data.startswith("buyinfo_"):
        cid = call.data.split('_')[1]
        c = load_json(COURSE_DB).get(cid)
        if c:
            data[uid]["pending_buy"] = cid
            save_json(DB_FILE, data)
            current_upi = get_upi()
            bot.send_message(uid, STRINGS[data[uid].get("lang", "hi")]["payment_instruction"].format(cname=c['name'], price=c['price'], upi=current_upi), parse_mode="HTML")
            
    # PAYMENT APPROVAL
    elif call.data.startswith("app_"):
        parts = call.data.split('_')
        t_id, cid = parts[1], parts[2]
        c = load_json(COURSE_DB).get(cid)
        if c:
            u_data = load_json(DB_FILE)
            if t_id in u_data:
                u_data[t_id].setdefault("purchased", []).append(cid)
                u_data[t_id]["status"] = "Paid"
                log_transaction(SALES_FILE, c['price'])
                
                l1 = u_data[t_id].get("referred_by")
                if l1 and l1 in u_data:
                    u_data[l1]["balance"] += c.get("l1", 0)
                    u_data[l1]["referrals"] = u_data[l1].get("referrals", 0) + 1
                    l2 = u_data[l1].get("referred_by")
                    if l2 and l2 in u_data: u_data[l2]["balance"] += c.get("l2", 0)
                
                save_json(DB_FILE, u_data)
                bot.send_message(t_id, "🥳 <b>Payment Approved!</b> Course unlocked.", parse_mode="HTML")
                bot.edit_message_caption("✅ APPROVED", ADMIN_ID, call.message.message_id)

    # WITHDRAWAL
    elif call.data == "ask_wd":
        bal = data[uid].get('balance', 0)
        if bal >= 500:
            msg = bot.send_message(uid, "🏧 Enter UPI ID:")
            bot.register_next_step_handler(msg, process_withdrawal, bal)
        else:
            bot.send_message(uid, "❌ Minimum withdrawal is ₹500.")

    elif call.data.startswith("wdpay_"):
        parts = call.data.split('_')
        t_id, amt = parts[1], int(parts[2])
        u_data = load_json(DB_FILE)
        if t_id in u_data:
            u_data[t_id]["balance"] -= amt
            save_json(DB_FILE, u_data)
            log_transaction(WD_FILE, amt)
            bot.send_message(t_id, "✅ Withdrawal Successful!")
            bot.edit_message_caption(f"✅ PAID ₹{amt}", ADMIN_ID, call.message.message_id)

    elif call.data.startswith("wdrej_"):
        t_id = call.data.split('_')[1]
        bot.send_message(t_id, "❌ Withdrawal Rejected.")
        bot.edit_message_caption("❌ REJECTED", ADMIN_ID, call.message.message_id)

def process_withdrawal(message, amt):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("✅ Pay", callback_data=f"wdpay_{message.chat.id}_{amt}"),
               types.InlineKeyboardButton("❌ Reject", callback_data=f"wdrej_{message.chat.id}"))
    bot.send_message(ADMIN_ID, f"🔔 <b>WD Request: ₹{amt}</b>\nUPI: <code>{message.text}</code>", reply_markup=markup, parse_mode="HTML")
    bot.send_message(message.chat.id, "✅ Request Sent!")

@bot.message_handler(func=lambda m: True)
def handle_menu(message):
    uid, text = str(message.chat.id), message.text
    data = load_json(DB_FILE)
    if uid not in data: return
    lang = data[uid].get("lang", "hi")

    if text == "🛠 Admin Panel" and uid == ADMIN_ID:
        m = types.ReplyKeyboardMarkup(resize_keyboard=True)
        m.add("📊 Stats", "📢 Broadcast")
        m.add("📥 Export Data", "🎓 Manage Courses")
        m.add("📞 Support Settings", "👤 Search User")
        m.add("💳 Change UPI", "🔙 Back to Main Menu")
        bot.send_message(uid, "🛠 Admin Panel:", reply_markup=m)
    
    elif text == "📊 Stats" and uid == ADMIN_ID: bot.send_message(uid, get_stats(), parse_mode="HTML")
    
    elif text == "📢 Broadcast" and uid == ADMIN_ID:
        msg = bot.send_message(uid, "📢 Send Message to Broadcast:")
        bot.register_next_step_handler(msg, process_broadcast)
    
    elif text == "🎓 Manage Courses" and uid == ADMIN_ID:
        m = types.InlineKeyboardMarkup()
        m.add(types.InlineKeyboardButton("➕ Add New", callback_data="c_add"),
              types.InlineKeyboardButton("🗑️ Delete Course", callback_data="c_del"))
        bot.send_message(uid, "🎓 Course Management:", reply_markup=m)
        
    elif text == "📞 Support Settings" and uid == ADMIN_ID:
        m = types.InlineKeyboardMarkup()
        m.add(types.InlineKeyboardButton("➕ Add Button", callback_data="adm_add"), 
              types.InlineKeyboardButton("🗑️ Delete Button", callback_data="adm_del_menu"))
        bot.send_message(uid, "⚙️ Settings:", reply_markup=m)
    
    elif text == "💳 Change UPI" and uid == ADMIN_ID:
        current = get_upi()
        msg = bot.send_message(uid, f"💳 <b>Current UPI:</b> <code>{current}</code>\n\n👇 <b>Enter New UPI ID:</b>", parse_mode="HTML")
        bot.register_next_step_handler(msg, change_upi_process)

    elif text == "📥 Export Data" and uid == ADMIN_ID:
        if os.path.exists(DB_FILE): bot.send_document(uid, open(DB_FILE, 'rb'))
        if os.path.exists(SALES_FILE): bot.send_document(uid, open(SALES_FILE, 'rb'))
    
    elif text == "👤 Search User" and uid == ADMIN_ID:
        m = types.InlineKeyboardMarkup()
        m.add(types.InlineKeyboardButton("🆔 By ID", callback_data="s_id"),
              types.InlineKeyboardButton("🔤 By Name", callback_data="s_name"))
        bot.send_message(uid, "🔍 Search User By:", reply_markup=m)

    elif text in ["👤 प्रोफाइल", "👤 Profile"]:
        p = data[uid]
        j_date = p.get('join_date', time.strftime("%Y-%m-%d"))
        bot.send_message(uid, STRINGS[lang]["profile"].format(name=p['name'], status=p['status'], refs=p.get('referrals', 0), bal=p['balance'], date=j_date), parse_mode="HTML")

    elif text in ["💰 वॉलेट", "💰 Wallet"]:
        bal = data[uid].get('balance', 0)
        m = types.InlineKeyboardMarkup()
        if bal >= 500: m.add(types.InlineKeyboardButton("💸 Withdraw", callback_data="ask_wd"))
        bot.send_message(uid, STRINGS[lang]["wallet_msg"].format(bal=bal), reply_markup=m, parse_mode="HTML")

    elif text in ["📚 कोर्स खरीदें", "📚 Buy Course"]:
        courses = load_json(COURSE_DB)
        purchased = data[uid].get("purchased", [])
        m = types.InlineKeyboardMarkup()
        for cid, info in courses.items():
            if cid in purchased: m.add(types.InlineKeyboardButton(f"📥 Download {info['name']}", url=info['link']))
            else: m.add(types.InlineKeyboardButton(f"🛒 {info['name']} - ₹{info['price']}", callback_data=f"buyinfo_{cid}"))
        bot.send_message(uid, STRINGS[lang]["buy_menu"], reply_markup=m, parse_mode="HTML")

    elif text in ["🏆 लीडरबोर्ड", "🏆 Leaderboard"]:
        u_list = sorted(data.items(), key=lambda x: x[1].get('referrals', 0), reverse=True)[:10]
        res = ""
        for i, (k, v) in enumerate(u_list, 1): res += f"{i}. <b>{v['name']}</b> - {v.get('referrals', 0)} Refs\n"
        bot.send_message(uid, STRINGS[lang]["leaderboard"].format(list=res), parse_mode="HTML")

    elif text in ["📞 सहायता", "📞 Support"]:
        settings = load_json(SETTINGS_FILE)
        btns = settings.get("buttons", [])
        if not btns:
            bot.send_message(uid, "⚠️ <b>Contact Admin directly.</b>", parse_mode="HTML")
        else:
            m = types.InlineKeyboardMarkup()
            for b in btns: m.add(types.InlineKeyboardButton(f"👉 {b['name']}", url=b['url']))
            bot.send_message(uid, STRINGS[lang]["support_msg"], reply_markup=m, parse_mode="HTML")

    elif text in ["⚙️ सेटिंग्स", "⚙️ Settings"]:
        m = types.InlineKeyboardMarkup()
        m.add(types.InlineKeyboardButton("🇮🇳 Hindi", callback_data="setlang_hi"), types.InlineKeyboardButton("🇺🇸 English", callback_data="setlang_en"))
        bot.send_message(uid, STRINGS[lang]["lang_select"], reply_markup=m, parse_mode="HTML")

    elif text in ["🔗 इनवाइट लिंक", "🔗 Invite Link"]:
        if not data[uid].get("purchased", []): bot.send_message(uid, STRINGS[lang]["invite_locked"], parse_mode="HTML")
        else:
            link = f"https://t.me/{bot.get_me().username}?start={uid}"
            bot.send_message(uid, STRINGS[lang]["invite"].format(link=link), parse_mode="HTML")

    elif text in ["🔙 Back to Main Menu", "🔙 वापस"]:
        bot.send_message(uid, "🔙 Main Menu", reply_markup=get_main_menu(uid, lang))

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    uid = str(message.chat.id)
    data = load_json(DB_FILE)
    pending_cid = data.get(uid, {}).get("pending_buy")
    if pending_cid:
        courses = load_json(COURSE_DB)
        c_name = courses[pending_cid]['name'] if pending_cid in courses else "Unknown"
        m = types.InlineKeyboardMarkup()
        m.add(types.InlineKeyboardButton("✅ Approve", callback_data=f"app_{uid}_{pending_cid}"),
              types.InlineKeyboardButton("❌ Reject", callback_data=f"rej_{uid}"))
        bot.send_photo(ADMIN_ID, message.photo[-1].file_id, caption=f"📩 <b>New Payment!</b>\nUser: {uid}\nCourse: {c_name}", reply_markup=m, parse_mode="HTML")
        bot.send_message(uid, "✅ Screenshot received! Wait for approval.")

# --- 8. WEBHOOK ROUTES ---
@app.route('/' + API_TOKEN, methods=['POST'])
def getMessage():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "!", 200

@app.route("/")
def webhook():
    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL + "/" + API_TOKEN)
    return "Webhook Set!", 200

def run_server():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

if __name__ == "__main__":
    if WEBHOOK_URL:
        run_server()
    else:
        # Local fallback
        bot.remove_webhook()
        bot.polling(none_stop=True)
