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

# --- 2. भाषा और मैसेज (HTML Mode) ---
STRINGS = {
    "hi": {
        "welcome": "नमस्ते {name}! <b>Skillclub</b> में स्वागत है।",
        "profile": "👤 <b>नाम:</b> {name}\n🏆 <b>स्टेटस:</b> {status}\n👥 <b>रेफरल:</b> {refs}",
        "buy_menu": "🎓 <b>हमारे उपलब्ध कोर्सेस चुनें:</b>",
        "payment_instruction": "🚀 <b>कोर्स:</b> {cname}\n💰 <b>कीमत:</b> ₹{price}\n\n1. UPI: <code>{upi}</code> पर पेमेंट करें।\n2. स्क्रीनशॉट इसी बोट में भेजें।",
        "wallet": "💰 <b>वॉलेट बैलेंस:</b> ₹{bal}\n📉 न्यूनतम विड्रॉल: ₹500",
        "invite": "🔥 <b>आपका इनवाइट लिंक:</b>\n{link}",
        "btns": ["👤 प्रोफाइल", "🔗 इनवाइट लिंक", "💰 वॉलेट", "📚 कोर्स खरीदें", "⚙️ सेटिंग्स"]
    },
    "en": {
        "welcome": "Hello {name}! Welcome to <b>Skillclub</b>.",
        "profile": "👤 <b>Name:</b> {name}\n🏆 <b>Status:</b> {status}\n👥 <b>Referrals:</b> {refs}",
        "buy_menu": "🎓 <b>Choose from our available courses:</b>",
        "payment_instruction": "🚀 <b>Course:</b> {cname}\n💰 <b>Price:</b> ₹{price}\n\n1. Send payment to UPI: <code>{upi}</code>\n2. Send screenshot here.",
        "wallet": "💰 <b>Wallet Balance:</b> ₹{bal}\n📉 Min. Withdrawal: ₹500",
        "invite": "🔥 <b>Your Invite Link:</b>\n{link}",
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

def load_courses():
    if not os.path.exists(COURSE_DB):
        with open(COURSE_DB, 'w') as f: json.dump({}, f)
        return {}
    try:
        with open(COURSE_DB, 'r') as f: return json.load(f)
    except: return {}

def save_courses(data):
    with open(COURSE_DB, 'w') as f: json.dump(data, f, indent=4)

# --- 4. वेब सर्वर (24/7) ---
app = Flask('')
@app.route('/')
def home(): return "Skillclub Online!"
def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive():
    t = Thread(target=run)
    t.start()

# --- 5. एडमिन कोर्स मैनेजमेंट ---
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
    c_link = message.text
    courses = load_courses()
    c_id = c_name.lower().replace(" ", "_")
    try:
        clean_price = int(re.sub(r'\D', '', c_price))
        clean_l1 = int(re.sub(r'\D', '', l1_comm))
        clean_l2 = int(re.sub(r'\D', '', l2_comm))
        courses[c_id] = {"name": c_name, "price": clean_price, "l1": clean_l1, "l2": clean_l2, "link": c_link}
        save_courses(courses)
        bot.send_message(message.chat.id, f"✅ <b>कोर्स जुड़ गया!</b> ID: <code>{c_id}</code>", parse_mode="HTML")
    except:
        bot.send_message(message.chat.id, "❌ एरर: नंबर का उपयोग करें।")

# --- 6. मुख्य लॉजिक (Approval & Menu Fixes) ---
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
            lang = data[uid].get("lang", "hi")
            bot.send_message(uid, STRINGS[lang]["payment_instruction"].format(cname=courses[cid]['name'], price=courses[cid]['price'], upi=ADMIN_UPI), parse_mode="HTML")

    elif action == "app": # अप्रूवल लॉजिक (Fix 1)
        app_parts = call.data.split('_')
        t_id = app_parts[1]
        cid = "_".join(app_parts[2:])
        
        if t_id in data:
            course = courses[cid]
            # खरीदे गए कोर्स को रिकॉर्ड में जोड़ना
            if "purchased" not in data[t_id]: data[t_id]["purchased"] = []
            
            if cid not in data[t_id]["purchased"]:
                data[t_id]["purchased"].append(cid)
                data[t_id]["status"] = "Paid"
                
                # कमीशन लॉजिक (L1 & L2)
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
            # यूजर को तुरंत डाउनलोड बटन भेजना
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("📥 कोर्स डाउनलोड करें", url=course['link']))
            bot.send_message(t_id, f"🥳 <b>मुबारक हो!</b>\nपेमेंट अप्रूव हो गया है।", reply_markup=markup, parse_mode="HTML")
            bot.edit_message_caption(f"✅ APPROVED: {course['name']}", ADMIN_ID, call.message.message_id)

@bot.message_handler(func=lambda m: True)
def handle_menu(message):
    data = load_data()
    uid = str(message.chat.id)
    lang = data[uid].get("lang", "hi")
    text = message.text

    if text in ["📚 कोर्स खरीदें", "📚 Buy Course"]: # मेनू लॉजिक (Fix 2)
        courses = load_courses()
        if not courses:
            bot.send_message(uid, "❌ कोई कोर्स नहीं है।")
            return
            
        purchased_list = data[uid].get("purchased", [])
        markup = types.InlineKeyboardMarkup()
        for cid, info in courses.items():
            if cid in purchased_list: # अगर खरीदा है तो डाउनलोड लिंक
                markup.add(types.InlineKeyboardButton(f"📥 Download {info['name']}", url=info['link']))
            else: # वरना खरीदने का बटन
                markup.add(types.InlineKeyboardButton(f"🛒 {info['name']} - ₹{info['price']}", callback_data=f"buyinfo_{cid}"))
        bot.send_message(uid, STRINGS[lang]["buy_menu"], reply_markup=markup, parse_mode="HTML")

    elif text in ["👤 प्रोफाइल", "👤 Profile"]:
        bot.send_message(uid, STRINGS[lang]["profile"].format(name=data[uid]['name'], status=data[uid]['status'], refs=data[uid].get('referrals', 0)), parse_mode="HTML")

    elif text in ["💰 वॉलेट", "💰 Wallet"]:
        bot.send_message(uid, STRINGS[lang]["wallet"].format(bal=data[uid]['balance']), parse_mode="HTML")

# --- 8. फोटो हैंडलर ---
@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    uid = str(message.chat.id)
    data = load_data()
    pending_cid = data[uid].get("pending_buy")
    if pending_cid:
        courses = load_courses()
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("✅ Approve", callback_data=f"app_{uid}_{pending_cid}"),
                   types.InlineKeyboardButton("❌ Reject", callback_data=f"rej_{uid}"))
        bot.send_photo(ADMIN_ID, message.photo[-1].file_id, caption=f"📩 <b>नया पेमेंट!</b>\nID: <code>{uid}</code>\nकोर्स: {courses[pending_cid]['name']}", reply_markup=markup, parse_mode="HTML")
        bot.send_message(uid, "✅ स्क्रीनशॉट मिल गया! अप्रूवल का इंतज़ार करें।")
    else:
        bot.send_message(uid, "❌ पहले कोर्स चुनें।")

@bot.message_handler(commands=['start'])
def start(message):
    data = load_data()
    uid = str(message.chat.id)
    if uid not in data:
        args = message.text.split()
        ref_id = args[1] if len(args) > 1 else None
        data[uid] = {"name": message.from_user.first_name, "balance": 0, "referred_by": ref_id, "status": "Free", "referrals": 0, "lang": "hi", "pending_buy": None, "purchased": []}
        save_data(data)
    lang = data[uid].get("lang", "hi")
    bot.send_message(uid, STRINGS[lang]["welcome"].format(name=message.from_user.first_name), reply_markup=get_menu(uid, lang), parse_mode="HTML")

def get_menu(uid, lang):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    b = STRINGS[lang]["btns"]
    markup.add(b[0], b[1])
    markup.add(b[2], b[3])
    markup.add(b[4])
    if str(uid) == ADMIN_ID: markup.add("🛠 Admin Panel")
    return markup

if __name__ == "__main__":
    keep_alive()
    print("🚀 Skillclub Bot is Starting...")
    while True:
        try:
            bot.polling(none_stop=True, interval=0, timeout=20)
        except Exception as e:
            time.sleep(5)
