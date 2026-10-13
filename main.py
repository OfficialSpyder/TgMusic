import os
import sys
import asyncio
import warnings
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telethon.tl.custom import Button
from pytgcalls import PyTgCalls
import logging

# --- PLAY, VPLAY, STATS, HELP & SPEEDTEST MODULES ---
from play import register_play_module, QUEUES
from vplay import register_vplay_module, VQUEUES
from stats import register_stats_module
from help import register_help_module
from speedtest import register_speedtest_module

# Ignore internal PyTgCalls unawaited coroutine warnings on exit
warnings.filterwarnings("ignore", category=RuntimeWarning)

# --- IMPORT CONFIG CREDENTIALS ---
from config import API_ID, API_HASH, BOT_TOKEN, STRING_SESSION

# --- START IMAGE CONFIG ---
START_IMG = "start.png"  # Ya koi bhi URL/path

# --- STREAM COMPATIBILITY (AUDIO & VIDEO PIPED) ---
try:
    from pytgcalls.types import AudioPiped, VideoPiped
except ImportError:
    try:
        from pytgcalls.types.input_stream import AudioPiped, VideoPiped
    except ImportError:
        try:
            from pytgcalls.types import MediaStream as AudioPiped
            from pytgcalls.types import MediaStream as VideoPiped
        except ImportError:
            from pytgcalls.types.input_stream import MediaStream as AudioPiped
            from pytgcalls.types.input_stream import MediaStream as VideoPiped

# Logging setup
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("TgMusicBot")

# Robust bypass function to forcefully remove bot from Voice Chat
async def force_leave_call(pytgcalls, chat_id):
    methods_to_try = [
        'leave_group_call', 
        'leave_current_call', 
        'leave_call', 
        'leave'
    ]
    for method in methods_to_try:
        if hasattr(pytgcalls, method):
            try:
                func = getattr(pytgcalls, method)
                await func(chat_id)
            except Exception:
                try:
                    await func()
                except Exception:
                    pass
    
    try:
        if hasattr(pytgcalls, 'reject_call'):
            await pytgcalls.reject_call(chat_id)
    except Exception:
        pass

async def main():
    logger.info("Initializing Dual-Client Setup (Userbot for VC & Bot Token for Messages)...")
    
    # 1. Userbot Client (StringSession) -> Isse PyTgCalls chalega aur Voice Chat join hogi
    userbot = TelegramClient(StringSession(STRING_SESSION), API_ID, API_HASH)
    pytgcalls = PyTgCalls(userbot)

    # 2. Bot Client (BOT_TOKEN) -> Isse BotFather wala bot messages aur thumbnails bheja karega
    bot = TelegramClient('bot_session', API_ID, API_HASH)
    await bot.start(bot_token=BOT_TOKEN)

    # --- REGISTER MODULES WITH BOT CLIENT & USERBOT CLIENT ---
    register_play_module(bot, events, pytgcalls, AudioPiped, userbot_client=userbot)
    register_vplay_module(bot, events, pytgcalls, VideoPiped, userbot_client=userbot)
    register_stats_module(bot, events, QUEUES, VQUEUES)
    register_help_module(bot)  # Registering Help Module from help.py
    register_speedtest_module(bot, events)  # Registering Speedtest Module from speedtest.py

    # --- INLINE BUTTONS CALLBACK QUERY HANDLER ---
    @bot.on(events.CallbackQuery)
    async def inline_button_handler(event):
        data = event.data.decode('utf-8')
        chat_id = event.chat_id
        
        if data == "pause":
            try:
                await pytgcalls.pause(chat_id)
                await event.answer("⏸️ Music Paused Successfully!", alert=False)
            except Exception as e:
                await event.answer(f"⚠️ Error: {str(e)}", alert=True)
                
        elif data == "resume":
            try:
                await pytgcalls.resume(chat_id)
                await event.answer("▶️ Music Resumed Successfully!", alert=False)
            except Exception as e:
                await event.answer(f"⚠️ Error: {str(e)}", alert=True)
                
        elif data == "skip":
            try:
                active_queue = None
                is_video = False
                
                if chat_id in QUEUES and len(QUEUES[chat_id]) > 0:
                    active_queue = QUEUES[chat_id]
                elif chat_id in VQUEUES and len(VQUEUES[chat_id]) > 0:
                    active_queue = VQUEUES[chat_id]
                    is_video = True
                    
                if active_queue and len(active_queue) > 0:
                    skipped_track = active_queue.pop(0)
                    try:
                        if os.path.exists(skipped_track['file_path']):
                            os.remove(skipped_track['file_path'])
                    except Exception:
                        pass
                    
                    if len(active_queue) > 0:
                        next_track = active_queue[0]
                        stream = VideoPiped(next_track['file_path']) if is_video else AudioPiped(next_track['file_path'])
                        await pytgcalls.play(chat_id, stream)
                        await event.answer(f"⏭️ Skipped! Now Playing: {next_track['title'][:20]}...", alert=False)
                    else:
                        if chat_id in QUEUES: QUEUES[chat_id].clear()
                        if chat_id in VQUEUES: VQUEUES[chat_id].clear()
                        await force_leave_call(pytgcalls, chat_id)
                        await event.answer("⏭️ Skipped! Queue is empty, left VC.", alert=False)
                else:
                    await event.answer("📭 Queue is empty!", alert=False)
            except Exception as e:
                await event.answer(f"⚠️ Skip Error: {str(e)}", alert=True)
                
        elif data == "stop":
            try:
                if chat_id in QUEUES: QUEUES[chat_id].clear()
                if chat_id in VQUEUES: VQUEUES[chat_id].clear()
                await force_leave_call(pytgcalls, chat_id)
                await event.answer("⏹️ Music Stopped & Left Voice Chat!", alert=False)
            except Exception as e:
                await event.answer(f"⚠️ Stop Error: {str(e)}", alert=True)
                
        elif data == "help_menu":
            help_text = (
                "📖 Master Bot Help Menu:\n\n"
                "Chose the category for which you wanna get help.\n"
                "All Commands Can Be Used With : `/`\n\n"
                "1️⃣ `/play [name]` - Stream Audio\n"
                "2️⃣ `/vplay [name]` - Stream Video\n"
                "3️⃣ `/stats` - Hardware & Bot Status\n"
                "4️⃣ `/speedtest` - Check Server Network Speed\n"
                "5️⃣ `/pause` / `/resume` - Control Playback\n"
                "6️⃣ `/skip` - Skip Current Song\n"
                "7️⃣ `/end` - Force Exit VC"
            )
            await event.answer("Opening Help Menu...", alert=False)
            await event.respond(help_text)

    # --- /start: Welcome Message with Custom Buttons & Image ---
    @bot.on(events.NewMessage(pattern=r"^/start$"))
    async def start_handler(event):
        bot_username = (await bot.get_me()).username
        
        welcome_text = (
            "> **This Music Player Has Been Launched By Master In 2026.**\n"
            "> **This Music Player Is Made With All Update Version Modules So That Telegram Users Do Not Face Any Problem.**\n\n"
            "**Credit ➱ AKM**"
        )
        
        buttons = [
            [Button.url("• ADD ME IN YOUR GROUP •", f"https://t.me/{bot_username}?startgroup=true")],
            [Button.inline("˹ HELP COMMANDS ˼", data="help_menu")],
            [
                Button.url("˹ UPDATES ˼", "https://t.me/Your_Official_Master"), 
                Button.url("˹ SUPPORT ˼", "https://t.me/Master_Support_GC")  
            ],
            [Button.url("Bot List", "https://t.me/+h51rWafNtFg2N2I1")] 
        ]
        
        try:
            if START_IMG and (os.path.exists(START_IMG) or START_IMG.startswith("http")):
                await event.reply(file=START_IMG, message=welcome_text, buttons=buttons, parse_mode='md')
            else:
                await event.reply(welcome_text, buttons=buttons, parse_mode='md')
        except Exception as e:
            logger.error(f"Failed to send start image: {e}")
            await event.reply(welcome_text, buttons=buttons, parse_mode='md')

    # --- /pause: PAUSE STREAM ---
    @bot.on(events.NewMessage(pattern=r"^/pause$"))
    async def pause_handler(event):
        try:
            await pytgcalls.pause(event.chat_id)
            await event.reply("⏸️ Stream Paused Successfully!")
        except Exception as e:
            await event.reply(f"⚠️ Pause Error: `{str(e)}`")

    # --- /resume: RESUME STREAM ---
    @bot.on(events.NewMessage(pattern=r"^/resume$"))
    async def resume_handler(event):
        try:
            await pytgcalls.resume(event.chat_id)
            await event.reply("▶️ Stream Resumed Successfully!")
        except Exception as e:
            await event.reply(f"⚠️ Resume Error: `{str(e)}`")

    # --- /skip: SKIP WITH NEXT TRACK TITLE DISPLAY ---
    @bot.on(events.NewMessage(pattern=r"^/skip$"))
    async def skip_handler(event):
        chat_id = event.chat_id
        active_queue = None
        is_video = False
        
        if chat_id in QUEUES and len(QUEUES[chat_id]) > 0:
            active_queue = QUEUES[chat_id]
        elif chat_id in VQUEUES and len(VQUEUES[chat_id]) > 0:
            active_queue = VQUEUES[chat_id]
            is_video = True
            
        if active_queue and len(active_queue) > 0:
            skipped_track = active_queue.pop(0)
            try:
                if os.path.exists(skipped_track['file_path']):
                    os.remove(skipped_track['file_path'])
            except Exception:
                pass
            
            if len(active_queue) > 0:
                next_track = active_queue[0]
                try:
                    stream = VideoPiped(next_track['file_path']) if is_video else AudioPiped(next_track['file_path'])
                    await pytgcalls.play(chat_id, stream)
                    
                    next_caption = (
                        f"⏭️ [SKIPPED & NOW PLAYING] ⏭️\n"
                        f"━━━━━━━━━━━━━━━━━━━━━━\n"
                        f"🎵 Track: {next_track['title']}\n"
                        f"⏱️ Duration: {next_track['duration']}\n"
                        f"━━━━━━━━━━━━━━━━━━━━━━"
                    )
                    if next_track.get('thumbnail'):
                        await bot.send_file(chat_id, next_track['thumbnail'], caption=next_caption)
                    else:
                        await bot.send_message(chat_id, next_caption)
                except Exception as e:
                    await event.reply(f"⚠️ Skip Playback Error: `{str(e)}`")
            else:
                if chat_id in QUEUES: QUEUES[chat_id].clear()
                if chat_id in VQUEUES: VQUEUES[chat_id].clear()
                await force_leave_call(pytgcalls, chat_id)
                await event.reply("⏭️ Track Skipped! Queue is empty, bot left the voice chat successfully!")
        else:
            if chat_id in QUEUES: QUEUES[chat_id].clear()
            if chat_id in VQUEUES: VQUEUES[chat_id].clear()
            await force_leave_call(pytgcalls, chat_id)
            await event.reply("📭 Queue empty thi, bot ne voice chat chhod diya hai!")

    # --- /stop & /end: FORCE REMOVE BOT FROM VC ---
    @bot.on(events.NewMessage(pattern=r"^/(stop|end)$"))
    async def stop_handler(event):
        chat_id = event.chat_id
        if chat_id in QUEUES: QUEUES[chat_id].clear()
        if chat_id in VQUEUES: VQUEUES[chat_id].clear()
        
        await force_leave_call(pytgcalls, chat_id)
        await event.reply("⏹️ Music Stopped & Bot Successfully Left VC!")

    # Start Userbot, PyTgCalls, and Bot Client together
    await userbot.start()
    await pytgcalls.start()
    logger.info("Bot started successfully with Dual-Client Architecture!")
    
    # Run both clients simultaneously
    await asyncio.gather(
        userbot.run_until_disconnected(),
        bot.run_until_disconnected()
    )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped gracefully by user.")