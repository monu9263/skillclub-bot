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
ADMIN_UPI = "anand1312@fam" # अपनी UPI ID

# --- 2. भाषा और मैसेज (HTML Mode) ---
STRINGS = {
    "hi": {
        "welcome": "नमस्ते {name}! <b>Skillclub</b> में स्वागत है।",
        "profile": "👤 <b>नाम:</b> {name}\n🏆 <b>स्टेटस:</b> {status}\n👥 <b>रेफरल:</b> {refs}",
        "buy_menu": "🎓 <b>हमारे उपलब्ध कोर्सेस चुनें:</b>",
        "no_courses": "❌ अभी कोई कोर्स उपलब्ध नहीं है।",
        "payment_instruction": "🚀 <b>कोर्स:</b> {cname}\n💰 <b>कीमत:</b> ₹{price}\n\n1. UPI: <code>{upi}</code> पर पेमेंट करें।\n2. स्क्रीनशॉट इसी बोट में भेजें।",
        "wallet_msg": "💰 <b>वॉलेट बैलेंस:</b> ₹{bal}\n📉 न्यूनतम विड्रॉल: ₹500",
        "invite": "🔥 <b>आपका इनवाइट लिंक:</b>\n{link}",
        "leaderboard_header": "🏆 <b>Skillclub Top 10 Leaders</b> 🏆\n\n",
        "wd_request_sent": "✅ <b>रिक्वेस्ट भेज दी गई है!</b>\nपेमेंट का इंतज़ार करें।",
        "wd_completed": "🥳 <b>Payout Successful!</b>\nआपका ₹{amt} भेज दिया गया है।",
        "wd_cancelled": "❌ <b>Payout Cancelled!</b>\nआपकी रिक्वेस्ट रिजेक्ट हो गई है।",
        "btns": ["👤 प्रोफाइल", "🔗 इनवाइट लिंक", "💰 वॉलेट", "📚 कोर्स खरीदें", "🏆 लीडरबोर्ड", "⚙️ सेटिंग्स"]
    },
    "en": {
        "welcome": "Hello {name}! Welcome to <b>Skillclub</b>.",
        "profile": "👤 <b>Name:</b> {name}\n🏆 <b>Status:</b> {status}\n👥 <b>Referrals:</b> {refs}",
        "buy_menu": "🎓 <b>Choose from our available courses:</b>",
        "no_courses": "❌ No courses available.",
        "payment_instruction": "🚀 <b>Course:</b> {cname}\n💰 <b>Price:</b> ₹{price}\n\n1. Send payment to UPI: <code>{upi}</code>\n2. Send screenshot here.",
        "wallet_msg": "💰 <b>Wallet Balance:</b> ₹{bal}\n📉 Min. Withdrawal: ₹500",
        "invite": "🔥 <b>Your Invite Link:</b>\n{link}",
        "leaderboard_header": "🏆 <b>Skillclub Top 10 Leaders</b> 🏆\n\n",
        "wd_request_sent": "✅ <b>Request Sent!</b>\nAdmin will verify soon.",
        "wd_completed": "🥳 <b>Payout Successful!</b>\nYour payment of ₹{amt} is done.",
        "wd_cancelled": "❌ <b>Payout Cancelled!</b>\nYour request has been rejected.",
        "btns": ["👤 Profile", "🔗 Invite Link", "💰 Wallet", "📚 Buy Course", "🏆 Leaderboard", "⚙️ Settings"]
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

def load_courses():
    if not os.path.exists(COURSE_DB):
        with open(COURSE_DB, 'w') as f: json.dump({}, f)
        return {}
    try:
        with open(COURSE_DB, 'r') as f: return json.load(f)
    except: return {}

def save_courses(data):
    with open(COURSE_DB, 'w') as f: json.dump(data, f, indent=4)

# --- 4. वेब सर्वर ---
app = Flask('')
@app.route('/')
def home(): return "Skillclub Online!"
def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive():
    t = Thread(target=run)
    t.start()

# --- 5. एडमिन पैनल फंक्शनलिटी (Stats & Search) ---
def get_admin_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("📊 Stats", "👤 Search User")
    markup.add("📢 Broadcast", "➕ Add Course")
    markup.add("🔙 Back to Main Menu")
    return markup

def get_stats(): #
    data = load_data()
    courses = load_courses()
    total_users = len(data)
    total_bal = sum(u.get('balance', 0) for u in data.values())
    paid_users = sum(1 for u in data.values() if "Paid" in u.get('status', ''))
    
    stats_text = (f"📊 <b>Skillclub Real-time Stats</b>\n\n"
                  f"👥 <b>Total Users:</b> {total_users}\n"
                  f"✅ <b>Paid Users:</b> {paid_users}\n"
                  f"💰 <b>Total Wallet Balance:</b> ₹{total_bal}\n"
                  f"📚 <b>Total Courses:</b> {len(courses)}")
    return stats_text

# --- 6. एडमिन कोर्स मैनेजमेंट ---
@bot.message_handler(commands=['addcourse'])
def add_course_start(message):
    if str(message.chat.id) == ADMIN_ID:
        msg = bot.send_message(message.chat.id, "📝 <b>कोर्स का नाम लिखें:</b>", parse_mode="HTML")
        bot.register_next_step_handler(msg, process_course_name)

def process_course_name(message):
    c_name = message.text
    msg = bot.send_message(message.chat.id, f"💰 <b>'{c_name}' की कीमत लिखें:</b>", parse_mode="HTML")
    bot.register_next_step_handler(msg, process_course_price, c_name)

def process_course_price(message, c_name):
    c_price = message.text
    msg = bot.send_message(message.chat.id, "👥 <b>Level 1 कमीशन लिखें:</b>", parse_mode="HTML")
    bot.register_next_step_handler(msg, process_course_l1, c_name, c_price)

def process_course_l1(message, c_name, c_price):
    l1_comm = message.text
    msg = bot.send_message(message.chat.id, "👥 <b>Level 2 कमीशन लिखें:</b>", parse_mode="HTML")
    bot.register_next_step_handler(msg, process_course_l2, c_name, c_price, l1_comm)

def process_course_l2(message, c_name, c_price, l1_comm):
    l2_comm = message.text
    msg = bot.send_message(message.chat.id, "🔗 <b>कोर्स का Drive Link भेजें:</b>", parse_mode="HTML")
    bot.register_next_step_handler(msg, finalize_course, c_name, c_price, l1_comm, l2_comm)

def finalize_course(message, c_name, c_price, l1_comm, l2_comm):
    try:
        courses = load_courses()
        c_id = c_name.lower().replace(" ", "_")
        courses[c_id] = {"name": c_name, "price": int(re.sub(r'\D', '', c_price)), "l1": int(re.sub(r'\D', '', l1_comm)), "l2": int(re.sub(r'\D', '', l2_comm)), "link": message.text}
        save_courses(courses)
        bot.send_message(message.chat.id, f"✅ <b>कोर्स जुड़ गया!</b> ID: <code>{c_id}</code>", parse_mode="HTML")
    except: bot.send_message(message.chat.id, "❌ Error: सिर्फ नंबर का उपयोग करें।")

# --- 7. मुख्य कॉलकैब हैंडलर ---
@bot.callback_query_handler(func=lambda call: True)
def callbacks(call):
    data = load_data()
    courses = load_courses()
    uid = str(call.message.chat.id)
    parts = call.data.split('_', 1)
    action = parts[0]

    if action == "buyinfo":
        cid = parts[1]
        if cid in courses:
            data[uid]["pending_buy"] = cid
            save_data(data)
            bot.send_message(uid, STRINGS[data[uid].get("lang", "hi")]["payment_instruction"].format(cname=courses[cid]['name'], price=courses[cid]['price'], upi=ADMIN_UPI), parse_mode="HTML")

    elif action == "app":
        app_parts = call.data.split('_')
        t_id, cid = app_parts[1], "_".join(app_parts[2:])
        if t_id in data:
            course = courses[cid]
            if "purchased" not in data[t_id]: data[t_id]["purchased"] = []
            if cid not in data[t_id]["purchased"]:
                data[t_id]["purchased"].append(cid)
                data[t_id]["status"] = "Paid"
                # कमीशन लॉजिक
                l1_id = data[t_id].get("referred_by")
                if l1_id and l1_id in data:
                    data[l1_id]["balance"] += course.get("l1", 0)
                    data[l1_id]["referrals"] = data[l1_id].get("referrals", 0) + 1
                    try: bot.send_message(l1_id, f"💰 कमीशन मिला: ₹{course['l1']}", parse_mode="HTML")
                    except: pass
                    l2_id = data[l1_id].get("referred_by")
                    if l2_id and l2_id in data:
                        data[l2_id]["balance"] += course.get("l2", 0)
                        try: bot.send_message(l2_id, f"💸 L2 बोनस मिला: ₹{course['l2']}", parse_mode="HTML")
                        except: pass
            save_data(data)
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("📥 डाउनलोड करें", url=course['link']))
            bot.send_message(t_id, f"🥳 <b>पेमेंट अप्रूव हो गया है!</b>", reply_markup=markup, parse_mode="HTML")
            bot.edit_message_caption(f"✅ APPROVED: {course['name']}", ADMIN_ID, call.message.message_id, parse_mode="HTML")

    elif action == "ask_wd":
        msg = bot.send_message(uid, "📝 <b>अपनी UPI ID भेजें:</b>", parse_mode="HTML")
        bot.register_next_step_handler(msg, process_withdrawal, data[uid]["balance"])

    elif action == "wdpay":
        t_id, amt = call.data.split('_')[1], int(call.data.split('_')[2])
        if t_id in data:
            data[t_id]["balance"] -= amt
            save_data(data)
            bot.send_message(t_id, STRINGS[data[t_id].get("lang", "hi")]["wd_completed"].format(amt=amt), parse_mode="HTML")
            bot.edit_message_caption(f"✅ <b>PAYOUT DONE</b>", ADMIN_ID, call.message.message_id, parse_mode="HTML")

    elif action == "wdrej":
        t_id = call.data.split('_')[1]
        if t_id in data:
            bot.send_message(t_id, STRINGS[data[t_id].get("lang", "hi")]["wd_cancelled"], parse_mode="HTML")
            bot.edit_message_caption(f"❌ <b>PAYOUT CANCELLED</b>", ADMIN_ID, call.message.message_id, parse_mode="HTML")

# --- 8. विड्रॉल, ब्रॉडकास्ट और सर्च लॉजिक ---
def process_withdrawal(message, amt):
    uid, upi_id = str(message.chat.id), message.text
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("✅ Payout Complete", callback_data=f"wdpay_{uid}_{amt}"),
               types.InlineKeyboardButton("❌ Cancel", callback_data=f"wdrej_{uid}"))
    bot.send_message(ADMIN_ID, f"🔔 <b>विड्रॉल रिक्वेस्ट!</b>\nAmt: ₹{amt}\nUPI: <code>{upi_id}</code>", reply_markup=markup, parse_mode="HTML")
    bot.send_message(uid, STRINGS["hi"]["wd_request_sent"], parse_mode="HTML")

@bot.message_handler(commands=['broadcast'])
def start_broadcast(message):
    if str(message.chat.id) == ADMIN_ID:
        msg = bot.send_message(ADMIN_ID, "📢 संदेश भेजें (टेक्स्ट या फोटो):", parse_mode="HTML")
        bot.register_next_step_handler(msg, send_broadcast)

def send_broadcast(message):
    data = load_data()
    count = 0
    for uid in data.keys():
        try:
            if message.content_type == 'text':
                bot.send_message(uid, f"📢 <b>ANNOUNCEMENT:</b>\n\n{message.text}", parse_mode="HTML")
            elif message.content_type == 'photo':
                bot.send_photo(uid, message.photo[-1].file_id, caption=f"📢 <b>ANNOUNCEMENT:</b>\n\n{message.caption if message.caption else ''}", parse_mode="HTML")
            count += 1
        except: continue
    bot.send_message(ADMIN_ID, f"✅ {count} यूजर्स को भेज दिया गया।")

def process_user_search(message): #
    data = load_data()
    search_id = message.text.strip()
    if search_id in data:
        u = data[search_id]
        purchased = ", ".join(u.get('purchased', [])) if u.get('purchased') else "None"
        info = (f"👤 <b>User Info:</b> {u['name']}\n"
                f"🆔 <b>ID:</b> <code>{search_id}</code>\n"
                f"💰 <b>Balance:</b> ₹{u['balance']}\n"
                f"👥 <b>Referrals:</b> {u.get('referrals', 0)}\n"
                f"🏆 <b>Status:</b> {u['status']}\n"
                f"📚 <b>Courses:</b> {purchased}")
        bot.send_message(ADMIN_ID, info, parse_mode="HTML")
    else:
        bot.send_message(ADMIN_ID, "❌ यूजर नहीं मिला।")

# --- 9. मेनू और फोटो हैंडलर ---
@bot.message_handler(func=lambda m: True)
def handle_menu(message):
    data = load_data()
    uid = str(message.chat.id)
    if uid not in data: return
    lang = data[uid].get("lang", "hi")
    text = message.text

    # --- Admin Panel Logic ---
    if text == "🛠 Admin Panel" and uid == ADMIN_ID:
        bot.send_message(uid, "🛠 <b>Welcome to Admin Control:</b>", reply_markup=get_admin_menu(), parse_mode="HTML")

    elif text == "📊 Stats" and uid == ADMIN_ID:
        bot.send_message(uid, get_stats(), parse_mode="HTML")

    elif text == "👤 Search User" and uid == ADMIN_ID:
        msg = bot.send_message(uid, "🔍 <b>यूजर की Telegram ID भेजें:</b>", parse_mode="HTML")
        bot.register_next_step_handler(msg, process_user_search)

    elif text == "📢 Broadcast" and uid == ADMIN_ID:
        start_broadcast(message)

    elif text == "➕ Add Course" and uid == ADMIN_ID:
        add_course_start(message)

    elif text == "🔙 Back to Main Menu":
        bot.send_message(uid, "🔙 मुख्य मेनू पर वापस।", reply_markup=get_main_menu(uid, lang), parse_mode="HTML")

    # --- User Menu Logic ---
    elif text in ["📚 कोर्स खरीदें", "📚 Buy Course"]:
        courses = load_courses()
        purchased_list = data[uid].get("purchased", [])
        markup = types.InlineKeyboardMarkup()
        for cid, info in courses.items():
            if cid in purchased_list: markup.add(types.InlineKeyboardButton(f"📥 Download {info['name']}", url=info['link']))
            else: markup.add(types.InlineKeyboardButton(f"🛒 {info['name']} - ₹{info['price']}", callback_data=f"buyinfo_{cid}"))
        bot.send_message(uid, STRINGS[lang]["buy_menu"], reply_markup=markup, parse_mode="HTML")

    elif text in ["🏆 लीडरबोर्ड", "🏆 Leaderboard"]:
        sorted_users = sorted(data.items(), key=lambda x: x[1].get('referrals', 0), reverse=True)
        leader_text = STRINGS[lang]["leaderboard_header"]
        for i, (u_id, u_data) in enumerate(sorted_users[:10], 1):
            leader_text += f"{i}. {u_data.get('name', 'User')} — {u_data.get('referrals', 0)} रेफरल्स\n"
        bot.send_message(uid, leader_text, parse_mode="HTML")

    elif text in ["💰 वॉलेट", "💰 Wallet"]:
        bal = data[uid].get('balance', 0)
        markup = types.InlineKeyboardMarkup()
        if bal >= 500: markup.add(types.InlineKeyboardButton("💸 Withdraw Money", callback_data=f"ask_wd_{uid}"))
        bot.send_message(uid, STRINGS[lang]["wallet_msg"].format(bal=bal), reply_markup=markup, parse_mode="HTML")

    elif text in ["👤 प्रोफाइल", "👤 Profile"]:
        bot.send_message(uid, STRINGS[lang]["profile"].format(name=data[uid]['name'], status=data[uid]['status'], refs=data[uid].get('referrals', 0)), parse_mode="HTML")

    elif text in ["🔗 इनवाइट लिंक", "🔗 Invite Link"]:
        link = f"https://t.me/{bot.get_me().username}?start={uid}"
        bot.send_message(uid, STRINGS[lang]["invite"].format(link=link), parse_mode="HTML")

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    uid, data = str(message.chat.id), load_data()
    pending_cid = data[uid].get("pending_buy")
    if pending_cid:
        courses = load_courses()
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("✅ Approve", callback_data=f"app_{uid}_{pending_cid}"),
                   types.InlineKeyboardButton("❌ Reject", callback_data=f"rej_{uid}"))
        bot.send_photo(ADMIN_ID, message.photo[-1].file_id, caption=f"📩 <b>नया पेमेंट!</b>\nID: <code>{uid}</code>\nकोर्स: {courses[pending_cid]['name']}", reply_markup=markup, parse_mode="HTML")
        bot.send_message(uid, "✅ स्क्रीनशॉट मिल गया! अप्रूवल का इंतज़ार करें।")

@bot.message_handler(commands=['start'])
def start(message):
    data = load_data()
    uid = str(message.chat.id)
    if uid not in data:
        args = message.text.split()
        ref_id = args[1] if len(args) > 1 else None
        data[uid] = {"name": message.from_user.first_name, "balance": 0, "referred_by": ref_id, "status": "Free", "referrals": 0, "lang": "hi", "purchased": []}
        save_data(data)
    lang = data[uid].get("lang", "hi")
    bot.send_message(uid, STRINGS[lang]["welcome"].format(name=message.from_user.first_name), reply_markup=get_main_menu(uid, lang), parse_mode="HTML")

def get_main_menu(uid, lang):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    b = STRINGS[lang]["btns"]
    markup.add(b[0], b[1])
    markup.add(b[2], b[3])
    markup.add(b[4], b[5])
    if str(uid) == ADMIN_ID: markup.add("🛠 Admin Panel")
    return markup

if __name__ == "__main__":
    keep_alive()
    bot.polling(none_stop=True)
        
