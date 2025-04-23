from telethon import TelegramClient, events
from flask import Flask
from threading import Thread
import re
import traceback
import time
import hashlib
import os

# --- Konfigurasi ---
api_id = int(os.getenv("API_ID"))
api_hash = os.getenv("API_HASH")

SOURCE_CHAT = -1002214581326
TARGET_CHAT = 'soberfilter'

client = TelegramClient('sober-session', api_id, api_hash)

# Regex CA
ca_regex = re.compile(r'\b[A-HJ-NP-Za-km-z1-9]{32,60}\b')
q_param_regex = re.compile(r'[?&]q=([A-HJ-NP-Za-km-z1-9]{32,60})')

# Cache untuk anti-duplicate (pakai hash isi pesan)
message_cache = {}

# --- Handler utama ---
@client.on(events.NewMessage(chats=SOURCE_CHAT))
async def handler(event):
    try:
        original_message = event.message.message or ''
        if not re.search(r'\b3 smart money bought\b', original_message.lower()):
            print("⏭️ Skip (bukan trigger)")
            return

        # Hitung hash isi pesan
        message_hash = hashlib.md5(original_message.encode('utf-8')).hexdigest()
        now = time.time()

        # Cek cache: kalau hash sudah ada & < 60 detik => skip
        if message_hash in message_cache and (now - message_cache[message_hash]) < 60:
            print("⏱️ Duplikat kurang dari 1 menit — di-skip.")
            return
        else:
            message_cache[message_hash] = now

        all_text = original_message
        cas = set()

        # ✅ Dari teks biasa
        cas.update(ca_regex.findall(all_text))
        cas.update(q_param_regex.findall(all_text))

        # ✅ Dari anchor link tersembunyi (entities)
        for ent in event.message.entities or []:
            if hasattr(ent, 'url') and ent.url:
                cas.update(q_param_regex.findall(ent.url))

        if cas:
            ca_text = '\n'.join(cas)
            final_message = original_message + f"\n\nCA mudah dicopy di sini:\n{ca_text}"

            if len(final_message) > 4096:
                final_message = original_message[:3900] + "\n\n...(pesan dipotong)\n" + f"\n\nCA mudah dicopy:\n{ca_text}"

            await client.send_message(TARGET_CHAT, final_message)
            print(f"✅ Forwarded dengan CA: {list(cas)}")
        else:
            print("⚠️ Tidak ditemukan CA di teks atau URL.")

    except Exception as e:
        print("❌ Error saat proses:")
        traceback.print_exc()

# --- Flask Keep-Alive ---
app = Flask(__name__)

@app.route('/')
def home():
    return '✅ Bot aktif dan siap!'

def keep_alive():
    app.run(host='0.0.0.0', port=8080)

# --- Jalankan bot ---
Thread(target=keep_alive, daemon=True).start()
print("🚀 Bot berjalan... Menunggu pesan dari grup.")
client.start()
client.run_until_disconnected()
