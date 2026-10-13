import re
from telethon import events
from telethon.tl.custom import Button

def register_help_module(bot):
    
    # --- /help Command Handler ---
    @bot.on(events.NewMessage(pattern=r"^/help$"))
    async def help_command_handler(event):
        help_text = (
            "📖 Master Bot Help Menu\n\n"
            "Chose the category for which you wanna get help.\n"
            "All Commands Can Be Used With : `/`\n\n"
            "💎 Working Commands:\n"
            "• `/play [Song Name]` - Stream Audio with Thumbnail\n"
            "• `/vplay [Video Name]` - Stream HD Video with Thumbnail\n"
            "• `/stats` - Check Hardware & System Status\n"
            "• `/pause` - Pause Current Stream\n"
            "• `/resume` - Resume Stream\n"
            "• `/skip` - Skip Track & Play Next\n"
            "• `/stop` or `/end` - Stop & Leave VC"
        )
        
        buttons = [
            [
                Button.inline("Play", data="help_play"),
                Button.inline("Stats", data="help_stats")
            ],
            [
                Button.inline("Control", data="help_control"),
                Button.inline("Close", data="help_close")
            ]
        ]
        
        await event.reply(help_text, buttons=buttons)

    # --- Help Menu Inline Callbacks ---
    @bot.on(events.CallbackQuery(data=re.compile(b"^help_")))
    async def help_callback_handler(event):
        data = event.data.decode('utf-8')
        
        if data == "help_play":
            await event.answer(
                "🎵 Play Commands:\n- /play [name]\n- /vplay [name]", 
                alert=True
            )
        elif data == "help_stats":
            await event.answer(
                "📊 Stats Command:\n- /stats (Shows CPU, RAM, Disk & Streams)", 
                alert=True
            )
        elif data == "help_control":
            await event.answer(
                "⚙️ Control Commands:\n- /pause, /resume\n- /skip, /stop, /end", 
                alert=True
            )
        elif data == "help_close":
            await event.delete()