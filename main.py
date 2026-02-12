import telebot
from telebot import types
import json
import os
import time

# --- 1. CONFIGURATION ---
API_TOKEN = os.getenv('API_TOKEN')
ADMIN_ID = "8114779182"  # Aapki Admin ID
SUPPORT_BOT_USERNAME = "SkillClubHelpBot" # Bina @ ke

bot = telebot.TeleBot(API_TOKEN)

# Data Files
DB_FILE = 'users.json'
COURSE_DB = 'courses.json'
SETTINGS_FILE = 'settings.json'

# --- 2. DATA MANAGERS ---
def load_json(filename):
    if not os.path.exists(filename):
        with open(filename, 'w') as f: json.dump({}, f)
        return {}
    try:
        with open(filename, 'r') as f: return json.load(f)
    except: return {}

def save_json(filename, data):
    with open(filename, 'w') as f: json.dump(data, f, indent=4)

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

# --- 4. BROADCAST LOGIC ---
def process_broadcast(message):
    data = load_json(DB_FILE)
    count = 0
    status_msg = bot.send_message(ADMIN_ID, "⏳ **Broadcasting started...**", parse_mode="Markdown")
    for user_id in data:
        try:
            bot.copy_message(user_id, ADMIN_ID, message.message_id)
            count += 1
            time.sleep(0.05) # Rate limit se bachne ke liye
        except: continue
    bot.edit_message_text(f"✅ **Broadcast Done!**\nSent to: {count} users", ADMIN_ID, status_msg.message_id, parse_mode="Markdown")

# --- 5. START COMMAND ---
@bot.message_handler(commands=['start'])
def start_cmd(message):
    data, uid = load_json(DB_FILE), str(message.chat.id)
    if uid not in data:
        args = message.text.split()
        ref = args[1] if len(args) > 1 else None
        data[uid] = {
            "name": message.from_user.first_name, 
            "balance": 0, "referred_by": ref, 
            "status": "Free", "referrals": 0, "lang": "hi", 
            "purchased": [], "join_date": time.strftime("%Y-%m-%d")
        }
        save_json(DB_FILE, data)

    lang = data[uid].get("lang", "hi")
    welcome = "नमस्ते! Skillclub में आपका स्वागत है।" if lang == "hi" else "Welcome to Skillclub!"
    bot.send_message(uid, welcome, reply_markup=get_main_menu(uid, lang))

# --- 6. MAIN MESSAGE HANDLER ---
@bot.message_handler(func=lambda m: True)
def handle_all_messages(message):
    uid = str(message.chat.id)
    data = load_json(DB_FILE)
    if uid not in data: return
    
    text = message.text
    lang = data[uid].get("lang", "hi")

    # --- 📚 COURSE BUTTON ---
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

    # --- 📞 SUPPORT BUTTON (Magic Link) ---
    elif text in ["📞 सहायता", "📞 Support"]:
        sales = len(data[uid].get("purchased", []))
        bal = data[uid].get("balance", 0)
        status = data[uid].get("status", "Free")
        join_date = data[uid].get("join_date", "Old")
        
        payload = f"{sales}_{bal}_{status}_{join_date}".replace(" ", "")
        magic_link = f"https://t.me/{SUPPORT_BOT_USERNAME}?start={payload}"

        m = types.InlineKeyboardMarkup()
        # Custom Buttons from Settings
        settings = load_json(SETTINGS_FILE)
        for b in settings.get("buttons", []):
            m.add(types.InlineKeyboardButton(f"👉 {b['name']}", url=b['url']))
        # Live Chat Button
        btn_txt = "💬 एडमिन से चैट करें" if lang == "hi" else "💬 Chat with Admin"
        m.add(types.InlineKeyboardButton(btn_txt, url=magic_link))
        
        bot.send_message(uid, "सपोर्ट मेनू:" if lang == "hi" else "Support Menu:", reply_markup=m)

    # --- 🛠 ADMIN PANEL ---
    elif text == "🛠 Admin Panel" and uid == ADMIN_ID:
        m = types.ReplyKeyboardMarkup(resize_keyboard=True)
        m.add("📊 Stats", "📢 Broadcast")
        m.add("🔙 वापस")
        bot.send_message(uid, "Admin Control Panel:", reply_markup=m)

    elif text == "📢 Broadcast" and uid == ADMIN_ID:
        msg = bot.send_message(uid, "📢 **ब्रॉडकास्ट मैसेज भेजें (Text/Photo/Video):**", parse_mode="Markdown")
        bot.register_next_step_handler(msg, process_broadcast)

    # --- 👤 PROFILE ---
    elif text in ["👤 प्रोफाइल", "👤 Profile"]:
        p = data[uid]
        msg = f"👤 **Profile**\nName: {p['name']}\nStatus: {p['status']}\nBalance: ₹{p['balance']}"
        bot.send_message(uid, msg, parse_mode="Markdown")

    elif text in ["🔙 वापस", "🔙 Back"]:
        bot.send_message(uid, "Main Menu:", reply_markup=get_main_menu(uid, lang))

# --- 7. RUNNING THE BOT ---
if __name__ == "__main__":
    print("🚀 Main Bot Started...")
    bot.polling(none_stop=True)
