import os
import telebot
import json
import time
import datetime
import random
from flask import Flask
from threading import Thread

# 1. कॉन्फ़िगरेशन और एनवायरनमेंट वेरिएबल्स
API_TOKEN = os.getenv('API_TOKEN')
ADMIN_ID = os.getenv('ADMIN_ID')
bot = telebot.TeleBot(API_TOKEN)
app = Flask('')

# 2. मल्टी-कोर्स डेटाबेस (नाम, कीमत और कमीशन)
COURSES = {
    "ai_basic": {"name": "AI Influencer Basic", "price": 499, "commission": 200},
    "marketing_pro": {"name": "Advanced Marketing", "price": 999, "commission": 450},
    "masterclass": {"name": "Masterclass Tier 1", "price": 2499, "commission": 1000}
}

# 3. डेटाबेस हेल्पर्स (JSON फाइल मैनेजमेंट)
def load_data():
    if not os.path.exists('users.json'):
        return {}
    with open('users.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def save_data(data):
    with open('users.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# 4. इनवॉइस जनरेट करने का फंक्शन
def send_invoice(user_id, course_id, amount):
    users = load_data()
    user_data = users.get(str(user_id))
    course = COURSES.get(course_id)
    
    if not user_data or not course:
        return
    
    invoice_no = f"SKL-{datetime.datetime.now().strftime('%Y%m%d')}-{random.randint(100, 999)}"
    date = datetime.datetime.now().strftime("%d-%m-%Y %H:%M")
    
    invoice_text = (
        f"📄 **OFFICIAL INVOICE: {course['name']}**\n"
        f"------------------------------------------\n"
        f"**Invoice No:** `{invoice_no}`\n"
        f"**Date:** {date}\n"
        f"**Customer Name:** {user_data.get('name')}\n"
        f"**User ID:** `{user_id}`\n"
        f"------------------------------------------\n"
        f"**Course:** {course['name']}\n"
        f"**Amount Paid:** ₹{amount}\n"
        f"**Status:** ✅ SUCCESSFUL\n"
        f"------------------------------------------\n"
        f"Skillclub में आपका स्वागत है!\n"
        f"अब आप अपना कोर्स एक्सेस कर सकते हैं।"
    )
    bot.send_message(user_id, invoice_text, parse_mode="Markdown")

# 5. Render के लिए Keep Alive सर्वर
@app.route('/')
def home():
    return "Skillclub Bot is Online!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# --- बोट हैंडलर्स ---

# /start कमांड और मेनू
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
    markup.add("📚 Courses", "🏆 Leaderboard")
    markup.add("🤖 Ask AI", "💰 Wallet")
    
    bot.send_message(message.chat.id, f"नमस्ते {message.from_user.first_name}! Skillclub में आपका स्वागत है।", reply_markup=markup)

# कोर्सेस लिस्टिंग
@bot.message_handler(func=lambda m: m.text == "📚 Courses")
def show_courses(message):
    markup = telebot.types.InlineKeyboardMarkup()
    for cid, info in COURSES.items():
        btn = telebot.types.InlineKeyboardButton(f"{info['name']} - ₹{info['price']}", callback_data=f"buy_{cid}")
        markup.add(btn)
    bot.send_message(message.chat.id, "हमारा कोर्स चुनें और सीखना शुरू करें:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('buy_'))
def handle_purchase(call):
    course_id = call.data.split('_')[1]
    course = COURSES.get(course_id)
    if course:
        bot.answer_callback_query(call.id, f"आपने {course['name']} चुना है।")
        bot.send_message(call.message.chat.id, f"✅ **{course['name']}** खरीदने के लिए एडमिन को ₹{course['price']} भेजें।\n\nइस कोर्स पर आपको ₹{course['commission']} कमीशन मिलेगा!")

# लीडरबोर्ड
@bot.message_handler(func=lambda m: m.text == "🏆 Leaderboard")
def leaderboard(message):
    users = load_data()
    sorted_users = sorted(users.items(), key=lambda x: x[1].get('referrals', 0), reverse=True)
    
    text = "🏆 **Skillclub Top 10 Leaders** 🏆\n\n"
    for i, (uid, data) in enumerate(sorted_users[:10], 1):
        text += f"{i}. {data.get('name', 'User')} — {data.get('referrals', 0)} Referrals\n"
    bot.send_message(message.chat.id, text, parse_mode="Markdown")

# AI कोचिंग (प्रॉम्प्ट बेस)
@bot.message_handler(func=lambda m: m.text == "🤖 Ask AI")
def ask_ai_intro(message):
    bot.reply_to(message, "अपना सवाल पूछने के लिए /ask_ai के बाद अपना प्रश्न लिखें।\nउदाहरण: `/ask_ai AI Influencer कैसे बनाएं?`", parse_mode="Markdown")

@bot.message_handler(commands=['ask_ai'])
def handle_ai_query(message):
    query = message.text.replace('/ask_ai', '').strip()
    if not query:
        bot.reply_to(message, "कृपया अपना सवाल लिखें।")
        return
    bot.reply_to(message, f"🤖 **Skillclub AI:**\n\nआपके सवाल '{query}' का विश्लेषण किया जा रहा है...")

# --- एडमिन कमांड्स ---

# पेमेंट कंफर्मेशन और इनवॉइसिंग
@bot.message_handler(commands=['confirm'])
def confirm_payment(message):
    if str(message.from_user.id) == ADMIN_ID:
        try:
            args = message.text.split()
            if len(args) < 3:
                bot.reply_to(message, "उपयोग: /confirm [user_id] [course_id]")
                return
            
            target_id, c_id = args[1], args[2]
            users = load_data()
            
            if target_id in users and c_id in COURSES:
                if c_id not in users[target_id]['purchased_courses']:
                    users[target_id]['purchased_courses'].append(c_id)
                    save_data(users)
                    send_invoice(target_id, c_id, COURSES[c_id]['price'])
                    bot.reply_to(message, f"✅ भुगतान सफल! यूजर {target_id} को इनवॉइस भेज दिया गया है।")
            else:
                bot.reply_to(message, "❌ यूजर या कोर्स आईडी गलत है।")
        except:
            bot.reply_to(message, "❌ कमांड फॉर्मेट गलत है।")

# ब्रॉडकास्ट फीचर
@bot.message_handler(commands=['broadcast'])
def broadcast(message):
    if str(message.from_user.id) == ADMIN_ID:
        text = message.text.replace('/broadcast', '').strip()
        if not text:
            bot.reply_to(message, "उपयोग: /broadcast [मैसेज]")
            return
        
        users = load_data()
        count = 0
        for uid in users.keys():
            try:
                bot.send_message(uid, text)
                count += 1
            except: continue
        bot.reply_to(message, f"✅ संदेश {count} यूजर्स को भेज दिया गया है।")

# 6. मुख्य लूप
if __name__ == "__main__":
    keep_alive()
    print("🚀 Skillclub Bot is Starting on Render...")
    while True:
        try:
            bot.polling(none_stop=True, interval=0, timeout=20)
        except Exception as e:
            print(f"❌ Error: {e}")
            time.sleep(10)
