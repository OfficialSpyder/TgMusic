import sys
import asyncio
from pyrogram import errors
from pyrogram.raw.functions import phone
from pyrogram.raw import types
from pytgcalls import PyTgCalls
from yt_dlp import YoutubeDL
from bot_logger import logger

# --- COMPATIBILITY IMPORTS FOR AUDIOPIPED / VIDEOPIPED ---
try:
    from pytgcalls.types import AudioPiped, VideoPiped
except ImportError:
    try:
        from pytgcalls.types.input_stream import AudioPiped, VideoPiped
    except ImportError:
        try:
            from pytgcalls.types import MediaStream as AudioPiped
            VideoPiped = AudioPiped
        except ImportError:
            AudioPiped = None
            VideoPiped = None

# --- ULTIMATE PYROGRAM & PYTGCALLS COMPATIBILITY PATCH ---
class DummyClass:
    def __init__(self, *args, **kwargs):
        pass
    def __getattr__(self, name):
        return DummyClass()

class DynamicTypesModule:
    def __getattr__(self, name):
        if not hasattr(types, name):
            dummy = DummyClass()
            setattr(types, name, dummy)
            return dummy
        return getattr(types, name)

sys.modules['pyrogram.raw.types'] = DynamicTypesModule()

for err_name in ['GroupcallForbidden', 'GroupcallInvalid', 'GroupcallNotJoined', 'NotJoined']:
    if not hasattr(errors, err_name):
        class DummyError(Exception):
            pass
        setattr(errors, err_name, DummyError)
        sys.modules['pyrogram.errors'].__dict__[err_name] = DummyError

for func_name in [
    'CreateConferenceCall', 'GetGroupCallChainBlocks', 'JoinGroupCall', 
    'LeaveGroupCall', 'InviteConferenceCallParticipant', 'SendConferenceCallBroadcast'
]:
    if not hasattr(phone, func_name):
        setattr(phone, func_name, DummyClass)
        sys.modules['pyrogram.raw.functions.phone'].__dict__[func_name] = DummyClass
# ---------------------------------------------------------

class MusicPlayer:
    def __init__(self, client):
        self.pytgcalls = PyTgCalls(client)
        self.queues = {}
        # yt-dlp options for universal search and direct streaming links
        self.ytdl_opts = {
            'format': 'bestaudio/best',
            'noplaylist': True,
            'nocheckcertificate': True,
            'ignoreerrors': True,
            'logtostderr': False,
            'quiet': True,
            'no_warnings': True,
            'default_search': 'ytsearch',
            'source_address': '0.0.0.0',
        }

    async def start(self):
        await self.pytgcalls.start()
        logger.info("PyTgCalls client started successfully.")

    async def get_stream_url(self, query: str):
        logger.info(f"Searching and extracting stream for query: {query}")
        loop = asyncio.get_event_loop()
        
        def extract():
            with YoutubeDL(self.ytdl_opts) as ydl:
                try:
                    info = ydl.extract_info(query, download=False)
                    if 'entries' in info:
                        # Grab the first result if it's a search query
                        info = info['entries'][0]
                    
                    return {
                        'url': info.get('url'),
                        'title': info.get('title', 'Unknown Title'),
                        'duration': info.get('duration', 0),
                        'is_video': True if info.get('vcodec') != 'none' else False
                    }
                except Exception as e:
                    logger.error(f"YTDL Extraction Error for '{query}': {str(e)}")
                    return None

        return await loop.run_in_executor(None, extract)

    async def add_to_queue(self, chat_id: int, track: dict):
        if chat_id not in self.queues:
            self.queues[chat_id] = []
        self.queues[chat_id].append(track)
        logger.info(f"Added to queue for chat {chat_id}: {track['title']}")

    async def play_next(self, chat_id: int):
        if chat_id in self.queues and len(self.queues[chat_id]) > 0:
            track = self.queues[chat_id].pop(0)
            url = track['url']
            
            try:
                if AudioPiped is None:
                    await self.pytgcalls.join_group_call(chat_id, url)
                else:
                    stream = VideoPiped(url) if track['is_video'] else AudioPiped(url)
                    await self.pytgcalls.join_group_call(chat_id, stream)
                
                logger.info(f"Now playing in chat {chat_id}: {track['title']}")
                return track
            except Exception as e:
                logger.error(f"Playback error in chat {chat_id}: {str(e)}")
                return await self.play_next(chat_id)
        else:
            try:
                await self.pytgcalls.leave_group_call(chat_id)
                logger.info(f"Queue empty. Left voice call in chat {chat_id}.")
            except Exception as e:
                logger.warning(f"Error leaving group call: {str(e)}")
            return None