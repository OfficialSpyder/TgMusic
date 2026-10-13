import logging
import time
import aiohttp

logger = logging.getLogger("TgMusicBot")

def register_speedtest_module(client, events):
    @client.on(events.NewMessage(pattern=r"^/speedtest$"))
    async def speedtest_handler(event):
        msg = await event.reply(
            "🚀 **Testing Server Bandwidth...**\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "⏳ *Measuring live connection speed from server...*"
        )
        
        start_time = time.time()
        
        try:
            # Cloudflare ka public test file use kar rahe hain (Fast & Accurate latency/speed check ke liye)
            test_url = "https://speed.cloudflare.com/__down?bytes=10000000" # ~10 MB file
            
            ping_start = time.time()
            async with aiohttp.ClientSession() as session:
                async with session.get(test_url) as response:
                    ping = round((time.time() - ping_start) * 1000, 2) # ms
                    
                    if response.status == 200:
                        download_start = time.time()
                        data = await response.read()
                        download_time = time.time() - download_start
                        
                        # Speed calculation in Mbps (Megabits per second)
                        file_size_bits = len(data) * 8
                        speed_bps = file_size_bits / download_time
                        download_speed = round(speed_bps / 1_000_000, 2)
                    else:
                        download_speed = 0.0
            
            elapsed_time = round(time.time() - start_time, 2)

            speed_text = (
                f"⚡ **MASTER BOT SPEEDTEST REPORT** ⚡\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"📥 **Server Download Speed:** `{download_speed} Mbps`\n"
                f"🏓 **Ping / Latency:** `{ping} ms`\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"⏱️ **Test Completed in:** `{elapsed_time}s`\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"🚀 **Powered by Master Music Bot**"
            )
            
            await msg.edit(speed_text)

        except Exception as e:
            logger.error(f"Speedtest error: {e}")
            await msg.edit(
                f"❌ **Speed Test Failed!**\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"⚠️ Error: `{str(e)}`"
            )