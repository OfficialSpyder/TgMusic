import os
import asyncio
import yt_dlp
from yt_dlp.utils import DownloadError

YTDL_AUDIO_OPTS = {
    'format': 'bestaudio/best',
    'geo_bypass': True,
    'nocheckcertificate': True,
    'quiet': True,
    'no_warnings': True,
    'extract_flat': False,
    'outtmpl': 'downloads/%(id)s.%(ext)s',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '192',
    }],
}

YTDL_VIDEO_OPTS = {
    'format': 'best[height<=720]/best',
    'geo_bypass': True,
    'nocheckcertificate': True,
    'quiet': True,
    'no_warnings': True,
    'outtmpl': 'downloads/%(id)s.%(ext)s',
}

os.makedirs('downloads', exist_ok=True)

async def download_audio(url_or_query):
    loop = asyncio.get_running_loop()
    def _download():
        with yt_dlp.YoutubeDL(YTDL_AUDIO_OPTS) as ydl:
            try:
                if not url_or_query.startswith("http"):
                    info = ydl.extract_info(f"ytsearch:{url_or_query}", download=True)['entries'][0]
                else:
                    info = ydl.extract_info(url_or_query, download=True)
                
                file_path = ydl.prepare_filename(info)
                base, _ = os.path.splitext(file_path)
                mp3_path = base + ".mp3"
                
                return {
                    'file_path': mp3_path if os.path.exists(mp3_path) else file_path,
                    'title': info.get('title', 'Unknown Title'),
                    'duration': info.get('duration_string', '3:00'),
                    'thumbnail': info.get('thumbnail', None),
                    'url': info.get('webpage_url', url_or_query)
                }
            except Exception as e:
                raise DownloadError(f"Download failed: {str(e)}")
    return await loop.run_in_executor(None, _download)

async def download_video(url_or_query):
    loop = asyncio.get_running_loop()
    def _download():
        with yt_dlp.YoutubeDL(YTDL_VIDEO_OPTS) as ydl:
            try:
                if not url_or_query.startswith("http"):
                    info = ydl.extract_info(f"ytsearch:{url_or_query}", download=True)['entries'][0]
                else:
                    info = ydl.extract_info(url_or_query, download=True)
                
                file_path = ydl.prepare_filename(info)
                return {
                    'file_path': file_path,
                    'title': info.get('title', 'Unknown Title'),
                    'duration': info.get('duration_string', '3:00'),
                    'thumbnail': info.get('thumbnail', None),
                    'url': info.get('webpage_url', url_or_query)
                }
            except Exception as e:
                raise DownloadError(f"Video Download failed: {str(e)}")
    return await loop.run_in_executor(None, _download)