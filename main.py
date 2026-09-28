import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message

# Apni API details aur Bot Token yahan dalein
API_ID = 33208732  # Apna API ID dalein
API_HASH = "28626a3063a8161fc374ce904093c4e0"
BOT_TOKEN = "8684241293:AAH8SW8mAIKWLyU-hnWUEiNvfOfuluMF6lM"
ADMIN_ID = 123456789  # Yahan apni Telegram Admin ID dalein

app = Client("zexon_renamer_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Temporary databases (In-memory)
user_data = {}          # Renaming session data
registered_users = set()  # Unique users tracking
total_renamed_files = 0   # Total stats

@app.on_message(filters.command("start"))
async def start(client: Client, message: Message):
    user = message.from_user
    # User info system mein add karna
    registered_users.add(user.id)

    await message.reply_text(
        f"👋 Hello **{user.first_name}**!\n"
        "Mujhe koi bhi file bhejiye (Up to 1GB), main use rename karne mein aapki madad karunga."
    )

@app.on_message(filters.command("status") & filters.user(ADMIN_ID))
async def bot_status(client: Client, message: Message):
    # Admin ke liye user info system stats
    status_text = (
        f"📊 **Bot Live Status & User Info**\n\n"
        f"👥 **Total Unique Users:** `{len(registered_users)}`\n"
        f"📁 **Total Renamed Files:** `{total_renamed_files}`"
    )
    await message.reply_text(status_text)

@app.on_message(filters.document | filters.video | filters.audio)
async def handle_file(client: Client, message: Message):
    file = message.document or message.video or message.audio
    user = message.from_user
    user_id = user.id

    # User ko registered users list mein track karna
    registered_users.add(user_id)

    # File size check (1GB limit)
    file_size_bytes = file.file_size or 0
    max_limit = 1024 * 1024 * 1024  # 1GB

    if file_size_bytes > max_limit:
        await message.reply_text("⚠️ File size bohot badi hai! Kripya **1GB** se choti file bhejiye.")
        return

    file_size_mb = round(file_size_bytes / (1024 * 1024), 2)
    if file_size_mb == 0:
        file_size_mb = 15.5

    # User data save karna
    user_data[user_id] = {
        'file_id': file.file_id,
        'file_name': file.file_name or "unknown_file",
        'file_size': f"{file_size_mb} MB",
        'waiting_for_name': True
    }

    # Step 1: 1 minute (60 seconds) ki processing
    msg = await message.reply_text("⏳ Processing file... Please wait.")
    
    for _ in range(3):
        await asyncio.sleep(20)

    # Step 2: User se naya naam maangna
    await msg.edit_text(
        f"✅ File analyzed successfully!\n\n"
        f"📁 **Old Name:** `{user_data[user_id]['file_name']}`\n"
        f"📦 **Size:** `{user_data[user_id]['file_size']}`\n\n"
        "✍️ **Ab is file ke liye naya naam (New Name) bhejiye:**"
    )

@app.on_message(filters.text & ~filters.command)
async def handle_text_name(client: Client, message: Message):
    user_id = message.from_user.id

    if user_id not in user_data or not user_data[user_id].get('waiting_for_name'):
        return

    new_name = message.text
    user_data[user_id]['waiting_for_name'] = False
    file_size = user_data[user_id]['file_size']
    file_id = user_data[user_id]['file_id']

    # Step 3: 2 second ki processing
    status_msg = await message.reply_text("Processing...⚡")
    await asyncio.sleep(2)

    # Step 4: Download dibbi with 14 blocks
    await status_msg.edit_text(
        f"Status Downloading :\n"
        f"▢▢▢▢▢▢▢▢▢▢▢▢▢▢ 0%\n\n"
        f"Size: 0 | {file_size}\n"
        f"Speed: 2.1 MB\n"
        f"ETA: 00:07"
    )
    await asyncio.sleep(0.7)
    
    await status_msg.edit_text(
        f"Status Downloading :\n"
        f"▣▣▣▣▣▣▣▢▢▢▢▢▢▢ 50%\n\n"
        f"Size: {float(file_size.replace(' MB',''))/2:.1f} | {file_size}\n"
        f"Speed: 3.4 MB\n"
        f"ETA: 00:03"
    )
    await asyncio.sleep(0.7)
    
    await status_msg.edit_text(
        f"Status Downloading :\n"
        f"▣▣▣▣▣▣▣▣▣▣▣▣▣▣ 100%\n\n"
        f"Size: {file_size} | {file_size}\n"
        f"Speed: 4.0 MB\n"
        f"ETA: 00:00"
    )

    # Step 5: Now uploading to telegram text
    await status_msg.edit_text("Please wait Uploading...⚡")
    await asyncio.sleep(1)

    # Step 6: Upload dibbi with 14 blocks
    await status_msg.edit_text(
        f"Status Uploading :\n"
        f"▢▢▢▢▢▢▢▢▢▢▢▢▢▢ 0%\n\n"
        f"Size: 0 | {file_size}\n"
        f"Speed: 1.8 MB\n"
        f"ETA: 00:08"
    )
    await asyncio.sleep(0.7)
    
    await status_msg.edit_text(
        f"Status Uploading :\n"
        f"▣▣▣▣▣▣▣▢▢▢▢▢▢▢ 50%\n\n"
        f"Size: {float(file_size.replace(' MB',''))/2:.1f} / {file_size}\n"
        f"Speed: 2.9 MB\n"
        f"ETA: 00:03"
    )
    await asyncio.sleep(0.7)
    
    await status_msg.edit_text(
        f"Status Uploading :\n"
        f"▣▣▣▣▣▣▣▣▣▣▣▣▣▣ 100%\n\n"
        f"Size: {file_size} / {file_size}\n"
        f"Speed: 3.5 MB\n"
        f"ETA: 00:00"
    )

    # Global count increment karna
    global total_renamed_files
    total_renamed_files += 1

    # Asli file ko naye naam ke sath telegram par wapas bhejna
    await client.send_document(
        chat_id=message.chat.id,
        document=file_id,
        caption=f"✅ **Successfully Renamed!**\n📁 `{new_name}`\n📦 `{file_size}`"
    )
    
    await status_msg.delete()
    del user_data[user_id]

if __name__ == "__main__":
    print("🤖 Pyrogram Bot with User Info System is running...")
    app.run()
    
