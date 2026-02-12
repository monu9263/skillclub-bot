import telebot
from telebot import types
import json, os, re, time, random
from flask import Flask
from threading import Thread

# --- 1. कॉन्फ़िगरेशन (CONFIGURATION) ---
API_TOKEN = os.getenv('API_TOKEN')
ADMIN_ID = os.getenv('ADMIN_ID') # आपकी ID: 8114779182
SUPPORT_BOT_USERNAME = "SkillClubHelpBot" # आपका सपोर्ट बोट यूजरनेम (बिना @)

if not API_TOKEN or not ADMIN_ID:
    print("❌ ERROR: API_TOKEN या ADMIN_ID सेट नहीं है!")

bot = telebot.TeleBot(API_TOKEN)
app = Flask('')

# डेटा फाइल्स
DB_FILE = 'users.json'
COURSE_DB = 'courses.json'
SALES_FILE = 'sales_log.json'
WD_FILE = 'withdrawals_log.json'
SETTINGS_FILE = 'settings.json'

# डिफ़ॉल्ट सेटिंग्स
ADMIN_UPI = "anand1312@fam" 
WELCOME_PHOTO = "https://files.catbox.moe/0v601y.png" 

# --- 2. भाषा और मैसेज (STRINGS) ---
STRINGS = {
    "hi": {
        "welcome": "नमस्ते {name}! <b>Skillclub</b> में आपका स्वागत है। 🙏\n\n🚀 <b>शुरू करने के लिए स्टेप्स:</b>\n1️⃣ '📚 कोर्स खरीदें' बटन दबाएं।\n2️⃣ पेमेंट करें।\n3️⃣ स्क्रीनशॉट भेजें।\n4️⃣ '🔗 इनवाइट लिंक' से लिंक बनाएं।",
        "lang_select": "🌐 <b>अपनी भाषा चुनें / Choose your language:</b>",
        "lang_updated": "✅ भाषा <b>Hindi</b> में बदल दी गई है।",
        "profile": "👤 <b>नाम:</b> {name}\n🏆 <b>स्टेटस:</b> {status}\n💰 <b>बैलेंस:</b> ₹{bal}\n👥 <b>रेफरल:</b> {refs}\n📅 <b>जॉइन डेट:</b> {date}",
        "buy_menu": "🎓 <b>हमारे उपलब्ध कोर्सेस चुनें:</b>",
        "payment_instruction": "🚀 <b>कोर्स:</b> {cname}\n💰 <b>कीमत:</b> ₹{price}\n\n1. UPI: <code>{upi}</code> पर पेमेंट करें।\n2. स्क्रीनशॉट इसी बोट में भेजें।",
        "wallet_msg": "💰 <b>वॉलेट बैलेंस:</b> ₹{bal}\n📉 न्यूनतम विड्रॉल: ₹500",
        "invite": "🔥 <b>आपका लिंक:</b>\n{link}\n\nइसे प्रमोट करें और डेली अर्न करें!",
        "invite_locked": "❌ <b>लिंक लॉक है!</b>\nपहले <b>कम से कम एक कोर्स खरीदें</b>।",
        "wd_success": "🥳 <b>Payout Successful!</b>",
        "support_msg": "📞 <b>सपोर्ट सेंटर:</b>\n\nकिसी भी सहायता के लिए नीचे दिए गए विकल्पों पर क्लिक करें:",
        "btns": ["👤 प्रोफाइल", "🔗 इनवाइट लिंक", "💰 वॉलेट", "📚 कोर्स खरीदें", "📞 सहायता", "⚙️ सेटिंग्स"]
    },
    "en": {
        "welcome": "Hello {name}! Welcome to <b>Skillclub</b>. 🙏\n\n🚀 <b>Steps to Start:</b>\n1️⃣ Click '📚 Buy Course'.\n2️⃣ Pay via UPI.\n3️⃣ Send Screenshot here.",
        "lang_select": "🌐 <b>Choose your language / अपनी भाषा चुनें:</b>",
        "lang_updated": "✅ Language updated to <b>English</b>.",
        "profile": "👤 <b>Name:</b> {name}\n🏆 <b>Status:</b> {status}\n💰 <b>Balance:</b> ₹{bal}\n👥 <b>Referrals:</b> {refs}\n📅 <b>Joined:</b> {date}",
        "buy_menu": "🎓 <b>Choose from available courses:</b>",
        "payment_instruction": "🚀 <b>Course:</b> {cname}\n💰 <b>Price:</b> ₹{price}\n\n1. Pay to UPI: <code>{upi}</code>\n2. Send screenshot here.",
        "wallet_msg": "💰 <b>Wallet Balance:</b> ₹{bal}\n📉 Min. Withdrawal: ₹500",
        "invite": "🔥 <b>Your Link:</b>\n{link}",
        "invite_locked": "❌ <b>Link Locked!</b>\nPlease <b>buy at least one course</b> first.",
        "wd_success": "🥳 <b>Payout Successful!</b>",
        "support_msg": "📞 <b>Support Center:</b>\n\nClick the buttons below to contact us:",
        "btns": ["👤 Profile", "🔗 Invite Link", "💰 Wallet", "📚 Buy Course", "📞 Support", "⚙️ Settings"]
    }
}

# --- 3. डेटा मैनेजर ---
def load_json(filename):
    if not os.path.exists(filename):
        if filename == SETTINGS_FILE: default = {"buttons": []}
        elif "log" in filename: default = []
        else: default = {}
        with open(filename, 'w') as f: json.dump(default, f)
        return default
    try:
        with open(filename, 'r') as f: return json.load(f)
    except: return {"buttons": []} if filename == SETTINGS_FILE else {}

def save_json(filename, data):
    with open(filename, 'w') as f: json.dump(data, f, indent=4)

def log_transaction(filename, amount):
    logs = load_json(filename)
    if not isinstance(logs, list): logs = []
    logs.append({"amount": amount, "date": time.strftime("%Y-%m-%d"), "month": time.strftime("%Y-%m")})
    save_json(filename, logs)

# --- 4. एडमिन स्टेट्स ---
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
            f"💰 <b>Today Sell:</b> ₹{t_sell}\n"
            f"📅 <b>Monthly Sell:</b> ₹{m_sell}\n"
            f"📈 <b>Lifetime Sell:</b> ₹{l_sell}\n\n"
            f"💸 <b>Today Payout:</b> ₹{t_wd}\n"
            f"🏧 <b>Lifetime Payout:</b> ₹{l_wd}\n\n"
            f"👥 <b>Total Users:</b> {len(data)}\n"
            f"✅ <b>Paid Users:</b> {sum(1 for u in data.values() if u.get('status') == 'Paid')}")

# --- 5. मेनू और स्टार्ट ---
def get_main_menu(uid, lang):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    b = STRINGS[lang]["btns"]
    markup.add(b[0], b[1]).add(b[2], b[3]).add(b[4], b[5])
    if str(uid) == ADMIN_ID: markup.add("🛠 Admin Panel")
    return markup

@bot.message_handler(commands=['start'])
def start_cmd(message):
    try:
        data, uid = load_json(DB_FILE), str(message.chat.id)
        if uid not in data:
            args = message.text.split()
            ref = args[1] if len(args) > 1 else None
            # NEW: Added 'join_date' and 'purchased' list
            data[uid] = {
                "name": message.from_user.first_name, 
                "balance": 0, "referred_by": ref, 
                "status": "Free", "referrals": 0, 
                "lang": "hi", "purchased": [],
                "join_date": time.strftime("%Y-%m-%d")
            }
            save_json(DB_FILE, data)

        lang = data[uid].get("lang", "hi")
        welcome_text = STRINGS[lang]["welcome"].format(name=data[uid]["name"])
        markup = get_main_menu(uid, lang)
        
        try: bot.send_photo(uid, WELCOME_PHOTO, caption=welcome_text, reply_markup=markup, parse_mode="HTML")
        except: bot.send_message(uid, welcome_text, reply_markup=markup, parse_mode="HTML")
    except Exception as e: print(f"Error: {e}")

# --- 6. हैंडलर्स ---
@bot.callback_query_handler(func=lambda call: True)
def callbacks(call):
    data, courses = load_json(DB_FILE), load_json(COURSE_DB)
    uid, action = str(call.message.chat.id), call.data.split('_')[0]
    
    if action == "setlang":
        new_lang = call.data.split('_')[1]
        data[uid]["lang"] = new_lang
        save_json(DB_FILE, data)
        bot.send_message(uid, STRINGS[new_lang]["lang_updated"], reply_markup=get_main_menu(uid, new_lang), parse_mode="HTML")

    elif action == "buyinfo":
        cid = call.data.split('_')[1]
        if cid in courses:
            data[uid]["pending_buy"] = cid
            save_json(DB_FILE, data)
            lang = data[uid].get("lang", "hi")
            bot.send_message(uid, STRINGS[lang]["payment_instruction"].format(cname=courses[cid]['name'], price=courses[cid]['price'], upi=ADMIN_UPI), parse_mode="HTML")

    elif action == "app":
        t_id, cid = call.data.split('_')[1], "_".join(call.data.split('_')[2:])
        if t_id in data and cid in courses:
            course = courses[cid]
            if cid not in data[t_id].get("purchased", []):
                log_transaction(SALES_FILE, course['price'])
                data[t_id].setdefault("purchased", []).append(cid)
                data[t_id]["status"] = "Paid"
                
                l1 = data[t_id].get("referred_by")
                if l1 and l1 in data:
                    data[l1]["balance"] += course.get("l1", 0)
                    data[l1]["referrals"] = data[l1].get("referrals", 0) + 1
                    l2 = data[l1].get("referred_by")
                    if l2 and l2 in data: data[l2]["balance"] += course.get("l2", 0)
            
            save_json(DB_FILE, data)
            bot.send_message(t_id, "🥳 <b>Approved! Check course menu.</b>", parse_mode="HTML")
            bot.edit_message_caption("✅ APPROVED", ADMIN_ID, call.message.message_id)

    elif action == "wdpay":
        t_id, amt = call.data.split('_')[1], int(call.data.split('_')[2])
        if t_id in data:
            log_transaction(WD_FILE, amt)
            data[t_id]["balance"] -= amt
            save_json(DB_FILE, data)
            bot.send_message(t_id, STRINGS[data[t_id]["lang"]]["wd_success"], parse_mode="HTML")
            bot.edit_message_caption(f"✅ PAID ₹{amt}", ADMIN_ID, call.message.message_id)

    # --- ADMIN SUPPORT SETTINGS CALLBACKS ---
    elif action == "addsupp":
        msg = bot.send_message(uid, "📝 <b>बटन का नाम लिखें:</b>", parse_mode="HTML")
        bot.register_next_step_handler(msg, process_supp_name)
    
    elif action == "delsupp":
        settings = load_json(SETTINGS_FILE)
        m = types.InlineKeyboardMarkup()
        for i, btn in enumerate(settings.get("buttons", [])):
            m.add(types.InlineKeyboardButton(f"🗑️ {btn['name']}", callback_data=f"delconf_{i}"))
        bot.send_message(uid, "🗑️ <b>किसको डिलीट करना है?</b>", reply_markup=m, parse_mode="HTML")

    elif action == "delconf":
        idx = int(call.data.split('_')[1])
        settings = load_json(SETTINGS_FILE)
        if 0 <= idx < len(settings["buttons"]):
            removed = settings["buttons"].pop(idx)
            save_json(SETTINGS_FILE, settings)
            bot.send_message(uid, f"✅ '{removed['name']}' Deleted.", parse_mode="HTML")

# --- Step Handlers for Support Buttons ---
def process_supp_name(message):
    name = message.text
    msg = bot.send_message(ADMIN_ID, f"🔗 <b>'{name}'</b> का लिंक भेजें:", parse_mode="HTML")
    bot.register_next_step_handler(msg, process_supp_link, name)

def process_supp_link(message, name):
    link = message.text
    settings = load_json(SETTINGS_FILE)
    settings.setdefault("buttons", []).append({"name": name, "url": link})
    save_json(SETTINGS_FILE, settings)
    bot.send_message(ADMIN_ID, f"✅ '{name}' Button Added!", parse_mode="HTML")

@bot.message_handler(func=lambda m: True)
def handle_menu(message):
    data, uid = load_json(DB_FILE), str(message.chat.id)
    if uid not in data: return
    text, lang = message.text, data[uid].get("lang", "hi")

    # --- ADMIN PANEL ---
    if text == "🛠 Admin Panel" and uid == ADMIN_ID:
        m = types.ReplyKeyboardMarkup(resize_keyboard=True)
        m.add("📊 Stats", "📢 Broadcast")
        m.add("➕ Add Course", "📞 Support Settings")
        m.add("📥 Export Data", "🔙 Back to Main Menu")
        bot.send_message(uid, "🛠 Admin Panel:", reply_markup=m, parse_mode="HTML")
    
    elif text == "📞 Support Settings" and uid == ADMIN_ID:
        settings = load_json(SETTINGS_FILE)
        btns = settings.get("buttons", [])
        curr = "\n".join([f"• {b['name']}" for b in btns])
        m = types.InlineKeyboardMarkup()
        m.add(types.InlineKeyboardButton("➕ Add Button", callback_data="addsupp"))
        if btns: m.add(types.InlineKeyboardButton("🗑️ Delete Button", callback_data="delsupp"))
        bot.send_message(uid, f"⚙️ <b>Support Buttons:</b>\n{curr if curr else 'None'}", reply_markup=m, parse_mode="HTML")

    # --- USER SUPPORT (MAGIC LINK MERGED) ---
    elif text in ["📞 सहायता", "📞 Support"]:
        p = data[uid]
        sales = len(p.get("purchased", []))
        bal = p.get("balance", 0)
        status = p.get("status", "Free")
        j_date = p.get("join_date", "Old")
        
        # Magic Link Payload
        payload = f"{sales}_{bal}_{status}_{j_date}".replace(" ", "")
        magic_link = f"https://t.me/{SUPPORT_BOT_USERNAME}?start={payload}"

        m = types.InlineKeyboardMarkup()
        # Add Custom Buttons (Instagram/Channel etc)
        settings = load_json(SETTINGS_FILE)
        for b in settings.get("buttons", []):
            m.add(types.InlineKeyboardButton(f"👉 {b['name']}", url=b['url']))
        # Add Live Chat Magic Button
        chat_txt = "💬 Live Chat with Admin" if lang == "en" else "💬 एडमिन से चैट करें"
        m.add(types.InlineKeyboardButton(chat_txt, url=magic_link))
        
        bot.send_message(uid, STRINGS[lang]["support_msg"], reply_markup=m, parse_mode="HTML")

    # --- OTHER BUTTONS (Keeping original logic) ---
    elif text == "📊 Stats" and uid == ADMIN_ID: bot.send_message(uid, get_stats(), parse_mode="HTML")
    
    elif text in ["📚 कोर्स खरीदें", "📚 Buy Course"]:
        courses = load_json(COURSE_DB)
        purchased = data[uid].get("purchased", [])
        m = types.InlineKeyboardMarkup()
        for cid, info in courses.items():
            if cid in purchased: m.add(types.InlineKeyboardButton(f"📥 Download {info['name']}", url=info['link']))
            else: m.add(types.InlineKeyboardButton(f"🛒 {info['name']} - ₹{info['price']}", callback_data=f"buyinfo_{cid}"))
        bot.send_message(uid, STRINGS[lang]["buy_menu"], reply_markup=m, parse_mode="HTML")
    
    elif text in ["👤 प्रोफाइल", "👤 Profile"]:
        p = data[uid]
        bot.send_message(uid, STRINGS[lang]["profile"].format(name=p['name'], status=p['status'], refs=p.get('referrals', 0), bal=p['balance'], date=p.get('join_date', 'Old')), parse_mode="HTML")
    
    elif text in ["💰 वॉलेट", "💰 Wallet"]:
        bal = data[uid].get('balance', 0)
        bot.send_message(uid, STRINGS[lang]["wallet_msg"].format(bal=bal), parse_mode="HTML")

    elif text in ["🔗 इनवाइट लिंक", "🔗 Invite Link"]:
        if not data[uid].get("purchased", []):
            bot.send_message(uid, STRINGS[lang]["invite_locked"], parse_mode="HTML")
        else:
            link = f"https://t.me/{bot.get_me().username}?start={uid}"
            bot.send_message(uid, STRINGS[lang]["invite"].format(link=link), parse_mode="HTML")
    
    elif text == "🔙 Back to Main Menu":
        bot.send_message(uid, "🔙 Main Menu", reply_markup=get_main_menu(uid, lang))

# --- 7. वेब सर्वर ---
@app.route('/')
def home(): return "Skillclub Bot Live"

def run_server():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

if __name__ == "__main__":
    Thread(target=run_server).start()
    bot.remove_webhook()
    time.sleep(1)
    print("🚀 Bot starting...")
    bot.polling(none_stop=True, skip_pending=True)
    
