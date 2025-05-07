from telethon import TelegramClient, events
import re
import traceback
import time
import hashlib
import nest_asyncio
import asyncio

nest_asyncio.apply()

# --- Konfigurasi API Telegram ---
api_id = 28420040
api_hash = '818defcc6440540407fb080f93ff5626'

# --- Grup sumber & target ---
SOURCE_CHAT = -1002214581326
TARGET_CHAT = 'soberfilter'

# --- Inisialisasi Telethon ---
client = TelegramClient('sober-session', api_id, api_hash)

# --- Regex Contract Address (CA) ---
ca_regex = re.compile(r'\b[A-HJ-NP-Za-km-z1-9]{32,60}\b')
q_param_regex = re.compile(r'[?&]q=([A-HJ-NP-Za-km-z1-9]{32,60})')

# --- Cache anti-duplikat ---
message_cache = {}

@client.on(events.NewMessage(chats=SOURCE_CHAT))
async def handler(event):
    try:
        original_message = event.message.message or ''
        if not re.search(r'\b3 smart money bought\b', original_message.lower()):
            print("⏭️ Skip (bukan trigger)")
            return

        # Hash pesan untuk deteksi duplikat
        message_hash = hashlib.md5(original_message.encode('utf-8')).hexdigest()
        now = time.time()

        if message_hash in message_cache and (now - message_cache[message_hash]) < 60:
            print("⏱️ Duplikat < 1 menit — skip")
            return
        else:
            message_cache[message_hash] = now

        # Cari CA
        cas = set()
        cas.update(ca_regex.findall(original_message))
        cas.update(q_param_regex.findall(original_message))

        # Cek URL jika ada entity
        if event.message.entities:
            for ent in event.message.entities:
                if hasattr(ent, 'url') and ent.url:
                    cas.update(q_param_regex.findall(ent.url))

        if cas:
            ca_text = '\n'.join(cas)
            final_message = original_message + f"\n\nCA mudah dicopy di sini:\n{ca_text}"

            # Potong jika terlalu panjang
            if len(final_message) > 4096:
                final_message = original_message[:3900] + "\n\n...(pesan dipotong)\n" + f"\n\nCA mudah dicopy:\n{ca_text}"

            await client.send_message(TARGET_CHAT, final_message)
            print(f"✅ Forwarded dengan CA: {list(cas)}")
        else:
            print("⚠️ Tidak ditemukan CA")

    except Exception as e:
        print("❌ Error:")
        traceback.print_exc()

# --- Main function untuk dijalankan ---
async def main():
    print("🚀 Bot Telegram berjalan...")
    await client.start()
    await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
