import telebot
from telebot import types
import json, os, time, random, string
from flask import Flask
from threading import Thread

# --- 1. CONFIGURATION ---
API_TOKEN = os.getenv('API_TOKEN')
ADMIN_ID = "8114779182"  #
SUPPORT_BOT_USERNAME = "SkillClubHelpBot" 

bot = telebot.TeleBot(API_TOKEN)
app = Flask('')

# Database Files
DB_FILE = 'users.json'
COURSE_DB = 'courses.json'
SETTINGS_FILE = 'settings.json'

# --- 2. DATA HELPERS ---
def load_json(file):
    if not os.path.exists(file): return {}
    try:
        with open(file, 'r') as f: return json.load(f)
    except: return {}

def save_json(file, data):
    with open(file, 'w') as f: json.dump(data, f, indent=4)

# --- 3. KEYBOARDS ---
def get_main_menu(uid, lang):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    if lang == "hi":
        markup.add("👤 प्रोफाइल", "🔗 इनवाइट लिंक")
        markup.add("💰 वॉलेट", "📚 कोर्स खरीदें")
        markup.add("📞 सहायता", "⚙️ सेटिंग्स")
    else:
        markup.add("👤 Profile", "🔗 Invite Link")
        markup.add("💰 Wallet", "📚 Buy Course")
        markup.add("📞 Support", "⚙️ Settings")
    
    if str(uid) == ADMIN_ID:
        markup.add("🛠 Admin Panel")
    return markup

# --- 4. BROADCAST SYSTEM ---
def process_broadcast(message):
    data = load_json(DB_FILE)
    count = 0
    status = bot.send_message(ADMIN_ID, "⏳ **Broadcasting started...**", parse_mode="Markdown")
    for user_id in data:
        try:
            bot.copy_message(user_id, ADMIN_ID, message.message_id)
            count += 1
            time.sleep(0.05)
        except: continue
    bot.edit_message_text(f"✅ **Broadcast Done!**\nSent to: {count} users", ADMIN_ID, status.message_id)

# --- 5. START & REFERRAL SYSTEM ---
@bot.message_handler(commands=['start'])
def start_cmd(message):
    data, uid = load_json(DB_FILE), str(message.chat.id)
    if uid not in data:
        args = message.text.split()
        ref = args[1] if len(args) > 1 else None
        
        # New User Entry
        data[uid] = {
            "name": message.from_user.first_name,
            "balance": 0,
            "referred_by": ref,
            "referrals": 0,
            "status": "Free",
            "lang": "hi",
            "purchased": [],
            "join_date": time.strftime("%Y-%m-%d")
        }
        
        # Referral Reward Logic
        if ref and ref in data and ref != uid:
            data[ref]['referrals'] += 1
            # Example: Add 5 INR per referral
            # data[ref]['balance'] += 5 
            bot.send_message(ref, f"🔔 **New Referral!**\n{data[uid]['name']} has joined using your link.")
        
        save_json(DB_FILE, data)

    lang = data[uid].get("lang", "hi")
    welcome_text = "नमस्ते! Skillclub में आपका स्वागत है।" if lang == "hi" else "Welcome to Skillclub!"
    bot.send_message(uid, welcome_text, reply_markup=get_main_menu(uid, lang))

# --- 6. CORE MESSAGE HANDLERS ---
@bot.message_handler(func=lambda m: True)
def handle_all_messages(message):
    uid = str(message.chat.id)
    data = load_json(DB_FILE)
    if uid not in data: return
    
    text = message.text
    lang = data[uid].get("lang", "hi")

    # --- 📚 COURSE SYSTEM ---
    if text in ["📚 कोर्स खरीदें", "📚 Buy Course"]:
        courses = load_json(COURSE_DB)
        purchased = data[uid].get("purchased", [])
        m = types.InlineKeyboardMarkup()
        for cid, info in courses.items():
            if cid in purchased:
                m.add(types.InlineKeyboardButton(f"📥 Download {info['name']}", url=info['link']))
            else:
                m.add(types.InlineKeyboardButton(f"🛒 {info['name']} - ₹{info['price']}", callback_data=f"buyinfo_{cid}"))
        bot.send_message(uid, "उपलब्ध कोर्सेस:" if lang == "hi" else "Available Courses:", reply_markup=m)

    # --- 👤 PROFILE ---
    elif text in ["👤 प्रोफाइल", "👤 Profile"]:
        p = data[uid]
        msg = (f"👤 **{p['name']}**\n"
               f"━━━━━━━━━━━━━━\n"
               f"🏆 Status: {p['status']}\n"
               f"💰 Balance: ₹{p['balance']}\n"
               f"👥 Referrals: {p['referrals']}\n"
               f"📅 Joined: {p['join_date']}")
        bot.send_message(uid, msg, parse_mode="Markdown")

    # --- 🔗 INVITE LINK ---
    elif text in ["🔗 इनवाइट लिंक", "🔗 Invite Link"]:
        bot_uname = bot.get_me().username
        link = f"https://t.me/{bot_uname}?start={uid}"
        msg = f"🔗 **आपका इनवाइट लिंक:**\n\n{link}\n\nअपने दोस्तों को जोड़ें और रिवॉर्ड पाएं!"
        bot.send_message(uid, msg)

    # --- 💰 WALLET ---
    elif text in ["💰 वॉलेट", "💰 Wallet"]:
        bal = data[uid]['balance']
        m = types.InlineKeyboardMarkup()
        m.add(types.InlineKeyboardButton("➕ Add Money", callback_data="add_money"),
              types.InlineKeyboardButton("📤 Withdraw", callback_data="withdraw"))
        bot.send_message(uid, f"💰 **Wallet Balance:** ₹{bal}", reply_markup=m)

    # --- 📞 SUPPORT (MAGIC LINK FIX) ---
    elif text in ["📞 सहायता", "📞 Support"]:
        p = data[uid]
        sales = len(p.get("purchased", []))
        payload = f"{sales}_{p['balance']}_{p['status']}_{p['join_date']}".replace(" ", "")
        magic_link = f"https://t.me/{SUPPORT_BOT_USERNAME}?start={payload}"

        m = types.InlineKeyboardMarkup()
        # Custom Buttons from settings.json
        settings = load_json(SETTINGS_FILE)
        for b in settings.get("buttons", []):
            m.add(types.InlineKeyboardButton(f"👉 {b['name']}", url=b['url']))
        m.add(types.InlineKeyboardButton("💬 Live Chat with Admin", url=magic_link))
        
        bot.send_message(uid, "सपोर्ट के लिए बटन चुनें:" if lang == "hi" else "Select Support Option:", reply_markup=m)

    # --- 🛠 ADMIN PANEL ---
    elif text == "🛠 Admin Panel" and uid == ADMIN_ID:
        m = types.ReplyKeyboardMarkup(resize_keyboard=True)
        m.add("📊 Stats", "📢 Broadcast")
        m.add("🔙 वापस")
        bot.send_message(uid, "🛠 एडमिन कंट्रोल पैनल में आपका स्वागत है।", reply_markup=m)

    elif text == "📢 Broadcast" and uid == ADMIN_ID:
        msg = bot.send_message(uid, "📢 वह मैसेज भेजें जिसे आप सबको भेजना चाहते हैं:")
        bot.register_next_step_handler(msg, process_broadcast)

    elif text == "📊 Stats" and uid == ADMIN_ID:
        total_users = len(data)
        bot.send_message(uid, f"📊 **Bot Stats:**\nTotal Users: {total_users}")

    elif text in ["🔙 वापस", "🔙 Back"]:
        bot.send_message(uid, "मुख्य मेनू:", reply_markup=get_main_menu(uid, lang))

# --- 7. CALLBACK HANDLERS (Course Buying, etc.) ---
@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    uid = str(call.message.chat.id)
    data = load_json(DB_FILE)
    
    if call.data.startswith("buyinfo_"):
        cid = call.data.split("_")[1]
        courses = load_json(COURSE_DB)
        if cid in courses:
            c = courses[cid]
            msg = f"🛒 **{c['name']}**\nPrice: ₹{c['price']}\n\nक्या आप इसे खरीदना चाहते हैं?"
            m = types.InlineKeyboardMarkup()
            m.add(types.InlineKeyboardButton("✅ Confirm Purchase", callback_data=f"buyfinal_{cid}"))
            bot.edit_message_text(msg, uid, call.message.message_id, reply_markup=m)

    elif call.data.startswith("buyfinal_"):
        cid = call.data.split("_")[1]
        courses = load_json(COURSE_DB)
        price = courses[cid]['price']
        
        if data[uid]['balance'] >= price:
            data[uid]['balance'] -= price
            data[uid]['purchased'].append(cid)
            data[uid]['status'] = "Paid" # Update Status
            save_json(DB_FILE, data)
            bot.answer_callback_query(call.id, "🎉 Purchase Successful!")
            bot.send_message(uid, f"✅ आपने **{courses[cid]['name']}** सफलतापूर्वक खरीद लिया है।")
        else:
            bot.answer_callback_query(call.id, "❌ अपर्याप्त बैलेंस!", show_alert=True)

# --- 8. RENDER WEB SERVER ---
@app.route('/')
def home(): return "Skillclub Main Bot Active"

def run_flask():
    bot_port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=bot_port)

if __name__ == "__main__":
    Thread(target=run_flask).start()
    print("🚀 Skillclub Bot is Polling...")
    bot.polling(none_stop=True)
