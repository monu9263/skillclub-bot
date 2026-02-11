import os
import telebot
import json
import time
import datetime
import random
from flask import Flask
from threading import Thread

# 1. कॉन्फ़िगरेशन
API_TOKEN = os.getenv('API_TOKEN')
ADMIN_ID = os.getenv('ADMIN_ID')
bot = telebot.TeleBot(API_TOKEN)
app = Flask('')

# 2. अपडेटेड कोर्सेस (AI Course @ 300)
COURSES = {
    "ai_basic": {
        "name": "AI Influencer Basic", 
        "price": 300, 
        "commission": 150,
        "link": "https://your-download-link.com/ai-course" # यहाँ अपना असली लिंक डालें
    },
    "marketing_pro": {
        "name": "Advanced Marketing", 
        "price": 999, 
        "commission": 450,
        "link": "https://your-download-link.com/marketing"
    }
}

# 3. डेटाबेस हेल्पर्स
def load_data():
    if not os.path.exists('users.json'): return {}
    with open('users.json', 'r', encoding='utf-8') as f: return json.load(f)

def save_data(data):
    with open('users.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# 4. इनवॉइस फंक्शन
def send_invoice(user_id, course_id, amount):
    course = COURSES.get(course_id)
    invoice_text = (
        f"📄 **Skillclub Official Invoice**\n"
        f"--------------------------\n"
        f"**Course:** {course['name']}\n"
        f"**Amount Paid:** ₹{amount}\n"
        f"**Status:** ✅ SUCCESSFUL\n"
        f"--------------------------\n"
        f"अब आप '📚 Courses' सेक्शन में जाकर इसे डाउनलोड कर सकते हैं।"
    )
    bot.send_message(user_id, invoice_text, parse_mode="Markdown")

# 5. Render Keep Alive
@app.route('/')
def home(): return "Skillclub Bot is Online!"

def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive(): Thread(target=run).start()

# --- बोट कमांड्स ---

@bot.message_handler(commands=['start'])
def start(message):
    user_id = str(message.from_user.id)
    users = load_data()
    if user_id not in users:
        users[user_id] = {"name": message.from_user.first_name, "referrals": 0, "balance": 0, "purchased_courses": []}
        save_data(users)
    
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("👤 Profile", "📚 Courses")
    markup.add("🏆 Leaderboard", "🤖 Ask AI")
    markup.add("💰 Wallet")
    bot.send_message(message.chat.id, "Skillclub में आपका स्वागत है!", reply_markup=markup)

# 👤 Profile Section
@bot.message_handler(func=lambda m: m.text == "👤 Profile")
def profile(message):
    user_id = str(message.from_user.id)
    users = load_data()
    u = users.get(user_id, {})
    text = (
        f"👤 **User Profile**\n\n"
        f"📛 Name: {u.get('name')}\n"
        f"💰 Balance: ₹{u.get('balance')}\n"
        f"👥 Referrals: {u.get('referrals')}\n"
        f"🎓 Courses: {len(u.get('purchased_courses', []))}"
    )
    bot.send_message(message.chat.id, text, parse_mode="Markdown")

# 💰 Wallet Section
@bot.message_handler(func=lambda m: m.text == "💰 Wallet")
def wallet(message):
    user_id = str(message.from_user.id)
    users = load_data()
    u = users.get(user_id, {})
    ref_link = f"https://t.me/{(bot.get_me()).username}?start={user_id}"
    text = (
        f"💰 **Skillclub Wallet**\n\n"
        f"Current Balance: ₹{u.get('balance')}\n"
        f"Minimum Withdrawal: ₹500\n\n"
        f"🔗 Referral Link to Earn:\n`{ref_link}`"
    )
    bot.send_message(message.chat.id, text, parse_mode="Markdown")

# 📚 Courses & Download Logic
@bot.message_handler(func=lambda m: m.text == "📚 Courses")
def show_courses(message):
    user_id = str(message.from_user.id)
    users = load_data()
    purchased = users.get(user_id, {}).get('purchased_courses', [])
    
    markup = telebot.types.InlineKeyboardMarkup()
    for cid, info in COURSES.items():
        if cid in purchased:
            btn = telebot.types.InlineKeyboardButton(f"📥 Download {info['name']}", url=info['link'])
        else:
            btn = telebot.types.InlineKeyboardButton(f"🛒 Buy {info['name']} - ₹{info['price']}", callback_data=f"buy_{cid}")
        markup.add(btn)
    bot.send_message(message.chat.id, "कोर्स चुनें (खरीदे हुए कोर्स पर डाउनलोड बटन दिखेगा):", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('buy_'))
def handle_buy(call):
    cid = call.data.split('_')[1]
    course = COURSES[cid]
    bot.send_message(call.message.chat.id, f"✅ **{course['name']}** खरीदने के लिए ₹{course['price']} एडमिन को भेजें।\n\nकमीशन: ₹{course['commission']}")

# 🤖 Ask AI
@bot.message_handler(func=lambda m: m.text == "🤖 Ask AI")
def ask_ai(message):
    bot.reply_to(message, "🤖 **Skillclub AI Assistant** सक्रिय है।\nअपना सवाल /ask लिखकर पूछें।\nउदाहरण: `/ask AI Influencer कैसे बनाएं?`", parse_mode="Markdown")

@bot.message_handler(commands=['ask'])
def ai_logic(message):
    query = message.text.replace('/ask', '').strip()
    if not query: return
    bot.reply_to(message, f"🤖 Skillclub AI विश्लेषण कर रहा है: '{query}'...")

# 📢 Admin Broadcast
@bot.message_handler(commands=['broadcast'])
def admin_broadcast(message):
    if str(message.from_user.id) == ADMIN_ID:
        text = message.text.replace('/broadcast', '').strip()
        if not text: return
        users = load_data()
        for uid in users:
            try: bot.send_message(uid, f"📢 **ANNOUNCEMENT**\n\n{text}", parse_mode="Markdown")
            except: continue
        bot.reply_to(message, "✅ संदेश प्रसारित कर दिया गया है।")

# ✅ Admin Payment Confirmation
@bot.message_handler(commands=['confirm'])
def confirm(message):
    if str(message.from_user.id) == ADMIN_ID:
        try:
            _, target_id, cid = message.text.split()
            users = load_data()
            if cid in COURSES and target_id in users:
                users[target_id]['purchased_courses'].append(cid)
                save_data(users)
                send_invoice(target_id, cid, COURSES[cid]['price'])
                bot.reply_to(message, f"✅ User {target_id} का कोर्स एक्टिव हो गया है।")
        except: bot.reply_to(message, "उपयोग: /confirm [user_id] [course_id]")

if __name__ == "__main__":
    keep_alive()
    bot.polling(none_stop=True)
