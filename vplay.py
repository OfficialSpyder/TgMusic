import os
import asyncio
import urllib.request
from yt_dlp import YoutubeDL
from telethon import Button, events
from telethon.tl.functions.messages import AddChatUserRequest
from telethon.tl.functions.channels import InviteToChannelRequest
import logging

# Config se LOGGER_ID import karein
try:
    from config import LOGGER_ID
except ImportError:
    LOGGER_ID = None

logger = logging.getLogger("TgMusicBot")

VQUEUES = {}
VIDEO_DIR = "storage/videos"
os.makedirs(VIDEO_DIR, exist_ok=True)

# -------------------------------------------------------------------------
# GLOBAL LOGGER HELPER
# -------------------------------------------------------------------------
async def send_log(client, text, parse_mode='markdown'):
    """Bot ke sabhi video events aur logs ko dedicated Log Group me bhejne ke liye"""
    if not LOGGER_ID:
        return
    try:
        await client.send_message(LOGGER_ID, text, parse_mode=parse_mode)
    except Exception as e:
        logger.error(f"Failed to send log to LOGGER_ID in vplay: {e}")

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
        chat_id = getattr(chat, 'id', 'Unknown')
        link = f"Private Chat / ID: `{chat_id}`"
        identifier = f"ID: `{chat_id}`"
        
    return title, link, identifier

def download_video_smart(query):
    ydl_opts_info = {'noplaylist': True, 'quiet': True, 'default_search': 'ytsearch', 'nocheckcertificate': True}
    with YoutubeDL(ydl_opts_info) as ydl:
        try:
            info = ydl.extract_info(query, download=False)
            if 'entries' in info:
                entries = [e for e in info['entries'] if e]
                if not entries:
                    return None
                info = entries[0]
            
            video_id = info.get('id')
        except Exception as e:
            logger.error(f"Video metadata extract error: {e}")
            video_id = None

    if video_id:
        file_path = os.path.join(VIDEO_DIR, f"{video_id}.mp4")
        thumb_path = os.path.join(VIDEO_DIR, f"{video_id}.jpg")
        
        if os.path.exists(file_path):
            return {
                'file_path': file_path,
                'title': info.get('title', 'Unknown Title'),
                'duration': info.get('duration_string', '0:00'),
                'thumbnail': thumb_path if os.path.exists(thumb_path) else None,
                'uploader': info.get('uploader', 'Unknown Channel'),
                'url': info.get('webpage_url', f"https://youtube.com/watch?v={video_id}")
            }

    ydl_opts = {
        'format': 'bestvideo[height<=720]+bestaudio/best[height<=720]',
        'merge_output_format': 'mp4',
        'outtmpl': os.path.join(VIDEO_DIR, '%(id)s.%(ext)s'),
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
            
            video_id = info.get('id')
            file_path = os.path.join(VIDEO_DIR, f"{video_id}.mp4")
            if not os.path.exists(file_path):
                for f in os.listdir(VIDEO_DIR):
                    if f.startswith(video_id) and f.endswith('.mp4'):
                        file_path = os.path.join(VIDEO_DIR, f)
                        break
            
            thumb_url = info.get('thumbnail')
            thumb_path = os.path.join(VIDEO_DIR, f"{video_id}.jpg")
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
                'uploader': info.get('uploader', 'Unknown Channel'),
                'url': info.get('webpage_url', f"https://youtube.com/watch?v={video_id}")
            }
        except Exception as e:
            logger.error(f"Video download error: {e}")
            return None

async def background_userbot_join_video(client, userbot_client, chat_id, is_group, is_channel):
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
            logger.error(f"Background auto-join vplay error: {add_err}")

async def play_next_video(client, chat_id, pytgcalls, VideoPiped):
    if chat_id in VQUEUES and len(VQUEUES[chat_id]) > 0:
        VQUEUES[chat_id].pop(0)
    
    if chat_id in VQUEUES and len(VQUEUES[chat_id]) > 0:
        next_track = VQUEUES[chat_id][0]
        try:
            stream = VideoPiped(next_track['file_path'])
            await pytgcalls.play(chat_id, stream)
            
            caption = (
                f"🎬 **Master Video Pro** ♪ (Now Playing)\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"🎥 Title: {next_track['title']}\n"
                f"👤 Channel: {next_track['uploader']}\n"
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
            logger.error(f"Next video play error: {e}")
            await play_next_video(client, chat_id, pytgcalls, VideoPiped)
    else:
        await asyncio.sleep(5)
        if chat_id in VQUEUES:
            del VQUEUES[chat_id]
        try:
            await pytgcalls.leave_call(chat_id)
            await client.send_message(chat_id, "🔌 **Video Queue is empty!** Files securely stored in folder, userbot left VC.")
        except Exception as e:
            logger.error(f"Auto leave vplay error: {e}")

def register_vplay_module(client, events, pytgcalls, VideoPiped, userbot_client=None):
    @pytgcalls.on_update()
    async def video_end_handler(client_call, update):
        from pytgcalls.types import StreamEnded
        if isinstance(update, StreamEnded):
            chat_id = update.chat_id
            await play_next_video(client, chat_id, pytgcalls, VideoPiped)

    # -------------------------------------------------------------------------
    # CHAT ACTIONS LOGS HANDLER
    # -------------------------------------------------------------------------
    @client.on(events.ChatAction)
    async def chat_action_handler_video(event):
        chat = event.chat
        chat_title, chat_link, _ = await get_chat_link_info(chat)
        chat_id = event.chat_id
        
        try:
            me = await client.get_me()
            if event.user_joined or event.added_to:
                if (event.added_by and event.added_by.id == me.id) or (event.user_joined and event.user_id == me.id):
                    await send_log(client, f"🚀 **Bot Added to New Group (Video Module)!**\n🏷️ Group: {chat_title}\n🔗 Link: {chat_link}\n🆔 ID: `{chat_id}`", parse_mode='markdown')
            elif event.user_left or event.kicked:
                if event.user_id == me.id or event.kicked:
                    await send_log(client, f"⚠️ **Bot Removed / Banned from Group (Video Module)!**\n🏷️ Group: {chat_title}\n🔗 Link: {chat_link}\n🆔 ID: `{chat_id}`", parse_mode='markdown')
        except Exception as e:
            logger.error(f"ChatAction video log error: {e}")

    # -------------------------------------------------------------------------
    # VPLAY HANDLER WITH LOGGING
    # -------------------------------------------------------------------------
    @client.on(events.NewMessage(pattern=r"^/vplay (.+)"))
    async def vplay_handler(event):
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
        log_type = "👤 **DM Video Play Request**" if is_private else "👥 **Group Video Play Request**"
        log_msg = (
            f"{log_type}\n"
            f"👤 User: {sender_name} ({sender_username}) (`{sender_id}`)\n"
            f"💬 Chat: {chat_title}\n"
            f"🔗 Chat Link/ID: {chat_link} (`{chat_id}`)\n"
            f"🎥 Query: `{query}`"
        )
        await send_log(client, log_msg, parse_mode='markdown')

        if chat_id in VQUEUES and len(VQUEUES[chat_id]) >= 100:
            return await event.reply("❌ Queue limit reached! Maximum 100 videos allowed.")

        asyncio.create_task(background_userbot_join_video(client, userbot_client, chat_id, event.is_group, event.is_channel))
        msg = await event.reply("🚀 **Checking Local Storage & Loading Video...** 🎬")
        
        loop = asyncio.get_running_loop()
        track = await loop.run_in_executor(None, download_video_smart, query)
        
        if not track or not track.get('file_path') or not os.path.exists(track['file_path']):
            return await msg.edit("❌ Video process nahi ho paya, link check karein!")

        if chat_id not in VQUEUES:
            VQUEUES[chat_id] = []

        VQUEUES[chat_id].append(track)
        await msg.delete()

        caption = (
            f"🎬 **Master Video Pro** ♪\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🎥 Title: {track['title']}\n"
            f"👤 Channel: {track['uploader']}\n"
            f"⏱️ Duration: {track['duration']}\n"
            f"👤 Requested By: {user_link}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"⚡ Status: `Playing from Local Storage Cache...`"
        )

        buttons = [
            [Button.inline("⏸ Pause", data="pause"), Button.inline("▶️ Resume", data="resume")],
            [Button.inline("⏭ Skip", data="skip"), Button.inline("⏹ Stop", data="stop")]
        ]

        if len(VQUEUES[chat_id]) == 1:
            try:
                stream = VideoPiped(track['file_path'])
                await pytgcalls.play(chat_id, stream)
                
                if track.get('thumbnail') and os.path.exists(track['thumbnail']):
                    await client.send_file(chat_id, track['thumbnail'], caption=caption, parse_mode='html', buttons=buttons)
                else:
                    await client.send_message(chat_id, caption, parse_mode='html', buttons=buttons)
            except Exception as e:
                VQUEUES[chat_id].pop(0)
                await event.reply(f"⚠️ Video Playback Error: `{str(e)}`")
        else:
            position = len(VQUEUES[chat_id]) - 1
            queue_caption = (
                f"➕ **[ADDED VIDEO TO QUEUE #{position}]**\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"🎥 Title: {track['title']}\n"
                f"👤 Channel: {track['uploader']}\n"
                f"⏱️ Duration: {track['duration']}\n"
                f"👤 Requested By: {user_link}\n"
                f"━━━━━━━━━━━━━━━━━━━━━━"
            )
            if track.get('thumbnail') and os.path.exists(track['thumbnail']):
                await client.send_file(track['thumbnail'], caption=queue_caption, parse_mode='html')
            else:
                await client.send_message(track['chat_id'] if 'chat_id' in locals() else chat_id, queue_caption, parse_mode='html')