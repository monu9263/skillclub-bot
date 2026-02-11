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
ADMIN_UPI = "anand1312@fam" # अपनी UPI ID यहाँ बदलें

# आपका डिज़ाइन किया हुआ पोस्टर
WELCOME_PHOTO = "https://files.catbox.moe/0v601y.png" 

# --- 2. भाषा और मैसेज (Bilingual & Instructions Added) ---
STRINGS = {
    "hi": {
        "welcome": (
            "नमस्ते {name}! <b>Skillclub</b> में आपका स्वागत है। 🙏\n\n"
            "🚀 <b>शुरू करने के लिए इन स्टेप्स को फॉलो करें:</b>\n\n"
            "1️⃣ <b>कोर्स चुनें:</b> नीचे दिए गए '📚 कोर्स खरीदें' बटन पर क्लिक करें।\n"
            "2️⃣ <b>पेमेंट करें:</b> बोट द्वारा दी गई UPI ID पर पेमेंट करें।\n"
            "3️⃣ <b>स्क्रीनशॉट भेजें:</b> Send your payment screenshot in bot here.\n"
            "4️⃣ <b>इनवाइट लिंक:</b> '🔗 इनवाइट लिंक' बटन दबाकर अपना लिंक जनरेट करें।\n\n"
            "🔥 <b>जरूरी सूचना:</b> आप इस लिंक को रेफर करके <b>डेली अर्न (Daily Earn)</b> कर सकते हो! हर सेल पर आपको कमीशन मिलेगा। 💰"
        ),
        "lang_select": "🌐 <b>अपनी भाषा चुनें / Choose your language:</b>",
        "lang_updated": "✅ आपकी भाषा <b>Hindi</b> में बदल दी गई है।",
        "profile": "👤 <b>नाम:</b> {name}\n🏆 <b>स्टेटस:</b> {status}\n👥 <b>रेफरल:</b> {refs}",
        "buy_menu": "🎓 <b>हमारे उपलब्ध कोर्सेस चुनें:</b>",
        "no_courses": "❌ अभी कोई कोर्स उपलब्ध नहीं है।",
        "payment_instruction": "🚀 <b>कोर्स:</b> {cname}\n💰 <b>कीमत:</b> ₹{price}\n\n1. UPI: <code>{upi}</code> पर पेमेंट करें।\n2. स्क्रीनशॉट इसी बोट में भेजें।",
        "wallet_msg": "💰 <b>वॉलेट बैलेंस:</b> ₹{bal}\n📉 न्यूनतम विड्रॉल: ₹500",
        "invite": "🔥 <b>आपका लिंक:</b>\n{link}\n\nइसे प्रमोट करें और डेली अर्न करें!",
        "leaderboard_header": "🏆 <b>Skillclub Top 10 Leaders</b> 🏆\n\n",
        "wd_request_sent": "✅ <b>रिक्वेस्ट भेज दी गई है!</b>\nएडमिन वेरिफिकेशन का इंतज़ार करें।",
        "wd_completed": "🥳 <b>Payout Successful!</b>\nआपका ₹{amt} भेज दिया गया है।",
        "wd_cancelled": "❌ <b>Payout Cancelled!</b>\nआपकी रिक्वेस्ट रिजेक्ट हो गई है।",
        "btns": ["👤 प्रोफाइल", "🔗 इनवाइट लिंक", "💰 वॉलेट", "📚 कोर्स खरीदें", "🏆 लीडरबोर्ड", "⚙️ सेटिंग्स"]
    },
    "en": {
        "welcome": (
            "Hello {name}! Welcome to <b>Skillclub</b>. 🙏\n\n"
            "🚀 <b>Follow these steps to get started:</b>\n\n"
            "1️⃣ <b>Select Course:</b> Click on '📚 Buy Course' below.\n"
            "2️⃣ <b>Make Payment:</b> Pay the amount to the UPI ID provided.\n"
            "3️⃣ <b>Send Screenshot:</b> Send your payment screenshot in bot here.\n"
            "4️⃣ <b>Invite Link:</b> Generate your link via '🔗 Invite Link'.\n\n"
            "🔥 <b>Earning Tip:</b> You can <b>earn daily</b> by referring this link to your friends! Get commissions on every sale. 💰"
        ),
        "lang_select": "🌐 <b>Choose your language / अपनी भाषा चुनें:</b>",
        "lang_updated": "✅ Your language has been updated to <b>English</b>.",
        "profile": "👤 <b>Name:</b> {name}\n🏆 <b>Status:</b> {status}\n👥 <b>Referrals:</b> {refs}",
        "buy_menu": "🎓 <b>Choose from our available courses:</b>",
        "no_courses": "❌ No courses available currently.",
        "payment_instruction": "🚀 <b>Course:</b> {cname}\n💰 <b>Price:</b> ₹{price}\n\n1. UPI: <code>{upi}</code>\n2. Send screenshot here.",
        "wallet_msg": "💰 <b>Wallet Balance:</b> ₹{bal}\n📉 Min. Withdrawal: ₹500",
        "invite": "🔥 <b>Your Link:</b>\n{link}\n\nPromote and earn daily!",
        "leaderboard_header": "🏆 <b>Skillclub Top 10 Leaders</b> 🏆\n\n",
        "wd_request_sent": "✅ <b>Request Sent!</b>\nAdmin will verify and pay soon.",
        "wd_completed": "🥳 <b>Payout Successful!</b>\nYour payment of ₹{amt} is done.",
        "wd_cancelled": "❌ <b>Payout Cancelled!</b>\nYour request has been rejected.",
        "btns": ["👤 Profile", "🔗 Invite Link", "💰 Wallet", "📚 Buy Course", "🏆 Leaderboard", "⚙️ Settings"]
    }
}

# --- 3. डेटा मैनेजर ---
def load_data():
    if not os.path.exists(DB_FILE): return {}
    try:
        with open(DB_FILE, 'r') as f: return json.load(f)
    except: return {}

def save_data(data):
    with open(DB_FILE, 'w') as f: json.dump(data, f, indent=4)

def load_courses():
    if not os.path.exists(COURSE_DB): return {}
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

# --- 5. एडमिन पैनल लॉजिक ---
def get_admin_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("📊 Stats", "👤 Search User")
    markup.add("📢 Broadcast", "📥 Export Data")
    markup.add("➕ Add Course", "🔙 Back to Main Menu")
    return markup

def get_stats(): #
    data = load_data()
    courses = load_courses()
    total_users = len(data)
    total_bal = sum(u.get('balance', 0) for u in data.values())
    paid_users = sum(1 for u in data.values() if "Paid" in u.get('status', ''))
    return (f"📊 <b>Stats:</b>\nUsers: {total_users}\nPaid: {paid_users}\nWallet: ₹{total_bal}\nCourses: {len(courses)}")

# --- 6. मुख्य कॉलकैब हैंडलर (Bilingual & Multi-word ID Fix) ---
@bot.callback_query_handler(func=lambda call: True)
def callbacks(call):
    data = load_data()
    courses = load_courses()
    uid = str(call.message.chat.id)
    if uid not in data: return
    parts = call.data.split('_', 1)
    action = parts[0]

    if action == "setlang": # भाषा अपडेट लॉजिक
        new_lang = parts[1]
        data[uid]["lang"] = new_lang
        save_data(data)
        bot.answer_callback_query(call.id, "Updated!")
        bot.send_message(uid, STRINGS[new_lang]["lang_updated"], reply_markup=get_main_menu(uid, new_lang), parse_mode="HTML")

    elif action == "buyinfo":
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
            if cid not in data[t_id].get("purchased", []):
                data[t_id].setdefault("purchased", []).append(cid)
                data[t_id]["status"] = "Paid"
                l1 = data[t_id].get("referred_by")
                if l1 and l1 in data:
                    data[l1]["balance"] += course.get("l1", 0)
                    data[l1]["referrals"] = data[l1].get("referrals", 0) + 1
                    try: bot.send_message(l1, f"💰 Commission: ₹{course['l1']}", parse_mode="HTML")
                    except: pass
                    l2 = data[l1].get("referred_by")
                    if l2 and l2 in data: data[l2]["balance"] += course.get("l2", 0)
            save_data(data)
            bot.send_message(t_id, "🥳 <b>Approved! Check 'Buy Course' for link.</b>", parse_mode="HTML")
            bot.edit_message_caption(f"✅ APPROVED", ADMIN_ID, call.message.message_id)

    elif action == "ask_wd":
        msg = bot.send_message(uid, "📝 <b>Send UPI ID:</b>", parse_mode="HTML")
        bot.register_next_step_handler(msg, process_withdrawal, data[uid]["balance"])

    elif action == "wdpay":
        t_id, amt = call.data.split('_')[1], int(call.data.split('_')[2])
        data[t_id]["balance"] -= amt
        save_data(data)
        bot.send_message(t_id, STRINGS[data[t_id]["lang"]]["wd_completed"].format(amt=amt), parse_mode="HTML")
        bot.edit_message_caption(f"✅ PAID ₹{amt}", ADMIN_ID, call.message.message_id)

# --- 7. एडमिन फंक्शन्स ---
def process_user_search(message):
    data = load_data()
    uid = message.text.strip()
    if uid in data:
        u = data[uid]
        info = (f"👤 {u['name']}\nID: <code>{uid}</code>\nBal: ₹{u['balance']}\nRefs: {u.get('referrals', 0)}\nStatus: {u['status']}")
        bot.send_message(ADMIN_ID, info, parse_mode="HTML")
    else: bot.send_message(ADMIN_ID, "❌ User not found.")

def handle_export(uid): #
    if os.path.exists(DB_FILE): bot.send_document(uid, open(DB_FILE, 'rb'), caption="Users Backup")
    if os.path.exists(COURSE_DB): bot.send_document(uid, open(COURSE_DB, 'rb'), caption="Courses Backup")

@bot.message_handler(commands=['broadcast'])
def start_broadcast(message):
    if str(message.chat.id) == ADMIN_ID:
        msg = bot.send_message(ADMIN_ID, "📢 संदेश (फोटो या टेक्स्ट) भेजें:", parse_mode="HTML")
        bot.register_next_step_handler(msg, send_broadcast)

def send_broadcast(message):
    data = load_data()
    for uid in data.keys():
        try:
            if message.content_type == 'text': bot.send_message(uid, f"📢 <b>Announcement:</b>\n\n{message.text}", parse_mode="HTML")
            elif message.content_type == 'photo': bot.send_photo(uid, message.photo[-1].file_id, caption=f"📢 {message.caption if message.caption else ''}", parse_mode="HTML")
        except: continue
    bot.send_message(ADMIN_ID, "✅ Broadcast complete.")

# --- 8. कोर्स मैनेजमेंट (Re-sub Fix) ---
@bot.message_handler(commands=['addcourse'])
def add_course_start(message):
    if str(message.chat.id) == ADMIN_ID:
        msg = bot.send_message(ADMIN_ID, "📝 कोर्स का नाम लिखें:", parse_mode="HTML")
        bot.register_next_step_handler(msg, process_course_name)

def process_course_name(message):
    c_name = message.text
    msg = bot.send_message(ADMIN_ID, f"💰 '{c_name}' की कीमत:", parse_mode="HTML")
    bot.register_next_step_handler(msg, process_course_price, c_name)

def process_course_price(message, c_name):
    c_price = message.text
    msg = bot.send_message(ADMIN_ID, "👥 L1 कमीशन:", parse_mode="HTML")
    bot.register_next_step_handler(msg, process_course_l1, c_name, c_price)

def process_course_l1(message, c_name, c_price):
    l1 = message.text
    msg = bot.send_message(ADMIN_ID, "👥 L2 कमीशन:", parse_mode="HTML")
    bot.register_next_step_handler(msg, process_course_l2, c_name, c_price, l1)

def process_course_l2(message, c_name, c_price, l1):
    l2 = message.text
    msg = bot.send_message(ADMIN_ID, "🔗 Drive Link:", parse_mode="HTML")
    bot.register_next_step_handler(msg, finalize_course, c_name, c_price, l1, l2)

def finalize_course(message, c_name, c_price, l1, l2):
    courses = load_courses()
    c_id = c_name.lower().replace(" ", "_")
    try:
        courses[c_id] = {"name": c_name, "price": int(re.sub(r'\D', '', c_price)), "l1": int(re.sub(r'\D', '', l1)), "l2": int(re.sub(r'\D', '', l2)), "link": message.text}
        save_courses(courses)
        bot.send_message(ADMIN_ID, f"✅ Done! ID: {c_id}", parse_mode="HTML")
    except: bot.send_message(ADMIN_ID, "❌ Error: Use numbers.")

# --- 9. मेनू और फोटो हैंडलर ---
@bot.message_handler(func=lambda m: True)
def handle_menu(message):
    data, uid = load_data(), str(message.chat.id)
    if uid not in data: return
    text, lang = message.text, data[uid].get("lang", "hi")

    # Admin Panel
    if text == "🛠 Admin Panel" and uid == ADMIN_ID:
        bot.send_message(uid, "🛠 Admin Control:", reply_markup=get_admin_menu(), parse_mode="HTML")
    elif text == "📊 Stats" and uid == ADMIN_ID: bot.send_message(uid, get_stats(), parse_mode="HTML")
    elif text == "👤 Search User" and uid == ADMIN_ID:
        msg = bot.send_message(uid, "🔍 User ID भेजें:")
        bot.register_next_step_handler(msg, process_user_search)
    elif text == "📥 Export Data" and uid == ADMIN_ID: handle_export(uid)
    elif text == "📢 Broadcast" and uid == ADMIN_ID: start_broadcast(message)
    elif text == "➕ Add Course" and uid == ADMIN_ID: add_course_start(message)
    elif text == "🔙 Back to Main Menu": bot.send_message(uid, "🔙 Menu", reply_markup=get_main_menu(uid, lang))

    # Language Settings
    elif text == "⚙️ सेटिंग्स" or text == "⚙️ Settings":
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🇮🇳 Hindi", callback_data="setlang_hi"),
                   types.InlineKeyboardButton("🇺🇸 English", callback_data="setlang_en"))
        bot.send_message(uid, STRINGS[lang]["lang_select"], reply_markup=markup, parse_mode="HTML")

    # User Features
    elif text in ["📚 कोर्स खरीदें", "📚 Buy Course"]:
        courses = load_courses()
        purchased = data[uid].get("purchased", [])
        markup = types.InlineKeyboardMarkup()
        for cid, info in courses.items():
            if cid in purchased: markup.add(types.InlineKeyboardButton(f"📥 Download {info['name']}", url=info['link']))
            else: markup.add(types.InlineKeyboardButton(f"🛒 {info['name']} - ₹{info['price']}", callback_data=f"buyinfo_{cid}"))
        bot.send_message(uid, STRINGS[lang]["buy_menu"], reply_markup=markup, parse_mode="HTML")

    elif text in ["🏆 लीडरबोर्ड", "🏆 Leaderboard"]:
        sorted_u = sorted(data.items(), key=lambda x: x[1].get('referrals', 0), reverse=True)
        lt = STRINGS[lang]["leaderboard_header"]
        for i, (u_id, u_data) in enumerate(sorted_u[:10], 1):
            lt += f"{i}. {u_data.get('name')} — {u_data.get('referrals', 0)} Refs\n"
        bot.send_message(uid, lt, parse_mode="HTML")

    elif text in ["💰 वॉलेट", "💰 Wallet"]:
        bal = data[uid].get('balance', 0)
        markup = types.InlineKeyboardMarkup()
        if bal >= 500: markup.add(types.InlineKeyboardButton("💸 Withdraw", callback_data=f"ask_wd"))
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
        bot.send_photo(ADMIN_ID, message.photo[-1].file_id, caption=f"📩 <b>New Payment!</b>\nID: <code>{uid}</code>\nCourse: {courses[pending_cid]['name']}", reply_markup=markup, parse_mode="HTML")
        bot.send_message(uid, "✅ Screenshot received! Wait for approval.")

@bot.message_handler(commands=['start'])
def start(message):
    data = load_data()
    uid = str(message.chat.id)
    if uid not in data:
        args = message.text.split()
        ref = args[1] if len(args) > 1 else None
        data[uid] = {"name": message.from_user.first_name, "balance": 0, "referred_by": ref, "status": "Free", "referrals": 0, "lang": "hi", "purchased": []}
        save_data(data)
    lang = data[uid].get("lang", "hi")
    bot.send_photo(uid, WELCOME_PHOTO, caption=STRINGS[lang]["welcome"].format(name=message.from_user.first_name), reply_markup=get_main_menu(uid, lang), parse_mode="HTML")

def get_main_menu(uid, lang):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    b = STRINGS[lang]["btns"]
    markup.add(b[0], b[1])
    markup.add(b[2], b[3])
    markup.add(b[4], b[5])
    if str(uid) == ADMIN_ID: markup.add("🛠 Admin Panel")
    return markup

def process_withdrawal(message, amt):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("✅ Payout Complete", callback_data=f"wdpay_{message.chat.id}_{amt}"),
               types.InlineKeyboardButton("❌ Cancel", callback_data=f"wdrej_{message.chat.id}"))
    bot.send_message(ADMIN_ID, f"🔔 <b>Withdraw: ₹{amt}</b>\nUPI: <code>{message.text}</code>", reply_markup=markup, parse_mode="HTML")
    bot.send_message(message.chat.id, "✅ Request Sent!")

if __name__ == "__main__":
    keep_alive()
    bot.polling(none_stop=True)
    
