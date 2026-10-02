import asyncio
import sys

try:
    loop = asyncio.get_event_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

import json
import math
import os
import re
import time
from concurrent.futures import ThreadPoolExecutor
from bs4 import BeautifulSoup
from pyrogram import Client, filters, idle
from pyrogram.enums import ParseMode, ChatMemberStatus
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
import requests

# --- CONFIG ---
API_ID = 33208732
API_HASH = "28626a3063a8161fc374ce904093c4e0"
BOT_TOKEN = "8724002590:AAGN3ef1v2SU6in-7o1ntmNx6WxJXKD4Y40"
ADMIN_ID = 8562470788

# Channel Force Join Config
REQUIRED_CHANNEL = -1001234567890  # Replace with your channel chat ID
CHANNEL_URL = "https://t.me/zexon_Bot_updates"

MEDIAFIRE_MAX_SIZE = 1024 * 1024 * 1024  # 1 GB Limit

USERS_FILE = "users.json"
executor = ThreadPoolExecutor(max_workers=4)

# In-memory state tracking for renames
user_states = {}

def load_users():
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, "r") as f:
                return set(json.load(f))
        except:
            return set()
    return set()

def save_users(s):
    try:
        with open(USERS_FILE, "w") as f:
            json.dump(list(s), f)
    except:
        pass

users_set = load_users()

def add_user(uid):
    if uid not in users_set:
        users_set.add(uid)
        save_users(users_set)

# --- FANCY TEXT HELPER ---
def make_fancy(text):
    normal = "0123456789."
    fancy = "𝟶𝟷𝟸𝟹𝟺𝟻𝟼𝟽𝟾𝟿."
    trans = str.maketrans(normal, fancy)
    return str(text).translate(trans)

def human_readable_size(b):
    if not b: return f"{make_fancy(0)} ᴍʙ"
    n = ("ʙ", "ᴋʙ", "ᴍʙ", "ɢʙ")
    i = int(math.floor(math.log(b, 1024)))
    p = math.pow(1024, i)
    return f"{make_fancy(round(b/p, 2))} {n[i]}"

def get_progress_bar(p):
    t = 17
    c = int((p / 100) * t)
    return "■" * c + "□" * (t - c)

def safe_remove(p):
    try:
        if p and os.path.exists(p): os.remove(p)
    except: pass

# --- JOIN CHECK ---
async def check_join(client, uid):
    if uid == ADMIN_ID: return True
    try:
        m = await client.get_chat_member(REQUIRED_CHANNEL, uid)
        if m.status in [ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
            return True
    except Exception as e:
        print(f"Check Join Error: {e}")
    return False

def get_join_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("𝙷𝙴𝚁𝙴 𝙹𝙾𝙸𝙽 𝙲𝙷𝙰𝙽𝙽𝙴𝙻", url=CHANNEL_URL)],
        [InlineKeyboardButton("𝗖𝗟𝗜𝗖𝗞 𝗧𝗢 𝗩𝗘𝗥𝗜𝗙𝗬 ✅", callback_data="check_joined")]
    ])

def extract_mediafire_link(url):
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"}
    for _ in range(3):
        try:
            r = requests.get(url, headers=headers, timeout=30)
            if r.status_code == 200:
                soup = BeautifulSoup(r.text, "html.parser")
                btn = soup.find("a", id="downloadButton") or soup.find("a", class_=re.compile("input|download", re.I)) or soup.find("a", href=re.compile("download.php"))
                if btn and btn.get("href"):
                    dlink = btn["href"]
                    if dlink.startswith("//"): dlink = "https:" + dlink
                    fname_div = soup.find("div", class_="filename")
                    fname = fname_div.text.strip() if fname_div else dlink.split("/")[-1].split("?")[0]
                    try:
                        h = requests.head(dlink, headers=headers, allow_redirects=True, timeout=20)
                        fsize = int(h.headers.get("content-length", 0))
                    except: fsize = 0
                    return dlink, fsize, fname
        except Exception as e:
            print(f"MF Extract: {e}")
            time.sleep(2)
    return None, None, None

app = Client("zexon_media_rename_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# --- HELPER KEYBOARDS & TEXTS ---
def get_home_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("ᴜᴘᴅᴀᴛᴇs", url="https://t.me/zexon_Bot_updates"), InlineKeyboardButton("ꜱᴜᴘᴘᴏʀᴛ", url="https://t.me/zexon_music_Bot")],
        [InlineKeyboardButton("ᴀʙᴏᴜᴛ", callback_data="bot_about")],
        [InlineKeyboardButton("ꜱʜᴀʀᴇ", url="https://t.me/URL_Save_Bot"), InlineKeyboardButton("ʜᴇʟᴘ", callback_data="bot_help")],
        [InlineKeyboardButton("ᴄʟᴏsᴇ", callback_data="bot_close")]
    ])

def get_welcome_text(user):
    full_name = user.first_name
    if user.last_name:
        full_name += f" {user.last_name}"

    return (
        f"<b><i>Hi</i> <code>{full_name}</code></b>\n\n"
        "<blockquote><b><i>WELCOME TO URL UPLOADER BOT</i></b>\n\n"
        "<b><i>WE CAN HELP MULTIPLE FAST PROSESS FEATURES ARE AVAILABLE TO DOWNLOAD MEDIA FIRE LINK, READY TO DOWNLOAD JUST SEND ME LINK THEN GET YOUR FILE INSTANTLY WITH SECURE FAST STABLE.</i></b>\n\n"
        "<b><i>IF YOU WANT TO ABOUT MY INFORMATION CLICK ON THE ABOUT BUTTON</i></b></blockquote>"
    )

@app.on_message(filters.command("start"))
async def start_cmd(client, message):
    add_user(message.from_user.id)
    if not await check_join(client, message.from_user.id):
        await message.reply_text("𝐅ɪʀsᴛ ᴊᴏɪɴ ᴍʏ ᴄʜᴀɴɴᴇʟ ᴛʜᴇɴ ᴄʟɪᴄᴋ ᴠᴇʀɪғʏ ᴄᴏɴᴛɪɴᴜᴇ.", reply_markup=get_join_keyboard(), parse_mode=ParseMode.HTML)
        return
    
    await message.reply_text(get_welcome_text(message.from_user), reply_markup=get_home_keyboard(), parse_mode=ParseMode.HTML)

@app.on_callback_query(filters.regex("bot_about"))
async def about_cb(client, callback_query):
    about_text = (
        "╭───────────⍟\n"
        "├ ᴍʏ ɴᴀᴍᴇ : ᴜʀʟ ᴜᴘʟᴏᴀᴅᴇʀ ʙᴏᴛ\n"
        "├ ᴅᴇᴠᴇʟᴏᴘᴇʀ : ᴢᴇxᴏɴ\n"
        "├ ʟɪʙʀᴀʀʏ : ᴘʏʀᴏɢʀᴀᴍ\n"
        "├ ʟᴀɴɢᴜᴀɢᴇ : ᴘʏᴛʜᴏɴ ᴇɴɢʟɪꜱʜ\n"
        "├ ᴅᴀᴛᴀ ʙᴀꜱᴇ : ᴘᴇʟʟᴀ ꜱᴇʀᴠᴇʀ\n"
        "├ ᴠᴇʀsɪᴏɴ : 𝟷.𝟶   \n"
        "╰───────────────⍟"
    )
    back_kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("ʙᴀᴄᴋ", callback_data="bot_home")]
    ])
    await callback_query.message.edit_text(about_text, reply_markup=back_kb, parse_mode=ParseMode.HTML)

@app.on_callback_query(filters.regex("bot_help"))
async def help_cb(client, callback_query):
    help_text = "<b><u>How to use this bot:</u></b>\n\n1. Send any <b>MediaFire Link</b> or <b>Document/File</b>.\n2. Enter the new file name when asked.\n3. The bot will rename and upload it for you instantly!"
    back_kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("ʙᴀᴄᴋ", callback_data="bot_home")]
    ])
    await callback_query.message.edit_text(help_text, reply_markup=back_kb, parse_mode=ParseMode.HTML)

@app.on_callback_query(filters.regex("bot_home"))
async def home_cb(client, callback_query):
    await callback_query.message.edit_text(
        get_welcome_text(callback_query.from_user),
        reply_markup=get_home_keyboard(),
        parse_mode=ParseMode.HTML
    )

@app.on_callback_query(filters.regex("check_joined"))
async def check_joined_cb(client, callback_query):
    uid = callback_query.from_user.id
    if await check_join(client, uid):
        try: await callback_query.message.delete()
        except: pass
        await client.send_message(uid, "𝙲𝙷𝙰𝙽𝙽𝙴𝙻 𝚅𝙴𝚁𝙸𝙵𝚈 𝙲𝙾𝙼𝙿𝙻𝙴𝚃𝙴 𝙽𝙾𝚆 𝙲𝙾𝙽𝚃𝙸𝙽𝚄𝙴 😊.", parse_mode=ParseMode.HTML)
    else:
        await callback_query.answer("𝚈𝙾𝚄 𝙰𝚁𝙴 𝙽𝙾𝚃 𝙹𝙾𝙸𝙽𝙴𝙳 𝙼𝚈 𝙲𝙷𝙰𝙽𝙽𝙴𝙻, 𝙵𝙸𝚁𝚂𝚃 𝙹𝙾𝙸𝙽 𝚃𝙷𝙴𝙽 𝙲𝙻𝙸𝙲𝙺 𝚅𝙴𝚁𝙸𝙵𝚈❌.", show_alert=True)

@app.on_callback_query(filters.regex("bot_close"))
async def close_cb(client, callback_query):
    try: await callback_query.message.delete()
    except: pass

@app.on_message(filters.command("status") & filters.user(ADMIN_ID))
async def status_cmd(client, message):
    total_users = len(users_set)
    await message.reply_text(f"📊 <b>Bot Status & User Info</b>\n\n👥 Total Unique Users: <code>{make_fancy(total_users)}</code>", parse_mode=ParseMode.HTML)

@app.on_message(filters.command("broadcast") & filters.user(ADMIN_ID))
async def broadcast_cmd(client, message):
    if not message.reply_to_message:
        await message.reply_text("⚠️ Please reply to any message to broadcast it to users!", parse_mode=ParseMode.HTML)
        return
    sent = 0
    failed = 0
    status_msg = await message.reply_text("🚀 Broadcast started...", parse_mode=ParseMode.HTML)
    for uid in list(users_set):
        try:
            await message.reply_to_message.copy(chat_id=uid)
            sent += 1
            await asyncio.sleep(0.1)
        except: failed += 1
    await status_msg.edit_text(f"✅ <b>Broadcast Completed!</b>\n\n📤 Sent: <code>{make_fancy(sent)}</code>\n❌ Failed: <code>{make_fancy(failed)}</code>", parse_mode=ParseMode.HTML)

# --- PROCESS MEDIAFIRE / FILE INPUT ---
@app.on_message((filters.text | filters.document | filters.video | filters.audio) & ~filters.command(["start", "status", "broadcast"]))
async def process_input(client, message):
    user_id = message.from_user.id
    add_user(user_id)
    
    if not await check_join(client, user_id):
        await message.reply_text("First join My Channel ⚠️", reply_markup=get_join_keyboard(), parse_mode=ParseMode.HTML)
        return

    # User state handling for rename input
    if user_id in user_states:
        state = user_states.pop(user_id)
        new_name = message.text.strip()
        info_msg = state["info_msg"]
        
        try: await info_msg.delete()
        except: pass

        status_msg = await message.reply_text("𝐏ʀᴏsᴇssɪɴGS...⏳", parse_mode=ParseMode.HTML)
        await asyncio.sleep(1)

        loop = asyncio.get_running_loop()
        local_file = None

        def safe_edit(txt):
            try:
                fut = asyncio.run_coroutine_threadsafe(status_msg.edit_text(txt, parse_mode=ParseMode.HTML), loop)
                fut.result(timeout=5)
            except: pass

        try:
            if state["type"] == "mediafire":
                dlink = state["dlink"]
                fsize = state["fsize"]
                orig_name = state["orig_name"]

                ext = os.path.splitext(orig_name)[1]
                if ext and not new_name.endswith(ext):
                    final_name = new_name + ext
                else:
                    final_name = new_name

                local_file = f"{user_id}_{int(time.time())}_{final_name}"

                def dl_file():
                    downloaded = 0
                    start = time.time()
                    last = [0]
                    headers = {"User-Agent": "Mozilla/5.0"}
                    with requests.get(dlink, headers=headers, stream=True, timeout=900) as r:
                        r.raise_for_status()
                        total = int(r.headers.get("content-length", 0)) or fsize or 0
                        with open(local_file, "wb") as f:
                            for chunk in r.iter_content(chunk_size=1024 * 1024):
                                if not chunk: continue
                                f.write(chunk)
                                downloaded += len(chunk)
                                if total > 0 and time.time() - last[0] > 3:
                                    last[0] = time.time()
                                    percent = (downloaded / total) * 100
                                    speed = downloaded / (time.time() - start + 0.1)
                                    eta = (total - downloaded) / speed if speed > 0 else 0
                                    bar = get_progress_bar(percent)
                                    txt = (
                                        f"<b>ꜱᴛᴀᴛᴜꜱ ᴅᴏᴡɴʟᴏᴀᴅɪɴɢ :</b>\n"
                                        f"<code>{bar}</code>\n"
                                        f"<b>ꜱɪᴢᴇ :</b> {human_readable_size(downloaded)} | {human_readable_size(total)}\n"
                                        f"<b>ᴅᴏɴᴇ :</b> {make_fancy(int(percent))}%\n"
                                        f"<b>ꜱᴘᴇᴇᴅ :</b> {human_readable_size(speed)}\n"
                                        f"<b>ᴇᴛᴀ :</b> {make_fancy(int(eta))} s"
                                    )
                                    safe_edit(txt)

                await loop.run_in_executor(executor, dl_file)

            elif state["type"] == "telegram_file":
                tg_msg = state["tg_msg"]
                orig_name = state["orig_name"]
                fsize = state["fsize"]

                ext = os.path.splitext(orig_name)[1]
                if ext and not new_name.endswith(ext):
                    final_name = new_name + ext
                else:
                    final_name = new_name

                start = time.time()
                last = [0]

                async def tg_dl_progress(current, total):
                    now = time.time()
                    if now - last[0] < 3: return
                    last[0] = now
                    percent = (current / total) * 100
                    speed = current / (now - start + 0.1)
                    eta = (total - current) / speed if speed > 0 else 0
                    bar = get_progress_bar(percent)
                    txt = (
                        f"<b>ꜱᴛᴀᴛᴜꜱ ᴅᴏᴡɴʟᴏᴀᴅɪɴɢ :</b>\n"
                        f"<code>{bar}</code>\n"
                        f"<b>ꜱɪᴢᴇ :</b> {human_readable_size(current)} | {human_readable_size(total)}\n"
                        f"<b>ᴅᴏɴᴇ :</b> {make_fancy(int(percent))}%\n"
                        f"<b>ꜱᴘᴇᴇᴅ :</b> {human_readable_size(speed)}\n"
                        f"<b>ᴇᴛᴀ :</b> {make_fancy(int(eta))} s"
                    )
                    try: await status_msg.edit_text(txt, parse_mode=ParseMode.HTML)
                    except: pass

                local_file = await client.download_media(tg_msg, file_name=f"{user_id}_{int(time.time())}_{final_name}", progress=tg_dl_progress)

            # Wait period while status updates to uploading
            await status_msg.edit_text("<b>Please wait uploading...</b>", parse_mode=ParseMode.HTML)
            await asyncio.sleep(3)

            upload_start = [time.time()]
            last_up_time = [0]

            async def upload_progress(current, total):
                now = time.time()
                if now - last_up_time[0] < 3: return
                last_up_time[0] = now
                percent = current * 100 / total
                elapsed = now - upload_start[0]
                speed = current / elapsed if elapsed > 0 else 0
                eta = (total - current) / speed if speed > 0 else 0
                bar = get_progress_bar(percent)
                txt = (
                    f"<b>ꜱᴛᴀᴛᴜꜱ ᴜᴘʟᴏᴀᴅɪɴɢ :</b>\n"
                    f"<code>{bar}</code>\n"
                    f"<b>ꜱɪᴢᴇ :</b> {human_readable_size(current)} | {human_readable_size(total)}\n"
                    f"<b>ᴅᴏɴᴇ :</b> {make_fancy(int(percent))}%\n"
                    f"<b>ꜱᴘᴇᴇᴅ :</b> {human_readable_size(speed)}\n"
                    f"<b>ᴇᴛᴀ :</b> {make_fancy(int(eta))} s"
                )
                try: await status_msg.edit_text(txt, parse_mode=ParseMode.HTML)
                except: pass

            await client.send_document(
                message.chat.id,
                document=local_file,
                file_name=final_name,
                caption="<b>ᴅᴏᴡɴʟᴏᴀᴅ ꜱᴜᴄᴄᴇꜱꜰᴜʟ ✨</b>",
                progress=upload_progress,
                force_document=True
            )
            await status_msg.delete()

        except Exception as e:
            print(e)
            try: await status_msg.edit_text(f"❌ Error: {e}", parse_mode=ParseMode.HTML)
            except: pass
        finally:
            safe_remove(local_file)
        return

    # Check for MediaFire Link
    if message.text and "mediafire.com" in message.text:
        text = message.text.strip()
        status_msg = await message.reply_text("𝐏ʀᴏsᴇssɪɴɢ...⏳", parse_mode=ParseMode.HTML)
        loop = asyncio.get_running_loop()
        dlink, fsize, oname = await loop.run_in_executor(executor, extract_mediafire_link, text)

        if not dlink:
            await status_msg.edit_text("this media fire Link Expired ❌", parse_mode=ParseMode.HTML)
            return

        if fsize and fsize > MEDIAFIRE_MAX_SIZE:
            await status_msg.edit_text(f"𝚂𝙾𝚁𝚁𝚈 𝚃𝙷𝙸𝚂 𝙵𝙸𝙻𝙴 𝙸𝚂 𝙱𝙸𝙶\n\n𝙵𝙸𝙻𝙴 : {human_readable_size(fsize)}\n𝙻𝙸𝙼𝙸𝚃 : {make_fancy(1024)} 𝙼𝙱", parse_mode=ParseMode.HTML)
            return

        info_text = (
            f"📄 <b>File Name:</b> <code>{oname}</code>\n"
            f"📦 <b>File Size:</b> {human_readable_size(fsize)}\n\n"
            "<b>Now send me new name</b>"
        )
        await status_msg.delete()
        info_msg = await message.reply_text(info_text, parse_mode=ParseMode.HTML)
        
        user_states[user_id] = {
            "type": "mediafire",
            "dlink": dlink,
            "fsize": fsize,
            "orig_name": oname,
            "info_msg": info_msg
        }
        return

    # Check for Document/Video/Audio Attachment
    if message.document or message.video or message.audio:
        media = message.document or message.video or message.audio
        oname = getattr(media, "file_name", f"file_{int(time.time())}")
        fsize = getattr(media, "file_size", 0)

        if fsize > MEDIAFIRE_MAX_SIZE:
            await message.reply_text(f"𝚂𝙾𝚁𝚁𝚈 𝚃𝙷𝙸𝚂 𝙵𝙸𝙻𝙴 𝙸𝚂 𝙱𝙸𝙶\n\n𝙵𝙸𝙻𝙴 : {human_readable_size(fsize)}\n𝙻𝙸𝙼𝙸𝚃 : {make_fancy(1024)} 𝙼𝙱", parse_mode=ParseMode.HTML)
            return

        info_text = (
            f"<b>File Name:</b> <code>{oname}</code>\n"
            f"<b>File Size:</b> {human_readable_size(fsize)}\n\n"
            "<b>Now send me new name</b>"
        )
        info_msg = await message.reply_text(info_text, parse_mode=ParseMode.HTML)

        user_states[user_id] = {
            "type": "telegram_file",
            "tg_msg": message,
            "fsize": fsize,
            "orig_name": oname,
            "info_msg": info_msg
        }
        return

    await message.reply_text("Dear, send MediaFire Link or File to rename 🔗", parse_mode=ParseMode.HTML)

async def main():
    await app.start()
    print("Pyrogram Bot Running - 6 Buttons & About Callback Ready ✅")
    await idle()
    await app.stop()

if __name__ == "__main__":
    try: loop.run_until_complete(main())
    except KeyboardInterrupt: print("Bot stopped!")
                                   
