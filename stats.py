import os
import psutil
import platform
import logging
import time
import sqlite3

logger = logging.getLogger("TgMusicBot")

# Bot start time record karne ke liye
BOT_START_TIME = time.time()

# Database setup for tracking global chats where bot is added
DB_FILE = "bot_chats.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chats (
            chat_id INTEGER PRIMARY KEY,
            chat_title TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

def add_chat_to_db(chat_id, chat_title="Unknown"):
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("OR IGNORE" if "OR" in "INSERT" else "INSERT OR IGNORE INTO chats (chat_id, chat_title) VALUES (?, ?)", (chat_id, chat_title))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"DB Insert Error: {e}")

def get_total_global_chats():
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM chats")
        count = cursor.fetchone()[0]
        conn.close()
        return count
    except Exception:
        return 0

def get_readable_time(seconds):
    count = 0
    ping_time = ""
    time_list = []
    time_suffix_list = ["s", "m", "h", "days"]
    while count < 4:
        count += 1
        remainder, result = divmod(seconds, 60) if count < 3 else divmod(seconds, 24)
        if count == 3:
            remainder, result = divmod(seconds, 24)
        if time_list and not result:
            seconds = remainder
            continue
        time_list.append(str(int(result)))
        seconds = remainder
    for x in range(len(time_list)):
        time_list[x] += time_suffix_list[x]
    if len(time_list) == 4:
        ping_time += time_list.pop() + " days, "
    time_list.reverse()
    ping_time += ":".join(time_list)
    return ping_time

def register_stats_module(client, events, QUEUES, VQUEUES):
    
    # Auto-track chats whenever bot receives any message or is added somewhere
    @client.on(events.NewMessage)
    async def track_chats(event):
        if event.is_group or event.is_channel:
            add_chat_to_db(event.chat_id, getattr(event.chat, 'title', 'Group/Channel'))

    @client.on(events.NewMessage(pattern=r"^/stats$"))
    async def stats_handler(event):
        msg = await event.reply("📊 **Fetching Global Telegram & System Stats...** ⚡")
        
        try:
            # 1. Telegram Global Tracked Chats Data
            total_global_chats = get_total_global_chats()
            if total_global_chats == 0 and event.is_group:
                # Fallback agar DB me abhi entry na hui ho
                total_global_chats = 1

            bot_me = await client.get_me()
            bot_name = bot_me.first_name
            bot_username = bot_me.username or "Self-Hosted Bot"
            
            # Uptime calculation
            uptime_seconds = int(time.time() - BOT_START_TIME)
            bot_uptime = get_readable_time(uptime_seconds)

            # 2. System Performance Stats (CPU, RAM, Disk via psutil)
            cpu_usage = psutil.cpu_percent(interval=0.5)
            ram = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            ram_total = round(ram.total / (1024.0 ** 3), 2)
            ram_used = round(ram.used / (1024.0 ** 3), 2)
            ram_percent = ram.percent
            
            disk_total = round(disk.total / (1024.0 ** 3), 2)
            disk_used = round(disk.used / (1024.0 ** 3), 2)
            disk_percent = disk.percent
            
            # 3. Active Streaming Queues Count
            active_audio = len([chat_id for chat_id, q in QUEUES.items() if q])
            active_video = len([chat_id for chat_id, q in VQUEUES.items() if q])
            total_active_vc = active_audio + active_video
            
            stats_text = (
                f"🔥 **MASTER BOT STATISTICS** 🔥\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"🤖 **Bot Name:** `{bot_name}`\n"
                f"🔗 **Username:** `@{bot_username}`\n"
                f"🌐 **Total Global Chats (Presence):** `{total_global_chats}`\n"
                f"⏱️ **Bot Uptime:** `{bot_uptime}`\n"
                f"🎵 **Active Audio Streams:** `{active_audio}`\n"
                f"🎬 **Active Video Streams:** `{active_video}`\n"
                f"🎙️ **Total Active Voice Chats:** `{total_active_vc}`\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"💻 **SYSTEM PERFORMANCE:**\n"
                f"🖥️ **CPU Usage:** `{cpu_usage}%`\n"
                f"🧠 **RAM Usage:** `{ram_used}GB / {ram_total}GB` (`{ram_percent}%`)\n"
                f"💾 **Hard Disk Usage:** `{disk_used}GB / {disk_total}GB` (`{disk_percent}%`)\n"
                f"⚙️ **Platform:** `{platform.system()} {platform.release()}`\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"⚡ **Powered by Master Music Bot**"
            )
            
            await msg.edit(stats_text)
        except Exception as e:
            logger.error(f"Stats error: {e}")
            await msg.edit(f"⚠️ Stats fetch karne me error aa gaya: `{str(e)}`")