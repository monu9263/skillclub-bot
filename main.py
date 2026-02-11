import telebot
from telebot import types
import json
import os
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

# --- 2. भाषा और मैसेज (Bilingual HTML Mode) ---
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

# --- 4. वेब सर्वर (24/7 Uptime) ---
app = Flask('')
@app.route('/')
def home(): return "Skillclub Online!"
def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive():
    t = Thread(target=run)
    t.start()

# --- 5. एडमिन कोर्स मैनेजमेंट (Step-by-Step) ---
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
    courses[c_id] = {"name": c_name, "price": int(c_price), "l1": int(l1_comm), "l2": int(l2_comm), "link": c_link}
    save_courses(courses)
    bot.send_message(message.chat.id, f"✅ <b>कोर्स सफलतापूर्वक जुड़ गया!</b>\nID: <code>{c_id}</code>", parse_mode="HTML")

# --- 6. अप्रूवल और कमीशन लॉजिक ---
@bot.callback_query_handler(func=lambda call: True)
def callbacks(call):
    data = load_data()
    courses = load_courses()
    uid = str(call.message.chat.id)
    
    # maxsplit=1 लगाने से 'ai_influencer' जैसा नाम पूरा मिलेगा
    parts = call.data.split('_', 1)
    action = parts[0]
    
    if action == "buyinfo":
        if len(parts) < 2: return
        cid = parts[1]
        
        if cid in courses:
            # यूजर का पेंडिंग कोर्स अपडेट करना
            if uid not in data: # सेफ्टी के लिए
                data[uid] = {"name": call.from_user.first_name, "balance": 0, "status": "Free", "referrals": 0, "lang": "hi"}
            
            data[uid]["pending_buy"] = cid
            save_data(data)
            
            lang = data[uid].get("lang", "hi")
            course = courses[cid]
            
            bot.send_message(uid, STRINGS[lang]["payment_instruction"].format(
                cname=course['name'], 
                price=course['price'], 
                upi=ADMIN_UPI
            ), parse_mode="HTML")
        else:
            bot.answer_callback_query(call.id, "❌ कोर्स डेटाबेस में नहीं मिला!")

    elif action == "app":
        # यहाँ भी वही स्प्लिट लॉजिक सुधारें
        parts = call.data.split('_')
        t_id = parts[1]
        cid = "_".join(parts[2:]) # बाकी बचा हुआ हिस्सा कोर्स ID है
        
        if t_id in data:
            course = courses[cid]
            data[t_id]["status"] = f"Paid ({course['name']})"
            # ... बाकी कमीशन लॉजिक ...
            save_data(data)
            bot.send_message(t_id, f"🥳 <b>अप्रूव हो गया!</b>", parse_mode="HTML")
            bot.edit_message_caption("✅ APPROVED", ADMIN_ID, call.message.message_id)
# --- 7. बटन्स और मेनू हैंडलर ---
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
        data[uid] = {"name": message.from_user.first_name, "balance": 0, "referred_by": ref_id, "status": "Free", "referrals": 0, "lang": "hi", "pending_buy": None}
        save_data(data)
    lang = data[uid].get("lang", "hi")
    bot.send_message(uid, STRINGS[lang]["welcome"].format(name=message.from_user.first_name), reply_markup=get_menu(uid, lang), parse_mode="HTML")

@bot.message_handler(func=lambda m: True)
def handle_menu(message):
    data = load_data()
    uid = str(message.chat.id)
    lang = data[uid].get("lang", "hi")
    text = message.text

    if text in ["📚 कोर्स खरीदें", "📚 Buy Course"]:
        courses = load_courses()
        if not courses:
            bot.send_message(uid, "❌ अभी कोई कोर्स उपलब्ध नहीं है।")
            return
        markup = types.InlineKeyboardMarkup()
        for cid, info in courses.items():
            markup.add(types.InlineKeyboardButton(f"🛒 {info['name']} - ₹{info['price']}", callback_data=f"buyinfo_{cid}"))
        bot.send_message(uid, STRINGS[lang]["buy_menu"], reply_markup=markup, parse_mode="HTML")

    elif text in ["👤 प्रोफाइल", "👤 Profile"]:
        bot.send_message(uid, STRINGS[lang]["profile"].format(name=data[uid]['name'], status=data[uid]['status'], refs=data[uid].get('referrals', 0)), parse_mode="HTML")

    elif text in ["💰 वॉलेट", "💰 Wallet"]:
        bot.send_message(uid, STRINGS[lang]["wallet"].format(bal=data[uid]['balance']), parse_mode="HTML")

# --- 8. फोटो हैंडलर (Approval System) ---
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
        bot.send_message(uid, "❌ पहले कोर्स चुनें, फिर स्क्रीनशॉट भेजें।")

if __name__ == "__main__":
    keep_alive()
    print("🚀 Skillclub Bot is Starting...")
    while True:
        try:
            bot.polling(none_stop=True, interval=0, timeout=20)
        except Exception as e:
            print(f"⚠️ Error: {e}")
            time.sleep(5)
