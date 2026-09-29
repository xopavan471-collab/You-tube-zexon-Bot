import os
import time
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

API_ID = 33208732
API_HASH = "28626a3063a8161fc374ce904093c4e0"
BOT_TOKEN = "BOT TOKEN HAI" # Bhai isko BotFather se reset kar lena
ADMIN_ID = 123456789

app = Client("zexon_renamer_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

user_data = {}
registered_users = set()
total_renamed_files = 0

# --- TERA DIBBI WALA PROGRESS ---
async def progress_for_pyrogram(current, total, message, start_time, type_text):
    now = time.time()
    diff = now - start_time
    if diff == 0: return
    if round(diff % 1.50) == 0 or current == total:
        percentage = current * 100 / total
        speed = current / diff
        eta = round((total - current) / speed) if speed > 0 else 0
        filled = int(percentage // 5)
        if filled > 20: filled = 20
        bar = "▣" * filled + "▢" * (20 - filled)
        if "Download" in type_text:
            status_head = "ꜱᴛᴀᴛᴜꜱ ᴅᴏᴡɴʟᴏᴀᴅɪɴɢ ᴍᴇᴅɪᴀ :"
        else:
            status_head = "ꜱᴛᴀᴛᴜꜱ ᴜᴘʟᴏᴀᴅɪɴɢ ᴍᴇᴅɪᴀ :"
        if eta < 60:
            eta_text = f"{eta} S"
        else:
            m, s = divmod(eta, 60)
            eta_text = f"{m} M {s} S"
        text = (
            f"{status_head}\n"
            f"{bar}\n"
            f"ꜱɪᴢᴇ : {humanbytes(current)} | {humanbytes(total)}\n"
            f"ᴅᴏɴᴇ : {percentage:.0f}%\n"
            f"ꜱᴘᴇᴇᴅ : {humanbytes_speed(speed)}\n"
            f"ᴇᴛᴀ : {eta_text}"
        )
        try: await message.edit_text(text)
        except: pass

def humanbytes(size):
    if not size: return "0.00 𝙼𝙱"
    return f"{size / (1024 * 1024):.2f} 𝙼𝙱"
def humanbytes_speed(speed):
    if not speed: return "0.00 𝙼𝙱"
    return f"{speed / (1024 * 1024):.2f} 𝙼𝙱"

@app.on_message(filters.command("start"))
async def start(client: Client, message: Message):
    user = message.from_user
    registered_users.add(user.id)
    photo_url = "https://envs.sh/X_v.jpg"
    start_caption = (
        f"𝐇ᴇʏ {user.first_name}\n\n"
        f"ᴡᴇ ᴀʀᴇ ᴀᴅᴠᴀɴᴄᴇ ᴀɴᴅ ꜰᴀꜱᴛ ʀᴇɴᴀᴍᴇ ʙᴏᴛ ᴛʜᴀᴛ ꜱᴜᴘᴘᴏʀᴛ ꜰɪʟᴇ ᴍᴀxɪᴍᴜᴍ ᴏɴᴇ ɢʙ, ᴡɪᴛʜ ꜰᴀꜱᴛ ʀᴇɴᴀᴍᴇ ʏᴏᴜʀ ꜰɪʟᴇ, ᴊᴜꜱᴛ ꜱᴇɴᴅ ᴍᴇ ʏᴏᴜʀ ᴀɴʏ ꜰɪʟᴇ ᴛʜᴇɴ ʀᴇɴᴀᴍᴇ ᴀɴᴅ ɢᴇᴛ ʏᴏᴜʀ ʀᴇɴᴀᴍᴇᴅ ꜰɪʟᴇ ɪɴꜱᴛᴀɴᴛʟʏ.\n\n"
        f"ᴍᴀɪɴᴛᴇɴᴇᴅ ʙʏ: ᴢᴇxᴏɴ"
    )
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("💬 Support", url="https://t.me/your_support_username"), InlineKeyboardButton("📢 Updates", url="https://t.me/your_updates_username")],
        [InlineKeyboardButton("ℹ️ About", callback_data="about_btn"), InlineKeyboardButton("💎 Premium", callback_data="premium_btn")],
        [InlineKeyboardButton("❌ Close", callback_data="close_btn")]
    ])
    await message.reply_photo(photo=photo_url, caption=start_caption, reply_markup=keyboard)

@app.on_callback_query()
async def callback_handler(client: Client, callback_query: CallbackQuery):
    data = callback_query.data
    if data == "about_btn":
        about_text = "╭────────────────⍟\n ๏  ᴍʏ ɪɴғᴏʀᴍᴀᴛɪᴏɴ ᴀʙᴏᴜᴛ : 😌\n➻ ɴᴀᴍᴇ : ʀᴇɴᴀᴍᴇʀ ᴢᴇxᴏɴ ʙᴏᴛ\n➻ ʜᴏᴍᴇ : ᴊᴜꜱᴛʀᴜɴᴍ ᴠᴘꜱ ꜱᴇʀᴠᴇʀ\n➻ ʟᴀɴɢᴜᴀɢᴇ : ᴘʏᴛʜᴏɴ ᴇɴɢʟɪꜱʜ\n➻ ɢᴏᴅ : ᴍʀ ᴢᴇxᴏɴ ᴘᴀᴠᴀɴ\n╰─────────────────⍟"
        await callback_query.message.edit_caption(caption=about_text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="back_btn")]]))
    elif data == "back_btn":
        user = callback_query.from_user
        start_caption = f"𝐇ᴇʏ {user.first_name}\n\nᴡᴇ ᴀʀᴇ ᴀᴅᴠᴀɴᴄᴇ ᴀɴᴅ ꜰᴀꜱᴛ ʀᴇɴᴀᴍᴇ ʙᴏᴛ ᴛʜᴀᴛ ꜱᴜᴘᴘᴏʀᴛ ꜰɪʟᴇ ᴍᴀxɪᴍᴜᴍ ᴏɴᴇ ɢʙ, ᴡɪᴛʜ ꜰᴀꜱᴛ ʀᴇɴᴀᴍᴇ ʏᴏᴜʀ ꜰɪʟᴇ, ᴊᴜꜱᴛ ꜱᴇɴᴅ ᴍᴇ ʏᴏᴜʀ ᴀɴʏ ꜰɪʟᴇ ᴛʜᴇɴ ʀᴇɴᴀᴍᴇ ᴀɴᴅ ɢᴇᴛ ʏᴏᴜʀ ʀᴇɴᴀᴍᴇᴅ ꜰɪʟᴇ ɪɴꜱᴛᴀɴᴛʟʏ.\n\nᴍᴀɪɴᴛᴇɴᴇᴅ ʙʏ: ᴢᴇxᴏɴ"
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("💬 Support", url="https://t.me/your_support_username"), InlineKeyboardButton("📢 Updates", url="https://t.me/your_updates_username")],[InlineKeyboardButton("ℹ️ About", callback_data="about_btn"), InlineKeyboardButton("💎 Premium", callback_data="premium_btn")],[InlineKeyboardButton("❌ Close", callback_data="close_btn")]])
        await callback_query.message.edit_caption(caption=start_caption, reply_markup=keyboard)
    elif data == "close_btn":
        await callback_query.message.delete()

@app.on_message(filters.command("status") & filters.user(ADMIN_ID))
async def bot_status(client: Client, message: Message):
    await message.reply_text(f"📊 **Bot Live Status**\n\n👥 **Total Users:** `{len(registered_users)}`\n📁 **Total Renamed:** `{total_renamed_files}`")

@app.on_message(filters.document | filters.video | filters.audio)
async def handle_file(client: Client, message: Message):
    file = message.document or message.video or message.audio
    user_id = message.from_user.id
    registered_users.add(user_id)
    file_size_bytes = file.file_size or 0
    if file_size_bytes > 1024 * 1024 * 1024:
        await message.reply_text("⚠️ 1GB se badi file allowed nahi hai.")
        return
    file_size_mb = round(file_size_bytes / (1024 * 1024), 2)
    analysed_msg = await message.reply_text(f" File analyzed successfully!\n\n**Old Name:** `{file.file_name}`\n**Size:** `{file_size_mb} MB`\n\n**Now send me new name:**")
    user_data[user_id] = {'waiting_for_name': True, 'original_message': message, 'analysed_msg_id': analysed_msg.id}

@app.on_message(filters.text & ~filters.command("", prefix="/"))
async def handle_text_name(client: Client, message: Message):
    user_id = message.from_user.id
    if user_id not in user_data or not user_data[user_id].get('waiting_for_name'): return
    new_name = message.text.strip()
    data = user_data[user_id]
    data['waiting_for_name'] = False

    # Tera bola hua auto-delete
    try:
        await client.delete_messages(message.chat.id, data['analysed_msg_id'])
        await message.delete()
    except: pass

    status_msg = await client.send_message(message.chat.id, "Processing...⚡")
    download_path = f"downloads/{user_id}_{new_name}"
    os.makedirs("downloads", exist_ok=True)
    start_time = time.time()

    try:
        path = await client.download_media(message=data['original_message'], file_name=download_path, progress=progress_for_pyrogram, progress_args=(status_msg, start_time, "Downloading"))
        start_time = time.time()
        global total_renamed_files
        total_renamed_files += 1
        # Final file - bina kisi text ke
        await client.send_document(chat_id=message.chat.id, document=path, file_name=new_name, caption="", progress=progress_for_pyrogram, progress_args=(status_msg, start_time, "Uploading"))
        await status_msg.delete()
        if os.path.exists(path): os.remove(path)
    except Exception as e:
        await status_msg.edit_text(f"❌ Error: `{e}`")
    finally:
        if user_id in user_data: del user_data[user_id]

if __name__ == "__main__":
    print("🤖 Zexon Renamer Running...")
    app.run()
