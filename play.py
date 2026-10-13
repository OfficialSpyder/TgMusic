import os
import asyncio
import urllib.request
from yt_dlp import YoutubeDL
from telethon import Button, events
from telethon.tl.functions.messages import AddChatUserRequest
from telethon.tl.functions.channels import InviteToChannelRequest
import logging

# Config se LOGGER_ID import karein (agar config me define na ho toh None rahega)
try:
    from config import LOGGER_ID
except ImportError:
    LOGGER_ID = None

logger = logging.getLogger("TgMusicBot")

QUEUES = {}
AUDIO_DIR = "storage/audio"
os.makedirs(AUDIO_DIR, exist_ok=True)

# -------------------------------------------------------------------------
# GLOBAL LOGGER HELPER
# -------------------------------------------------------------------------
async def send_log(client, text, parse_mode='markdown'):
    """Bot ke sabhi events aur logs ko dedicated Log Group me bhejne ke liye"""
    if not LOGGER_ID:
        return
    try:
        await client.send_message(LOGGER_ID, text, parse_mode=parse_mode)
    except Exception as e:
        logger.error(f"Failed to send log to LOGGER_ID: {e}")

# -------------------------------------------------------------------------
# HELPER: GET CHAT LINK / USERNAME
# -------------------------------------------------------------------------
async def get_chat_link_info(chat):
    """Group/Channel ka public link ya username/id nikalne ke liye"""
    if not chat:
        return "Private/DM", "N/A"
    
    title = getattr(chat, 'title', 'Private Chat')
    username = getattr(chat, 'username', None)
    
    if username:
        link = f"https://t.me/{username}"
        identifier = f"@{username}"
    else:
        # Private group/channel ke liye link nahi hota, toh ID ya invite check hota hai
        chat_id = getattr(chat, 'id', 'Unknown')
        link = f"Private Chat / ID: `{chat_id}`"
        identifier = f"ID: `{chat_id}`"
        
    return title, link, identifier

# -------------------------------------------------------------------------
# BOT ADMIN STATUS CHECKER (Startup Report)
# -------------------------------------------------------------------------
async def check_bot_admin_status(client):
    """Bot start hote hi check karega ki wo kin groups me admin hai aur kin me nahi"""
    if not LOGGER_ID:
        return
    
    log_text = "🤖 **Bot Startup & Admin Status Report**\n━━━━━━━━━━━━━━━━━━━━━━\n"
    count = 0
    
    try:
        async for dialog in client.iter_dialogs():
            if dialog.is_group or dialog.is_channel:
                chat_title, chat_link, _ = await get_chat_link_info(dialog.entity)
                chat_id = dialog.id
                try:
                    me = await client.get_me()
                    permissions = await client.get_permissions(chat_id, me.id)
                    is_admin = permissions.is_admin if hasattr(permissions, 'is_admin') else False
                    
                    if is_admin:
                        log_text += f"✅ **{chat_title}** ([Link]({chat_link})): `Admin`\n"
                    else:
                        log_text += f"⚠️ **{chat_title}** ([Link]({chat_link})): `Not Admin`\n"
                except Exception:
                    log_text += f"❌ **{chat_title}** (`{chat_id}`): `Permission Check Failed`\n"
                
                count += 1
                if count >= 25:
                    await send_log(client, log_text, parse_mode='markdown')
                    log_text = "━━━━━━━━━━━━━━━━━━━━━━ (Continuation)\n"
                    count = 0
                    
        if log_text != "🤖 **Bot Startup & Admin Status Report**\n━━━━━━━━━━━━━━━━━━━━━━\n":
            await send_log(client, log_text, parse_mode='markdown')
    except Exception as e:
        logger.error(f"Error in check_bot_admin_status: {e}")

# -------------------------------------------------------------------------
# SMART DOWNLOAD MODULE
# -------------------------------------------------------------------------
def download_audio_smart(query):
    ydl_opts_info = {'noplaylist': True, 'quiet': True, 'default_search': 'ytsearch', 'nocheckcertificate': True}
    with YoutubeDL(ydl_opts_info) as ydl:
        try:
            info = ydl.extract_info(query, download=False)
            if 'entries' in info:
                entries = [e for e in info['entries'] if e]
                if not entries:
                    return None
                info = entries[0]
            
            audio_id = info.get('id')
        except Exception as e:
            logger.error(f"Metadata extract error: {e}")
            audio_id = None

    if audio_id:
        file_path = os.path.join(AUDIO_DIR, f"{audio_id}.m4a")
        thumb_path = os.path.join(AUDIO_DIR, f"{audio_id}.jpg")
        
        if os.path.exists(file_path):
            return {
                'file_path': file_path,
                'title': info.get('title', 'Unknown Title'),
                'duration': info.get('duration_string', '0:00'),
                'thumbnail': thumb_path if os.path.exists(thumb_path) else None,
                'uploader': info.get('uploader', 'Unknown Artist'),
                'url': info.get('webpage_url', f"https://youtube.com/watch?v={audio_id}")
            }

    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'm4a',
            'preferredquality': '192',
        }],
        'outtmpl': os.path.join(AUDIO_DIR, '%(id)s.%(ext)s'),
        'noplaylist': True,
        'nocheckcertificate': True,
        'ignoreerrors': True,
        'quiet': True,
        'no_warnings': True,
        'default_search': 'ytsearch',
        'extractor_args': {
            'youtube': {
                'player_client': ['android', 'web']
            }
        }
    }

    with YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(query, download=True)
            if not info:
                return None
            if 'entries' in info:
                entries = [e for e in info['entries'] if e]
                if not entries:
                    return None
                info = entries[0]
            
            audio_id = info.get('id')
            file_path = os.path.join(AUDIO_DIR, f"{audio_id}.m4a")
            if not os.path.exists(file_path):
                for f in os.listdir(AUDIO_DIR):
                    if f.startswith(audio_id) and f.endswith('.m4a'):
                        file_path = os.path.join(AUDIO_DIR, f)
                        break
            
            thumb_url = info.get('thumbnail')
            thumb_path = os.path.join(AUDIO_DIR, f"{audio_id}.jpg")
            if thumb_url and not os.path.exists(thumb_path):
                try:
                    urllib.request.urlretrieve(thumb_url, thumb_path)
                except Exception:
                    thumb_path = None

            return {
                'file_path': file_path,
                'title': info.get('title', 'Unknown Title'),
                'duration': info.get('duration_string', '0:00'),
                'thumbnail': thumb_path if os.path.exists(thumb_path) else None,
                'uploader': info.get('uploader', 'Unknown Artist'),
                'url': info.get('webpage_url', f"https://youtube.com/watch?v={audio_id}")
            }
        except Exception as e:
            logger.error(f"Audio download error: {e}")
            return None

async def background_userbot_join(client, userbot_client, chat_id, is_group, is_channel):
    if not userbot_client:
        return
    try:
        me = await userbot_client.get_me()
        await userbot_client.get_permissions(chat_id, me.id)
    except Exception:
        try:
            me = await userbot_client.get_me()
            if is_group:
                await client(AddChatUserRequest(chat_id=chat_id, user_id=me.id, fwd_limit=100))
            elif is_channel:
                await client(InviteToChannelRequest(channel=chat_id, users=[me.id]))
        except Exception as add_err:
            logger.error(f"Background auto-join error: {add_err}")

async def play_next_audio(client, chat_id, pytgcalls, AudioPiped):
    if chat_id in QUEUES and len(QUEUES[chat_id]) > 0:
        QUEUES[chat_id].pop(0)
    
    if chat_id in QUEUES and len(QUEUES[chat_id]) > 0:
        next_track = QUEUES[chat_id][0]
        try:
            stream = AudioPiped(next_track['file_path'])
            await pytgcalls.play(chat_id, stream)
            
            caption = (
                f"🎵 **Master Music Pro** ♪ (Now Playing)\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"🎶 Title: {next_track['title']}\n"
                f"👤 Singer: {next_track['uploader']}\n"
                f"⏱️ Duration: {next_track['duration']}\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"⚡ Status: `Streaming from Local Storage...`"
            )
            buttons = [
                [Button.inline("⏸ Pause", data="pause"), Button.inline("▶️ Resume", data="resume")],
                [Button.inline("⏭ Skip", data="skip"), Button.inline("⏹ Stop", data="stop")]
            ]
            if next_track.get('thumbnail') and os.path.exists(next_track['thumbnail']):
                await client.send_file(chat_id, next_track['thumbnail'], caption=caption, parse_mode='html', buttons=buttons)
            else:
                await client.send_message(chat_id, caption, parse_mode='html', buttons=buttons)
        except Exception as e:
            logger.error(f"Next track play error: {e}")
            await play_next_audio(client, chat_id, pytgcalls, AudioPiped)
    else:
        await asyncio.sleep(5)
        if chat_id in QUEUES:
            del QUEUES[chat_id]
        try:
            await pytgcalls.leave_call(chat_id)
            await client.send_message(chat_id, "🔌 **Audio Queue is empty!** Saved files kept securely in storage, userbot left VC.")
        except Exception as e:
            logger.error(f"Auto leave error: {e}")


def register_play_module(client, events, pytgcalls, AudioPiped, userbot_client=None):
    
    asyncio.create_task(check_bot_admin_status(client))

    @pytgcalls.on_update()
    async def track_end_handler(client_call, update):
        from pytgcalls.types import StreamEnded
        if isinstance(update, StreamEnded):
            chat_id = update.chat_id
            await play_next_audio(client, chat_id, pytgcalls, AudioPiped)

    # -------------------------------------------------------------------------
    # CHAT ACTIONS LOGS HANDLER
    # -------------------------------------------------------------------------
    @client.on(events.ChatAction)
    async def chat_action_handler(event):
        chat = event.chat
        chat_title, chat_link, _ = await get_chat_link_info(chat)
        chat_id = event.chat_id
        
        try:
            me = await client.get_me()
            if event.user_joined or event.added_to:
                if (event.added_by and event.added_by.id == me.id) or (event.user_joined and event.user_id == me.id):
                    await send_log(client, f"🚀 **Bot Added to New Group!**\n🏷️ Group: {chat_title}\n🔗 Link: {chat_link}\n🆔 ID: `{chat_id}`", parse_mode='markdown')
            elif event.user_left or event.kicked:
                if event.user_id == me.id or event.kicked:
                    await send_log(client, f"⚠️ **Bot Removed / Banned from Group!**\n🏷️ Group: {chat_title}\n🔗 Link: {chat_link}\n🆔 ID: `{chat_id}`", parse_mode='markdown')
        except Exception as e:
            logger.error(f"ChatAction log error: {e}")

    # -------------------------------------------------------------------------
    # PLAY HANDLER WITH COMPREHENSIVE LOGGING
    # -------------------------------------------------------------------------
    @client.on(events.NewMessage(pattern=r"^/play (.+)"))
    async def play_handler(event):
        chat_id = event.chat_id
        is_private = event.is_private
        chat = event.chat
        chat_title, chat_link, _ = await get_chat_link_info(chat)
        query = event.pattern_match.group(1)
        
        try:
            sender = await event.get_sender()
            sender_name = sender.first_name if sender and hasattr(sender, 'first_name') else "User"
            sender_username = f"@{sender.username}" if sender and hasattr(sender, 'username') and sender.username else "No Username"
            sender_id = sender.id if sender else event.sender_id
            user_link = f"<a href='tg://user?id={sender_id}'>{sender_name}</a>"
        except Exception:
            sender_name = "User"
            sender_username = "No Username"
            sender_id = event.sender_id
            user_link = "User"

        # Log details with username and chat link
        log_type = "👤 **DM Play Request**" if is_private else "👥 **Group Play Request**"
        log_msg = (
            f"{log_type}\n"
            f"👤 User: {sender_name} ({sender_username}) (`{sender_id}`)\n"
            f"💬 Chat: {chat_title}\n"
            f"🔗 Chat Link/ID: {chat_link} (`{chat_id}`)\n"
            f"🎵 Query: `{query}`"
        )
        await send_log(client, log_msg, parse_mode='markdown')

        if chat_id in QUEUES and len(QUEUES[chat_id]) >= 100:
            return await event.reply("❌ Queue limit reached! Maximum 100 songs allowed.")

        asyncio.create_task(background_userbot_join(client, userbot_client, chat_id, event.is_group, event.is_channel))
        msg = await event.reply("⚡ **Checking Local Storage & Streaming...** 🚀")
        
        loop = asyncio.get_running_loop()
        track = await loop.run_in_executor(None, download_audio_smart, query)
        
        if not track or not track.get('file_path') or not os.path.exists(track['file_path']):
            return await msg.edit("❌ Gaana process nahi ho paya, dobara try karein!")

        if chat_id not in QUEUES:
            QUEUES[chat_id] = []

        QUEUES[chat_id].append(track)
        await msg.delete()

        caption = (
            f"🎵 **Master Music Pro** ♪\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🎶 Title: {track['title']}\n"
            f"👤 Singer: {track['uploader']}\n"
            f"⏱️ Duration: {track['duration']}\n"
            f"👤 Requested By: {user_link}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"⚡ Status: `Playing from Local Storage Cache...`"
        )

        buttons = [
            [Button.inline("⏸ Pause", data="pause"), Button.inline("▶️ Resume", data="resume")],
            [Button.inline("⏭ Skip", data="skip"), Button.inline("⏹ Stop", data="stop")]
        ]

        if len(QUEUES[chat_id]) == 1:
            try:
                stream = AudioPiped(track['file_path'])
                await pytgcalls.play(chat_id, stream)
                
                if track.get('thumbnail') and os.path.exists(track['thumbnail']):
                    await client.send_file(chat_id, track['thumbnail'], caption=caption, parse_mode='html', buttons=buttons)
                else:
                    await client.send_message(chat_id, caption, parse_mode='html', buttons=buttons)
            except Exception as e:
                QUEUES[chat_id].pop(0)
                await event.reply(f"⚠️ Playback Error: `{str(e)}`")
        else:
            position = len(QUEUES[chat_id]) - 1
            queue_caption = (
                f"➕ **[ADDED TO AUDIO QUEUE #{position}]**\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"🎵 Title: {track['title']}\n"
                f"👤 Singer: {track['uploader']}\n"
                f"⏱️ Duration: {track['duration']}\n"
                f"👤 Requested By: {user_link}\n"
                f"━━━━━━━━━━━━━━━━━━━━━━"
            )
            if track.get('thumbnail') and os.path.exists(track['thumbnail']):
                await client.send_file(chat_id, track['thumbnail'], caption=queue_caption, parse_mode='html')
            else:
                await client.send_message(chat_id, queue_caption, parse_mode='html')