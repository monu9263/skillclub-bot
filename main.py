import os
import telebot
import json
import time
import datetime
import random
from flask import Flask
from threading import Thread

# 1. कॉन्फ़िगरेशन (Render Settings से उठाया जाएगा)
API_TOKEN = os.getenv('API_TOKEN')
ADMIN_ID = str(os.getenv('ADMIN_ID')) 
bot = telebot.TeleBot(API_TOKEN)
app = Flask('')

# 2. कोर्सेस डेटाबेस (AI Course @ 300)
COURSES = {
    "ai": { 
        "name": "AI Influencer Basic", 
        "price": 300, 
        "commission": 150,
        "link": "https://t.me/your_link" # यहाँ अपना असली लिंक डालें
    },
    "marketing": {
        "name": "Advanced Marketing", 
        "price": 999, 
        "commission": 450,
        "link": "https://t.me/your_link"
    }
}

# 3. डेटाबेस मैनेजमेंट
def load_data():
    if not os.path.exists('users.json'): return {}
    with open('users.json', 'r', encoding='utf-8') as f: return json.load(f)

def save_data(data):
    with open('users.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# 4. Render के लिए Keep Alive सर्वर
@app.route('/')
def home(): return "Skillclub Bot is Online!"

def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive(): Thread(target=run, daemon=True).start()

# --- बोट लॉजिक ---

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
    u = load_data().get(user_id, {})
    text = (f"👤 **User Profile**\n\n📛 Name: {u.get('name')}\n💰 Balance: ₹{u.get('balance')}\n"
            f"👥 Referrals: {u.get('referrals')}\n🎓 Courses: {len(u.get('purchased_courses', []))}")
    bot.send_message(message.chat.id, text, parse_mode="Markdown")

# 📚 Courses & Download Logic
@bot.message_handler(func=lambda m: m.text == "📚 Courses")
def show_courses(message):
    user_id = str(message.from_user.id)
    purchased = load_data().get(user_id, {}).get('purchased_courses', [])
    markup = telebot.types.InlineKeyboardMarkup()
    for cid, info in COURSES.items():
        if cid in purchased:
            btn = telebot.types.InlineKeyboardButton(f"📥 Download {info['name']}", url=info['link'])
        else:
            btn = telebot.types.InlineKeyboardButton(f"🛒 Buy {info['name']} - ₹{info['price']}", callback_data=f"buy_{cid}")
        markup.add(btn)
    bot.send_message(message.chat.id, "कोर्स चुनें:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('buy_'))
def handle_buy(call):
    cid = call.data.split('_')[1]
    if cid in COURSES: # यहाँ अब KeyError नहीं आएगा
        course = COURSES[cid]
        bot.send_message(call.message.chat.id, f"✅ **{course['name']}** खरीदने के लिए ₹{course['price']} एडमिन को भेजें।")
    else:
        bot.answer_callback_query(call.id, "कोर्स नहीं मिला!")

# 🏆 Leaderboard
@bot.message_handler(func=lambda m: m.text == "🏆 Leaderboard")
def leaderboard(message):
    users = load_data()
    sorted_u = sorted(users.items(), key=lambda x: x[1].get('referrals', 0), reverse=True)
    text = "🏆 **Top 10 Leaders** 🏆\n\n"
    for i, (uid, data) in enumerate(sorted_u[:10], 1):
        text += f"{i}. {data.get('name')} — {data.get('referrals')} Refs\n"
    bot.send_message(message.chat.id, text, parse_mode="Markdown")

# 🤖 Ask AI (Logic Fixed)
@bot.message_handler(func=lambda m: m.text == "🤖 Ask AI")
def ask_intro(message):
    bot.reply_to(message, "सवाल पूछने के लिए `/ask [आपका प्रश्न]` लिखें।")

@bot.message_handler(commands=['ask'])
def handle_ask(message):
    # यह वह लाइन है जहाँ पिछले कोड में एरर था
    query = message.text.replace('/ask', '').strip()
    if query:
        bot.reply_to(message, f"🤖 Analyzing: '{query}'...")

# 💰 Wallet
@bot.message_handler(func=lambda m: m.text == "💰 Wallet")
def wallet(message):
    user_id = str(message.from_user.id)
    u = load_data().get(user_id, {})
    bot.send_message(message.chat.id, f"💰 Balance: ₹{u.get('balance')}\nMin Withdrawal: ₹500")

# 📢 Admin Broadcast
@bot.message_handler(commands=['broadcast'])
def broadcast(message):
    if str(message.from_user.id) == ADMIN_ID:
        text = message.text.replace('/broadcast', '').strip()
        if text:
            users = load_data()
            for uid in users:
                try: bot.send_message(uid, f"📢 **ANNOUNCEMENT**\n\n{text}", parse_mode="Markdown")
                except: continue
            bot.reply_to(message, "✅ संदेश भेज दिया गया है।")

# ✅ Admin Payment Confirmation
@bot.message_handler(commands=['confirm'])
def confirm(message):
    if str(message.from_user.id) == ADMIN_ID:
        try:
            _, t_id, cid = message.text.split()
            users = load_data()
            if cid in COURSES and t_id in users:
                users[t_id]['purchased_courses'].append(cid)
                save_data(users)
                bot.send_message(t_id, f"✅ Payment Success for {COURSES[cid]['name']}!")
                bot.reply_to(message, "Done!")
        except: bot.reply_to(message, "Use: /confirm [user_id] [course_id]")

# 5. Polling Loop with 409 Conflict Handling
if __name__ == "__main__":
    keep_alive()
    print("🚀 Bot is Starting...")
    while True:
        try:
            bot.polling(none_stop=True)
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(15)
