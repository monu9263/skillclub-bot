import os
import telebot
import json
import time
import datetime
import random
from flask import Flask
from threading import Thread

# 1. Configuration (Secrets used via Environment Variables)
API_TOKEN = os.getenv('API_TOKEN')
ADMIN_ID = str(os.getenv('ADMIN_ID')) # Ensure string for comparison
bot = telebot.TeleBot(API_TOKEN)
app = Flask('')

# 2. Corrected Courses Mapping
COURSES = {
    "ai": { # Match this with callback_data
        "name": "AI Influencer Basic", 
        "price": 300, 
        "commission": 150,
        "link": "https://t.me/your_course_link_ai"
    },
    "marketing": {
        "name": "Advanced Marketing", 
        "price": 999, 
        "commission": 450,
        "link": "https://t.me/your_course_link_pro"
    }
}

# 3. Database Management
def load_data():
    if not os.path.exists('users.json'):
        return {}
    with open('users.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def save_data(data):
    with open('users.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# 4. Flask Server for Render Health Check
@app.route('/')
def home():
    return "Skillclub Bot is Online!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

# --- BOT LOGIC ---

@bot.message_handler(commands=['start'])
def start(message):
    user_id = str(message.from_user.id)
    users = load_data()
    
    if user_id not in users:
        users[user_id] = {
            "name": message.from_user.first_name,
            "referrals": 0,
            "balance": 0,
            "purchased_courses": []
        }
        save_data(users)
    
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("👤 Profile", "📚 Courses")
    markup.add("🏆 Leaderboard", "🤖 Ask AI")
    markup.add("💰 Wallet")
    
    bot.send_message(message.chat.id, "Skillclub mein aapka swagat hai!", reply_markup=markup)

# Profile Feature
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

# Courses with Mapping Fix
@bot.message_handler(func=lambda m: m.text == "📚 Courses")
def list_courses(message):
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
    bot.send_message(message.chat.id, "Choose a course:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('buy_'))
def handle_purchase(call):
    cid = call.data.split('_')[1]
    if cid in COURSES: # Fixed KeyError here
        course = COURSES[cid]
        bot.send_message(call.message.chat.id, f"✅ **{course['name']}** kharidne ke liye ₹{course['price']} Admin ko bhejein.")
    else:
        bot.answer_callback_query(call.id, "Course not found!")

# Leaderboard
@bot.message_handler(func=lambda m: m.text == "🏆 Leaderboard")
def leaderboard(message):
    users = load_data()
    sorted_u = sorted(users.items(), key=lambda x: x[1].get('referrals', 0), reverse=True)
    text = "🏆 **Top 10 Leaders** 🏆\n\n"
    for i, (uid, data) in enumerate(sorted_u[:10], 1):
        text += f"{i}. {data.get('name')} — {data.get('referrals')} Refs\n"
    bot.send_message(message.chat.id, text, parse_mode="Markdown")

# Ask AI (Logic Fix)
@bot.message_handler(func=lambda m: m.text == "🤖 Ask AI")
def ask_intro(message):
    bot.reply_to(message, "Ask anything using `/ask [question]` command.")

@bot.message_handler(commands=['ask'])
def handle_ask(message):
    query = message.
