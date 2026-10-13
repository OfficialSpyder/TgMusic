# logger_helper.py
import logging
from config import LOGGER_ID

logger = logging.getLogger("TgMusicBot")

async def send_log(client, text, parse_mode='markdown'):
    """Bot ke sabhi events aur logs ko dedicated Log Group me bhejne ke liye"""
    if not LOGGER_ID:
        return
    try:
        await client.send_message(LOGGER_ID, text, parse_mode=parse_mode)
    except Exception as e:
        logger.error(f"Failed to send log to LOGGER_ID: {e}")