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
SALES_FILE = 'sales_log.json'
WD_FILE = 'withdrawals_log.json' 
ADMIN_UPI = "anand1312@fam" 

WELCOME_PHOTO = "https://files.catbox.moe/0v601y.png" 

# --- 2. डेटा मैनेजर (JSON Helpers) ---
def load_json(filename):
    if not os.path.exists(filename): return [] if "log" in filename else {}
    try:
        with open(filename, 'r') as f: return json.load(f)
    except: return [] if "log" in filename else {}

def save_json(filename, data):
    with open(filename, 'w') as f: json.dump(data, f, indent=4)

def log_transaction(filename, amount): # सेल और विड्रॉल रिकॉर्ड करने के लिए
    logs = load_json(filename)
    if not isinstance(logs, list): logs = []
    logs.append({
        "amount": amount,
        "date": time.strftime("%Y-%m-%d"),
        "month": time.strftime("%Y-%m")
    })
    save_json(filename, logs)

# --- 3. एडमिन स्टेट्स (आज, महीना और लाइफटाइम) ---
def get_stats():
    data = load_json(DB_FILE)
    sales = load_json(SALES_FILE)
    withdrawals = load_json(WD_FILE)
    
    today = time.strftime("%Y-%m-%d")
    this_month = time.strftime("%Y-%m")
    
    # सेल्स कैलकुलेशन (आज, महीना, लाइफटाइम)
    t_sell, m_sell, l_sell = 0, 0, 0
    if isinstance(sales, list):
        for s in sales:
            amt = s.get('amount', 0)
            l_sell += amt
            if s['date'] == today: t_sell += amt
            if s['month'] == this_month: m_sell += amt

    # विड्रॉल कैलकुलेशन (आज और लाइफटाइम)
    t_wd, l_wd = 0, 0
    if isinstance(withdrawals, list):
        for w in withdrawals:
            amt = w.get('amount', 0)
            l_wd += amt
            if w['date'] == today: t_wd += amt
            
    stats_text = (
        f"📊 <b>Skillclub Master Stats</b>\n\n"
        f"👥 <b>Total Users:</b> {len(data)}\n\n"
        f"💰 <b>Today's Sell:</b> ₹{t_sell}\n"
        f"📅 <b>Monthly Sell:</b> ₹{m_sell}\n"
        f"📈 <b>Lifetime Sell:</b> ₹{l_sell}\n\n"
        f"💸 <b>Today's Payout:</b> ₹{t_wd}\n"
        f"🏧 <b>Lifetime Payout:</b> ₹{l_wd}\n"
        f"────────────────────\n"
        f"✅ <b>Paid Users:</b> {sum(1 for u in data.values() if u.get('status') == 'Paid')}"
    )
    return stats_text

# --- 4. कॉलकैब हैंडलर ---
@bot.callback_query_handler(func=lambda call: True)
def callbacks(call):
    data, courses = load_json(DB_FILE), load_json(COURSE_DB)
    uid, action = str(call.message.chat.id), call.data.split('_', 1)[0]
    
    if action == "app":
        t_id, cid = call.data.split('_')[1], "_".join(call.data.split('_')[2:])
        if t_id in data and cid in courses:
            course = courses[cid]
            if cid not in data[t_id].get("purchased", []):
                log_transaction(SALES_FILE, course['price']) # सेल लॉग करें
                data[t_id].setdefault("purchased", []).append(cid)
                data[t_id]["status"] = "Paid"
                # कमीशन लॉजिक (L1 & L2)
                l1 = data[t_id].get("referred_by")
                if l1 and l1 in data:
                    data[l1]["balance"] += course.get("l1", 0)
                    data[l1]["referrals"] = data[l1].get("referrals", 0) + 1
                    l2 = data[l1].get("referred_by")
                    if l2 and l2 in data: data[l2]["balance"] += course.get("l2", 0)
            save_json(DB_FILE, data)
            bot.send_message(t_id, "🥳 <b>Approved!</b>", parse_mode="HTML")
            bot.edit_message_caption("✅ APPROVED", ADMIN_ID, call.message.message_id)

    elif action == "wdpay":
        t_id, amt = call.data.split('_')[1], int(call.data.split('_')[2])
        if t_id in data:
            log_transaction(WD_FILE, amt) # विड्रॉल लॉग करें
            data[t_id]["balance"] -= amt
            save_json(DB_FILE, data)
            bot.send_message(t_id, "🥳 <b>Payout Success!</b>", parse_mode="HTML")
            bot.edit_message_caption(f"✅ PAID ₹{amt}", ADMIN_ID, call.message.message_id)

# --- (Baaki Start, Menu, AddCourse functions wahi rahenge) ---

@bot.message_handler(func=lambda m: True)
def handle_menu(message):
    data, uid = load_json(DB_FILE), str(message.chat.id)
    if uid not in data: return
    text = message.text

    if text == "🛠 Admin Panel" and uid == ADMIN_ID:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("📊 Stats", "📢 Broadcast")
        markup.add("🔙 Back to Main Menu")
        bot.send_message(uid, "🛠 Admin Panel:", reply_markup=markup, parse_mode="HTML")
    elif text == "📊 Stats" and uid == ADMIN_ID:
        bot.send_message(uid, get_stats(), parse_mode="HTML")
    # ... बाकी बटन ...

if __name__ == "__main__":
    bot.polling(none_stop=True)
    
