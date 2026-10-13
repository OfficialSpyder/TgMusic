# from telethon import TelegramClient
# 
# # Apni API details yahan daal ya .env se load kar le
# API_ID = int(input("Apni API_ID daal: "))
# API_HASH = input("Apna API_HASH daal: ")
# 
# # Yahan hum 'assistant' naam ki .session file bana rahe hain
# session_name = "assistant"
# 
# print(f"\n[+] Connecting to Telegram to create '{session_name}.session' file...")
# client = TelegramClient(session_name, API_ID, API_HASH)
# 
# async def main():
#     await client.start()
#     me = await client.get_me()
#     print(f"\n[SUCCESS] Session file successfully created and verified!")
#     print(f"Logged in as: {me.first_name} (@{me.username})")
#     print(f"File saved as: {session_name}.session in your project folder.")
# 
# with client:
#     client.loop.run_until_complete(main())
    
    
    
from telethon.sync import TelegramClient
from telethon.sessions import StringSession

api_id = int(input("API_ID daal: "))
api_hash = input("API_HASH daal: ")

with TelegramClient(StringSession(), api_id, api_hash) as client:
    print("\nTERA STRING SESSION YE RAHA (Isse copy kar le):\n")
    print(client.session.save())
    print("\n--------------------------------------------------")