import telebot
from telebot import types
import json
import os
import re
from flask import Flask
from threading import Thread
import time

# --- 1. कॉन्फ़िगरेशन (CONFIGURATION) ---
API_TOKEN = os.getenv('API_TOKEN')
ADMIN_ID = os.getenv('ADMIN_ID')

# बोट स्टार्ट करने से पहले चेक करें
if not API_TOKEN or not ADMIN_ID:
    print("❌ ERROR: API_TOKEN या ADMIN_ID सेट नहीं है!")

bot = telebot.TeleBot(API_TOKEN)

# डेटा फाइल्स
DB_FILE = 'users.json'
COURSE_DB = 'courses.json'
SALES_FILE = 'sales_log.json'
WD_FILE = 'withdrawals_log.json'

# सेटिंग्स
ADMIN_UPI = "anand1312@fam" 
WELCOME_PHOTO = "https://files.catbox.moe/0v601y.png" 

# --- 2. भाषा और मैसेज (STRINGS) ---
STRINGS = {
    "hi": {
        "welcome": (
            "नमस्ते {name}! <b>Skillclub</b> में आपका स्वागत है। 🙏\n\n"
            "🚀 <b>शुरू करने के लिए स्टेप्स:</b>\n"
            "1️⃣ <b>कोर्स चुनें:</b> नीचे '📚 कोर्स खरीदें' बटन दबाएं।\n"
            "2️⃣ <b>पेमेंट करें:</b> बोट द्वारा दी गई UPI ID पर।\n"
            "3️⃣ <b>स्क्रीनशॉट भेजें:</b> पेमेंट का स्क्रीनशॉट यहाँ भेजें।\n"
            "4️⃣ <b>लिंक लें:</b> '🔗 इनवाइट लिंक' से अपना लिंक बनाएं।\n\n"
            "🔥 <b>Daily Earn:</b> लिंक रेफर करें और रोज़ कमाएं! 💰"
        ),
        "lang_select": "🌐 <b>अपनी भाषा चुनें / Choose your language:</b>",
        "lang_updated": "✅ भाषा <b>Hindi</b> में बदल दी गई है।",
        "profile": "👤 <b>नाम:</b> {name}\n🏆 <b>स्टेटस:</b> {status}\n👥 <b>रेफरल:</b> {refs}",
        "buy_menu": "🎓 <b>हमारे उपलब्ध कोर्सेस चुनें:</b>",
        "payment_instruction": "🚀 <b>कोर्स:</b> {cname}\n💰 <b>कीमत:</b> ₹{price}\n\n1. UPI: <code>{upi}</code> पर पेमेंट करें।\n2. स्क्रीनशॉट इसी बोट में भेजें।",
        "wallet_msg": "💰 <b>वॉलेट बैलेंस:</b> ₹{bal}\n📉 न्यूनतम विड्रॉल: ₹500",
        "invite": "🔥 <b>आपका लिंक:</b>\n{link}\n\nइसे प्रमोट करें और डेली अर्न करें!",
        "invite_locked": "❌ <b>लिंक लॉक है! (Link Locked)</b>\n\nइनवाइट लिंक जनरेट करने के लिए आपको पहले <b>कम से कम एक कोर्स खरीदना होगा</b>।\n\nकृपया '📚 कोर्स खरीदें' पर क्लिक करें।",
        "leaderboard_header": "🏆 <b>Skillclub Top 10 Leaders</b> 🏆\n\n",
        "wd_success": "🥳 <b>Payout Successful!</b>",
        "btns": ["👤 प्रोफाइल", "🔗 इनवाइट लिंक", "💰 वॉलेट", "📚 कोर्स खरीदें", "🏆 लीडरबोर्ड", "⚙️ सेटिंग्स"]
    },
    "en": {
        "welcome": (
            "Hello {name}! Welcome to <b>Skillclub</b>. 🙏\n\n"
            "🚀 <b>Steps to Start:</b>\n"
            "1️⃣ <b>Select Course:</b> Click '📚 Buy Course'.\n"
            "2️⃣ <b>Pay:</b> Send money to the provided UPI.\n"
            "3️⃣ <b>Screenshot:</b> Send your payment screenshot here.\n"
            "4️⃣ <b>Get Link:</b> Generate via '🔗 Invite Link'.\n\n"
            "🔥 <b>Daily Earn:</b> Refer link & earn daily! 💰"
        ),
        "lang_select": "🌐 <b>Choose your language / अपनी भाषा चुनें:</b>",
        "lang_updated": "✅ Language updated to <b>English</b>.",
        "profile": "👤 <b>Name:</b> {name}\n🏆 <b>Status:</b> {status}\n👥 <b>Referrals:</b> {refs}",
        "buy_menu": "🎓 <b>Choose from available courses:</b>",
        "payment_instruction": "🚀 <b>Course:</b> {cname}\n💰 <b>Price:</b> ₹{price}\n\n1. Pay to UPI: <code>{upi}</code>\n2. Send screenshot here.",
        "wallet_msg": "💰 <b>Wallet Balance:</b> ₹{bal}\n📉 Min. Withdrawal: ₹500",
        "invite": "🔥 <b>Your Link:</b>\n{link}\n\nPromote and earn daily!",
        "invite_locked": "❌ <b>Link Locked!</b>\n\nYou need to <b>buy at least one course</b> to generate your invite link.\n\nPlease click on '📚 Buy Course' first.",
        "leaderboard_header": "🏆 <b>Skillclub Top 10 Leaders</b> 🏆\n\n",
        "wd_success": "🥳 <b>Payout Successful!</b>",
        "btns": ["👤 Profile", "🔗 Invite Link", "💰 Wallet", "📚 Buy Course", "🏆 Leaderboard", "⚙️ Settings"]
    }
}

# --- 3. डेटा मैनेजर (DATA MANAGER) ---
def load_json(filename):
    if not os.path.exists(filename):
        default = [] if "log" in filename else {}
        with open(filename, 'w') as f: json.dump(default, f)
        return default
    try:
        with open(filename, 'r') as f: return json.load(f)
    except:
        return [] if "log" in filename else {}

def save_json(filename, data):
    with open(filename, 'w') as f: json.dump(data, f, indent=4)

def log_transaction(filename, amount):
    logs = load_json(filename)
    if not isinstance(logs, list): logs = []
    logs.append({
        "amount": amount,
        "date": time.strftime("%Y-%m-%d"),
        "month": time.strftime("%Y-%m")
    })
    save_json(filename, logs)

# --- 4. एडमिन स्टेट्स (ADMIN STATS) ---
def get_stats():
    data = load_json(DB_FILE)
    sales = load_json(SALES_FILE)
    withdrawals = load_json(WD_FILE)
    today, month = time.strftime("%Y-%m-%d"), time.strftime("%Y-%m")
    
    t_sell, m_sell, l_sell = 0, 0, 0
    for s in (sales if isinstance(sales, list) else []):
        amt = s.get('amount', 0)
        l_sell += amt
        if s.get('date') == today: t_sell += amt
        if s.get('month') == month: m_sell += amt
        
    t_wd, l_wd = 0, 0
    for w in (withdrawals if isinstance(withdrawals, list) else []):
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

# --- 5. मुख्य मेनू (MAIN MENU) ---
def get_main_menu(uid, lang):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    b = STRINGS[lang]["btns"]
    markup.add(b[0], b[1]).add(b[2], b[3]).add(b[4], b[5])
    if str(uid) == ADMIN_ID: markup.add("🛠 Admin Panel")
    return markup

# --- 6. स्टार्ट कमांड (ROBUST START COMMAND) ---
@bot.message_handler(commands=['start'])
def start_cmd(message):
    try:
        data, uid = load_json(DB_FILE), str(message.chat.id)
        
        if uid not in data:
            args = message.text.split()
            ref = args[1] if len(args) > 1 else None
            data[uid] = {
                "name": message.from_user.first_name, 
                "balance": 0, 
                "referred_by": ref, 
                "status": "Free", 
                "referrals": 0, 
                "lang": "hi", 
                "purchased": []
            }
            save_json(DB_FILE, data)
            print(f"✅ New User: {uid}")

        lang = data[uid].get("lang", "hi")
        welcome_text = STRINGS[lang]["welcome"].format(name=data[uid]["name"])
        markup = get_main_menu(uid, lang)
        
        try:
            bot.send_photo(uid, WELCOME_PHOTO, caption=welcome_text, reply_markup=markup, parse_mode="HTML")
        except Exception as e:
            print(f"⚠️ Photo Error for {uid}: {e}")
            bot.send_message(uid, welcome_text, reply_markup=markup, parse_mode="HTML")
            
    except Exception as e:
        print(f"❌ Critical Error in Start: {e}")

# --- 7. अन्य हैंडलर्स (HANDLERS) ---
@bot.callback_query_handler(func=lambda call: True)
def callbacks(call):
    data, courses = load_json(DB_FILE), load_json(COURSE_DB)
    uid, action = str(call.message.chat.id), call.data.split('_', 1)[0]
    
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
            bot.send_message(uid, STRINGS[data[uid].get("lang", "hi")]["payment_instruction"].format(cname=courses[cid]['name'], price=courses[cid]['price'], upi=ADMIN_UPI), parse_mode="HTML")

    elif action == "app":
        t_id, cid = call.data.split('_')[1], "_".join(call.data.split('_')[2:])
        if t_id in data and cid in courses:
            course = courses[cid]
            if cid not in data[t_id].get("purchased", []):
                log_transaction(SALES_FILE, course['price'])
                data[t_id].setdefault("purchased", []).append(cid)
                data[t_id]["status"] = "Paid"
                
                # कमीशन (L1 & L2)
                l1 = data[t_id].get("referred_by")
                if l1 and l1 in data:
                    data[l1]["balance"] += course.get("l1", 0)
                    data[l1]["referrals"] = data[l1].get("referrals", 0) + 1
                    try: bot.send_message(l1, f"💰 Commission: ₹{course['l1']}", parse_mode="HTML")
                    except: pass
                    
                    l2 = data[l1].get("referred_by")
                    if l2 and l2 in data: 
                        data[l2]["balance"] += course.get("l2", 0)
                        try: bot.send_message(l2, f"💸 L2 Bonus: ₹{course['l2']}", parse_mode="HTML")
                        except: pass
            
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
            
    elif action == "ask_wd":
        msg = bot.send_message(uid, "📝 <b>Send UPI ID:</b>", parse_mode="HTML")
        bot.register_next_step_handler(msg, process_withdrawal, data[uid]["balance"])

def process_withdrawal(message, amt):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("✅ Pay", callback_data=f"wdpay_{message.chat.id}_{amt}"),
               types.InlineKeyboardButton("❌ Reject", callback_data=f"wdrej_{message.chat.id}"))
    bot.send_message(ADMIN_ID, f"🔔 <b>WD Request: ₹{amt}</b>\nUPI: <code>{message.text}</code>", reply_markup=markup, parse_mode="HTML")
    bot.send_message(message.chat.id, "✅ Request Sent!")

def process_user_search(message):
    data = load_json(DB_FILE)
    sid = message.text.strip()
    if sid in data:
        u = data[sid]
        bot.send_message(ADMIN_ID, f"👤 {u['name']}\nID: <code>{sid}</code>\nBal: ₹{u['balance']}\nRefs: {u.get('referrals', 0)}\nStatus: {u['status']}", parse_mode="HTML")
    else: bot.send_message(ADMIN_ID, "❌ Not Found")

@bot.message_handler(commands=['addcourse'])
def add_course_start(message):
    if str(message.chat.id) == ADMIN_ID:
        msg = bot.send_message(ADMIN_ID, "📝 Course Name:")
        bot.register_next_step_handler(msg, lambda m: bot.register_next_step_handler(bot.send_message(ADMIN_ID, f"💰 {m.text} Price:"), process_course_price, m.text))

def process_course_price(message, name):
    msg = bot.send_message(ADMIN_ID, "👥 L1 Commission:")
    bot.register_next_step_handler(msg, process_course_comm, name, message.text)

def process_course_comm(message, name, price):
    l1 = message.text
    msg = bot.send_message(ADMIN_ID, "👥 L2 Commission:")
    bot.register_next_step_handler(msg, process_course_l2, name, price, l1)

def process_course_l2(message, name, price, l1):
    msg = bot.send_message(ADMIN_ID, "🔗 Drive Link:")
    bot.register_next_step_handler(msg, finalize_course, name, price, l1, message.text)

def finalize_course(message, name, price, l1, l2):
    courses = load_json(COURSE_DB)
    cid = name.lower().replace(" ", "_")
    courses[cid] = {"name": name, "price": int(re.sub(r'\D', '', price)), "l1": int(re.sub(r'\D', '', l1)), "l2": int(re.sub(r'\D', '', l2)), "link": message.text}
    save_json(COURSE_DB, courses)
    bot.send_message(ADMIN_ID, f"✅ Course Added!\nID: {cid}")

@bot.message_handler(commands=['broadcast'])
def start_broadcast(message):
    if str(message.chat.id) == ADMIN_ID:
        msg = bot.send_message(ADMIN_ID, "📢 Send Message/Photo:", parse_mode="HTML")
        bot.register_next_step_handler(msg, send_broadcast)

def send_broadcast(message):
    data = load_json(DB_FILE)
    count = 0
    for uid in data.keys():
        try:
            if message.content_type == 'text': bot.send_message(uid, f"📢 <b>Announcement:</b>\n\n{message.text}", parse_mode="HTML")
            elif message.content_type == 'photo': bot.send_photo(uid, message.photo[-1].file_id, caption=f"📢 {message.caption if message.caption else ''}", parse_mode="HTML")
            count += 1
        except: continue
    bot.send_message(ADMIN_ID, f"✅ Sent to {count} users.")

# --- 8. मेनू हैंडलर (MENU HANDLER WITH LOCK LOGIC) ---
@bot.message_handler(func=lambda m: True)
def handle_menu(message):
    data, uid = load_json(DB_FILE), str(message.chat.id)
    if uid not in data: return
    text, lang = message.text, data[uid].get("lang", "hi")

    if text == "🛠 Admin Panel" and uid == ADMIN_ID:
        m = types.ReplyKeyboardMarkup(resize_keyboard=True)
        m.add("📊 Stats", "📢 Broadcast").add("📥 Export Data", "➕ Add Course").add("👤 Search User", "🔙 Back to Main Menu")
        bot.send_message(uid, "🛠 Admin Panel:", reply_markup=m, parse_mode="HTML")
    
    elif text == "📊 Stats" and uid == ADMIN_ID: bot.send_message(uid, get_stats(), parse_mode="HTML")
    elif text == "➕ Add Course" and uid == ADMIN_ID: add_course_start(message)
    elif text == "👤 Search User" and uid == ADMIN_ID: 
        msg = bot.send_message(uid, "🔍 User ID:")
        bot.register_next_step_handler(msg, process_user_search)
    elif text == "📥 Export Data" and uid == ADMIN_ID:
        if os.path.exists(DB_FILE): bot.send_document(uid, open(DB_FILE, 'rb'))
        if os.path.exists(SALES_FILE): bot.send_document(uid, open(SALES_FILE, 'rb'))
    
    elif text == "⚙️ सेटिंग्स" or text == "⚙️ Settings":
        m = types.InlineKeyboardMarkup()
        m.add(types.InlineKeyboardButton("🇮🇳 Hindi", callback_data="setlang_hi"), types.InlineKeyboardButton("🇺🇸 English", callback_data="setlang_en"))
        bot.send_message(uid, STRINGS[lang]["lang_select"], reply_markup=m, parse_mode="HTML")
    
    elif text in ["🏆 लीडरबोर्ड", "🏆 Leaderboard"]:
        u_list = sorted(data.items(), key=lambda x: x[1].get('referrals', 0), reverse=True)[:10]
        res = STRINGS[lang]["leaderboard_header"]
        for i, (k, v) in enumerate(u_list, 1): res += f"{i}. {v['name']} - {v.get('referrals', 0)} Refs\n"
        bot.send_message(uid, res, parse_mode="HTML")
    
    elif text in ["📚 कोर्स खरीदें", "📚 Buy Course"]:
        courses = load_json(COURSE_DB)
        purchased = data[uid].get("purchased", [])
        markup = types.InlineKeyboardMarkup()
        for cid, info in courses.items():
            if cid in purchased: markup.add(types.InlineKeyboardButton(f"📥 Download {info['name']}", url=info['link']))
            else: markup.add(types.InlineKeyboardButton(f"🛒 {info['name']} - ₹{info['price']}", callback_data=f"buyinfo_{cid}"))
        bot.send_message(uid, STRINGS[lang]["buy_menu"], reply_markup=markup, parse_mode="HTML")
    
    elif text in ["💰 वॉलेट", "💰 Wallet"]:
        bal = data[uid].get('balance', 0)
        markup = types.InlineKeyboardMarkup()
        if bal >= 500: markup.add(types.InlineKeyboardButton("💸 Withdraw Money", callback_data="ask_wd"))
        bot.send_message(uid, STRINGS[lang]["wallet_msg"].format(bal=bal), reply_markup=markup, parse_mode="HTML")
    
    elif text in ["👤 प्रोफाइल", "👤 Profile"]:
        bot.send_message(uid, STRINGS[lang]["profile"].format(name=data[uid]['name'], status=data[uid]['status'], refs=data[uid].get('referrals', 0)), parse_mode="HTML")
    
    # --- INVITE LINK LOGIC (LOCKED) ---
    elif text in ["🔗 इनवाइट लिंक", "🔗 Invite Link"]:
        # चेक करें कि क्या यूजर ने कोर्स खरीदा है
        purchased_list = data[uid].get("purchased", [])
        
        if not purchased_list:
            # अगर कोर्स नहीं खरीदा
            bot.send_message(uid, STRINGS[lang]["invite_locked"], parse_mode="HTML")
        else:
            # अगर कोर्स खरीदा है
            link = f"https://t.me/{bot.get_me().username}?start={uid}"
            bot.send_message(uid, STRINGS[lang]["invite"].format(link=link), parse_mode="HTML")
    
    elif text == "🔙 Back to Main Menu":
        bot.send_message(uid, "🔙 Main Menu", reply_markup=get_main_menu(uid, lang))

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    uid, data = str(message.chat.id), load_json(DB_FILE)
    pending_cid = data[uid].get("pending_buy")
    if pending_cid:
        courses = load_json(COURSE_DB)
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("✅ Approve", callback_data=f"app_{uid}_{pending_cid}"),
                   types.InlineKeyboardButton("❌ Reject", callback_data=f"rej_{uid}"))
        bot.send_photo(ADMIN_ID, message.photo[-1].file_id, caption=f"📩 <b>New Payment!</b>\nID: <code>{uid}</code>\nCourse: {courses[pending_cid]['name']}", reply_markup=markup, parse_mode="HTML")
        bot.send_message(uid, "✅ Screenshot received! Please wait for approval.")

# --- 9. वेब सर्वर (RENDER SERVER CONFIG) ---
app = Flask('')
@app.route('/')
def home(): return "Skillclub Bot Running"

def run_server():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

if __name__ == "__main__":
    Thread(target=run_server).start()
    
    print("🚀 Bot starting...")
    bot.remove_webhook()
    time.sleep(1)
    
    while True:
        try:
            bot.polling(none_stop=True, skip_pending=True, timeout=60)
        except Exception as e:
            print(f"⚠️ Polling Error: {e}")
            time.sleep(5)
    
