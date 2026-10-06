import asyncio
import json
import math
import os
import random
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from bs4 import BeautifulSoup
from pyrogram import Client, filters, idle
from pyrogram.enums import ParseMode, ChatMemberStatus
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from pyrogram.raw import types
import requests
import yt_dlp

# --- CONFIG ---
API_ID = 33208732
API_HASH = "28626a3063a8161fc374ce904093c4e0"
BOT_TOKEN = "8283637087:AAHxTUU70SagkcNWIpNnEyZcbzv-1eVTuiE"
ADMIN_ID = 8562470788

REQUIRED_CHANNEL = -1001234567890 # Replace with Channel ID or Username
CHANNEL_URL = "https://t.me/zexon_Bot_updates"

# Host Crash Protect Cap (Set to 400MB)
MEDIAFIRE_MAX_SIZE = 400 * 1024 * 1024
SOCIAL_MAX_SIZE = 400 * 1024 * 1024

# --- REACTION EMOJIS LIST ---
REACTION_EMOJIS = ["🎉", "🥺", "😅", "⚡", "😊", "🙏", "🔥", "😍", "😘", "😐", "😌", "😃", "😂", "😭", "🙃", "🤭", "🤨", "😈", "👻", "👍"]

USERS_FILE = "users.json"
executor = ThreadPoolExecutor(max_workers=2)

def load_users():
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, "r") as f:
                return set(json.load(f))
        except Exception:
            return set()
    return set()

def save_users(s):
    try:
        with open(USERS_FILE, "w") as f:
            json.dump(list(s), f)
    except Exception:
        pass

users_set = load_users()
def add_user(uid):
    if uid not in users_set:
        users_set.add(uid)
        save_users(users_set)

# --- HELPER FUNCTIONS ---
def get_random_emoji():
    return random.choice(REACTION_EMOJIS)

def make_fancy(text):
    normal = "0123456789."
    fancy = "𝟶𝟷𝟸𝟹𝟺𝟻𝟼𝟽𝟾𝟿."
    trans = str.maketrans(normal, fancy)
    return str(text).translate(trans)

def human_readable_size(b):
    if not b: return f"{make_fancy(0)} ᴍʙ"
    n = ("ʙ", "ᴋʙ", "ᴍʙ", "ɢʙ")
    i = int(math.floor(math.log(b, 1024))) if b > 0 else 0
    p = math.pow(1024, i)
    return f"{make_fancy(round(b/p, 2))} {n[i]}"

# --- PERFECT DIBBI PROGRESS BAR FUNCTION ---
def get_progress_bar(p):
    t = 16
    if p >= 99.5:  # Pure 100% par poori 16 dibbi bharegi
        return "▣" * t
    c = int((p / 100) * t)
    c = min(max(c, 0), t - 1)  # Complete hone se pehle max 15 dibbi
    return "▣" * c + "▢" * (t - c)

def safe_remove(p):
    try:
        if p and os.path.exists(p):
            os.remove(p)
            print(f"Cleaned up file: {p}")
    except Exception as e:
        print(f"File Cleanup Error: {e}")

# --- CHANNEL JOIN CHECK ---
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
                    except Exception: fsize = 0
                    return dlink, fsize, fname
        except Exception as e:
            print(f"MF Extract Error: {e}")
            time.sleep(2)
    return None, None, None

def extract_devuploads_link(url):
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"}
    for _ in range(3):
        try:
            r = requests.get(url, headers=headers, timeout=30)
            if r.status_code == 200:
                soup = BeautifulSoup(r.text, "html.parser")
                data = {}
                for input_tag in soup.find_all("input"):
                    if input_tag.get("name"):
                        data[input_tag.get("name")] = input_tag.get("value", "")

                post_r = requests.post(url, data=data, headers=headers, timeout=30)
                if post_r.status_code == 200:
                    post_soup = BeautifulSoup(post_r.text, "html.parser")
                    download_btn = post_soup.find("a", class_="download-btn") or post_soup.find("a", id="downloadbtn") or post_soup.find("a", href=re.compile("download"))
                    if download_btn and download_btn.get("href"):
                        dlink = download_btn["href"]
                        fname = dlink.split("/")[-1].split("?")[0]
                        try:
                            h = requests.head(dlink, headers=headers, allow_redirects=True, timeout=20)
                            fsize = int(h.headers.get("content-length", 0))
                        except Exception: fsize = 0
                        return dlink, fsize, fname
        except Exception as e:
            print(f"Devuploads Extract Error: {e}")
            time.sleep(2)
    return None, None, None

app = Client("zexon_media_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

 # --- FIXED EMOJI REACTION HELPER FOR PYROGRAM ---
async def react_user_message(message):
    try:
        emoji = get_random_emoji()
        try:
            await message.react(emoji)
        except Exception:
            await app.send_reaction(
                chat_id=message.chat.id,
                message_id=message.id,
                emoji=types.ReactionEmoji(emoticon=emoji)
            )
    except Exception as e:
        print(f"Reaction Error: {e}")

@app.on_message(filters.command("start"))
async def start_cmd(client, message):
    add_user(message.from_user.id)
    await react_user_message(message)

    if not await check_join(client, message.from_user.id):
        await message.reply_text("𝐅ɪʀsᴛ ᴊᴏɪɴ ᴍʏ ᴄʜᴀɴɴᴇʟ ᴛʜᴇɴ ᴄʟɪᴄᴋ ᴠᴇʀɪғʏ ᴄᴏɴᴛɪɴᴜᴇ.", reply_markup=get_join_keyboard(), parse_mode=ParseMode.HTML)
        return
    welcome_text = (
        f"<b> 𝐇ᴇʟʟᴏ <code>{message.from_user.first_name}</code> !!</b>\n\n"
        "<blockquote> <b>𝐖ᴇʟᴄᴏᴍᴇ 𝐓ᴏ 𝐌ᴇᴅɪᴀ 𝐔ᴘʟᴏᴀᴅᴇʀ 𝐁ᴏᴛ</b></blockquote>\n"
        "<blockquote><i>ᴡᴇ ᴄᴀɴ ʜᴇʟᴘ ᴍᴜʟᴛɪᴘʟᴇ ꜰᴀꜱᴛ ᴘʀᴏꜱᴇꜱꜱ ꜰᴇᴀᴛᴜʀᴇꜱ ᴀʀᴇ ᴀᴠᴀɪʟᴀʙʟᴇ ᴛᴏ ᴅᴏᴡɴʟᴏᴀᴅ ᴍᴇᴅɪᴀ ꜰɪʀᴇ ꜰɪʟᴇ, ɪɴꜱᴛᴀɢʀᴀᴍ ꜰᴀᴄᴇʙᴏᴏᴋ ᴀɴᴅ ᴛɪᴋᴛᴏᴋ ᴠɪᴅᴇᴏ ʀᴇᴀᴅʏ ᴛᴏ ᴅᴏᴡɴʟᴏᴀᴅ ᴊᴜꜱᴛ ꜱᴇɴᴅ ᴍᴇ ʟɪɴᴋ ᴛʜᴇɴ ɢᴇᴛ ʏᴏᴜʀ ꜰɪʟᴇ ɪɴꜱᴛᴀɴᴛʟʏ ᴡɪᴛʜ ꜱᴇᴄᴜʀᴇ ꜰᴀꜱᴛ ꜱᴛᴀʙʟᴇ.</i></blockquote>\n"
        "<blockquote><b>𝐏ʟᴇᴀsᴇ 𝐒ʜᴀʀᴇ 𝐀ɴᴅ 𝐆ɪᴠᴇ 𝐒ᴜᴘᴘᴏʀᴛ</b></blockquote>"
    )
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("ᴜᴘᴅᴀᴛᴇs", url="https://t.me/zexon_Bot_updates")],
        [InlineKeyboardButton("ꜱᴜᴘᴘᴏʀᴛ", url="https://t.me/zexon_music_Bot"), InlineKeyboardButton("ꜱʜᴀʀᴇ", url="https://t.me/URL_Save_Bot")],
        [InlineKeyboardButton("ᴅᴇᴠᴇʟᴏᴘᴇʀ", url="https://t.me/zexon_x")],
        [InlineKeyboardButton("ᴄʟᴏsᴇ", callback_data="bot_close")],
    ])
    await message.reply_text(welcome_text, reply_markup=kb, parse_mode=ParseMode.HTML)

@app.on_callback_query(filters.regex("check_joined"))
async def check_joined_cb(client, callback_query):
    uid = callback_query.from_user.id
    if await check_join(client, uid):
        try: await callback_query.message.delete()
        except Exception: pass
        await client.send_message(uid, "<b>𝙲𝙷𝙰𝙽𝙽𝙴𝙻 𝚅𝙴𝚁𝙸𝙵𝙸𝙴𝙳! 𝙽𝙾𝚆 𝙲𝙾𝙽𝚃𝙸𝙽𝚄𝙴 🎉.</b>", parse_mode=ParseMode.HTML)
    else:
        await callback_query.answer("𝑌𝙾𝚄 𝙰𝚁𝙴 𝙽𝙾𝚃 𝙹𝙾𝙸𝙽𝙴𝙳 𝙼𝙸𝙽𝙴 𝙲𝙷𝙰𝙽𝙽𝙴𝙻, 𝙵𝙸𝚁𝚂𝚃 𝙹𝙾𝙸𝙽 𝚃𝙷𝙴𝙽 𝙲𝙻𝙸𝙲𝙺 𝚅𝙴𝚁𝙸𝙵𝙸𝙴𝙳❌.", show_alert=True)

@app.on_callback_query(filters.regex("bot_close"))
async def close_cb(client, callback_query):
    try: await callback_query.message.delete()
    except Exception: pass

@app.on_message(filters.command("status") & filters.user(ADMIN_ID))
async def status_cmd(client, message):
    await react_user_message(message)
    total_users = len(users_set)
    await message.reply_text(f"📊 <b>Bot Status & User Info</b>\n\n👥 Total Unique Users: <code>{make_fancy(total_users)}</code>", parse_mode=ParseMode.HTML)

@app.on_message(filters.command("broadcast") & filters.user(ADMIN_ID))
async def broadcast_cmd(client, message):
    await react_user_message(message)
    if not message.reply_to_message:
        await message.reply_text("⚠️ Please reply to any message to broadcast it!", parse_mode=ParseMode.HTML)
        return
    sent, failed = 0, 0
    status_msg = await message.reply_text("🚀 Broadcast started...", parse_mode=ParseMode.HTML)
    for uid in list(users_set):
        try:
            await message.reply_to_message.copy(chat_id=uid)
            sent += 1
            await asyncio.sleep(0.1)
        except Exception:
            failed += 1
    await status_msg.edit_text(f"✅ <b>Broadcast Completed!</b>\n\n📤 Sent: <code>{make_fancy(sent)}</code>\n❌ Failed: <code>{make_fancy(failed)}</code>", parse_mode=ParseMode.HTML)

@app.on_message(filters.text & ~filters.command(["start", "status", "broadcast"]))
async def process(client, message):
    user_id = message.from_user.id
    add_user(user_id)
    await react_user_message(message)

    if not await check_join(client, user_id):
        await message.reply_text("First join My Channel ⚠", reply_markup=get_join_keyboard(), parse_mode=ParseMode.HTML)
        return

    text = message.text.strip()
    is_mf = "mediafire.com" in text
    is_dev = "devuploads.com" in text
    is_ig = "instagram.com" in text
    is_fb = bool(re.search(r"(facebook\.com|fb\.watch|fb\.com/reel)", text))
    is_tiktok = "tiktok.com" in text or "vm.tiktok.com" in text
    is_yt = "youtube.com" in text or "youtu.be" in text

    if not (is_mf or is_dev or is_ig or is_fb or is_tiktok or is_yt):
        await message.reply_text("Dear, send Mediafire, Devuploads, Instagram, Facebook or TikTok link 🔗", parse_mode=ParseMode.HTML)
        return

    status_msg = await message.reply_text("𝐏ʀᴏsᴇssɪɴɢ...⏳", parse_mode=ParseMode.HTML)
    loop = asyncio.get_running_loop()
    local_file = None

    def safe_edit(txt):
        try:
            fut = asyncio.run_coroutine_threadsafe(status_msg.edit_text(txt, parse_mode=ParseMode.HTML), loop)
            fut.result(timeout=4)
        except Exception: pass

    try:
        if is_mf or is_dev:
            if is_mf:
                dlink, fsize, oname = await loop.run_in_executor(executor, extract_mediafire_link, text)
                err_msg = "This Mediafire link expired ❌"
            else:
                dlink, fsize, oname = await loop.run_in_executor(executor, extract_devuploads_link, text)
                err_msg = "This Devuploads link not supported ❌"

            if not dlink:
                await status_msg.edit_text(err_msg, parse_mode=ParseMode.HTML)
                return

            if fsize and fsize > MEDIAFIRE_MAX_SIZE:
                await status_msg.edit_text(f"𝚂𝙾𝚁𝚁𝚈 𝚃𝙷𝙸𝚂 𝙵𝙸𝙻𝙴 𝙸𝚂 𝙱𝙸𝙶\n𝙵𝙸𝙻𝙴 : {human_readable_size(fsize)}\n𝙻𝙸𝙼𝙸𝚃 : {make_fancy(400)} 𝙼𝙱", parse_mode=ParseMode.HTML)
                return

            local_file = f"{user_id}_{int(time.time())}_{oname}"

            def dl_file():
                downloaded = 0
                start = time.time()
                last = [0]
                headers = {"User-Agent": "Mozilla/5.0"}
                with requests.get(dlink, headers=headers, stream=True, timeout=900) as r:
                    r.raise_for_status()
                    total = int(r.headers.get("content-length", 0)) or fsize or 0
                    with open(local_file, "wb") as f:
                        for chunk in r.iter_content(chunk_size=2 * 1024 * 1024):
                            if not chunk: continue
                            f.write(chunk)
                            downloaded += len(chunk)
                            now = time.time()
                            is_complete = (downloaded >= total and total > 0)
                            if total > 0 and (now - last[0] > 3.5 or is_complete):
                                last[0] = now
                                percent = 100.0 if is_complete else (downloaded / total) * 100
                                speed = downloaded / (now - start + 0.1)
                                eta = 0 if is_complete else (total - downloaded) / speed if speed > 0 else 0
                                bar = get_progress_bar(percent)
                                txt = (
                                    f"<b>ꜱᴛᴀᴛᴜꜱ ᴅᴏᴡɴʟᴏᴀᴅɪɴɢ :</b>\n"
                                    f"<code>{bar}</code>\n"
                                    f"<b>ꜱɪᴢᴇ :</b> {human_readable_size(downloaded)} | {human_readable_size(total)}\n"
                                    f"<b>ᴅᴏɴᴇ :</b> {make_fancy(int(percent))}%\n"
                                    f"<b>ꜱᴘᴇᴇᴅ :</b> {human_readable_size(speed)}\n"
                                    f"<b> ᴇᴛᴀ :</b> {make_fancy(int(eta))} s"
                                )
                                safe_edit(txt)

            await loop.run_in_executor(executor, dl_file)

            try:
                await status_msg.edit_text("<b><i>𝐏ʟᴇᴀꜱᴇ ᴡᴀɪᴛ ᴜᴘʟᴏᴀᴅɪɴɢ...⚡</i></b>", parse_mode=ParseMode.HTML)
                await asyncio.sleep(1)
            except Exception:
                pass

            upload_start = [time.time()]
            last_up_time = [0]

            async def upload_progress(current, total):
                now = time.time()
                is_complete = (current >= total and total > 0)
                percent = 100.0 if is_complete else ((current / total) * 100 if total > 0 else 0)
                if not is_complete and (now - last_up_time[0] < 3.5): return
                last_up_time[0] = now
                elapsed = now - upload_start[0]
                speed = current / elapsed if elapsed > 0 else 0
                eta = 0 if is_complete else ((total - current) / speed if speed > 0 else 0)
                bar = get_progress_bar(percent)
                txt = (
                    f"<b>ꜱᴛᴀᴛᴜꜱ ᴜᴘʟᴏᴀᴅɪɴɢ :</b>\n"
                    f"<code>{bar}</code>\n"
                    f"<b>ꜱɪᴢᴇ :</b> {human_readable_size(current)} | {human_readable_size(total)}\n"
                    f"<b>ᴅᴏɴᴇ :</b> {make_fancy(int(percent))}%\n"
                    f"<b>ꜱᴘᴇᴇᴅ :</b> {human_readable_size(speed)}\n"
                    f"<b> ᴇᴛᴀ :</b> {make_fancy(int(eta))} s"
                )
                try: await status_msg.edit_text(txt, parse_mode=ParseMode.HTML)
                except Exception: pass

            await client.send_document(
                chat_id=message.chat.id,
                document=local_file,
                file_name=oname,
                progress=upload_progress,
                force_document=True
            )
            try:
                await status_msg.delete()
            except Exception:
                pass

        else:
            dl_last_edit = [0]

            def yt_progress_hook(d):
                if d.get('status') == 'downloading':
                    now = time.time()
                    downloaded = d.get('downloaded_bytes', 0)
                    total = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
                    speed = d.get('speed') or 0
                    eta = d.get('eta') or 0

                    is_complete = (d.get('status') == 'finished' or (total > 0 and downloaded >= total))
                    if not is_complete and (now - dl_last_edit[0] < 3.5):
                        return
                    dl_last_edit[0] = now

                    try:
                        percent = 100.0 if is_complete else ((downloaded / total) * 100 if total > 0 else 0)
                        bar = get_progress_bar(percent)

                        txt = (
                            f"<b>ꜱᴛᴀᴛᴜꜱ ᴅᴏᴡɴʟᴏᴀᴅɪɴɢ :</b>\n"
                            f"<code>{bar}</code>\n"
                            f"<b>ꜱɪᴢᴇ :</b> {human_readable_size(downloaded)} | {human_readable_size(total)}\n"
                            f"<b>ᴅᴏɴᴇ :</b> {make_fancy(int(percent))}%\n"
                            f"<b>ꜱᴘᴇᴇᴅ :</b> {human_readable_size(speed)}\n"
                            f"<b> ᴇᴛᴀ :</b> {make_fancy(int(eta))} s"
                        )
                        safe_edit(txt)
                    except Exception:
                        pass

            def run_social():
                opts = {
                    "format": "best[height<=720][ext=mp4]/best[ext=mp4]/best",
                    "merge_output_format": None,
                    "postprocessors": [],
                    "outtmpl": f"dl_{user_id}_%(id)s.%(ext)s",
                    "quiet": True, "no_warnings": True, "nocheckcertificate": True,
                    "retries": 10, "fragment_retries": 10,
                    "progress_hooks": [yt_progress_hook],
                    "extractor_args": {"youtube": {"player_client": ["android", "ios", "web"]}},
                    "http_headers": {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"},
                }
                if os.path.exists("cookies.txt"): opts["cookiefile"] = "cookies.txt"
                with yt_dlp.YoutubeDL(opts) as ydl:
                    info = ydl.extract_info(text, download=True)
                    fn = ydl.prepare_filename(info)
                    if not os.path.exists(fn):
                        base = os.path.splitext(fn)[0]
                        for ext in [".mp4", ".mkv", ".webm", ".m4a"]:
                            if os.path.exists(base + ext):
                                fn = base + ext
                                break
                    return fn

            local_file = await loop.run_in_executor(executor, run_social)

            try:
                await status_msg.edit_text(
                    f"<b><i>𝐏ʟᴇᴀꜱᴇ ᴡᴀɪᴛ ᴜᴘʟᴏᴀᴅɪɴɢ...⚡</i></b>",
                    parse_mode=ParseMode.HTML
                )
                await asyncio.sleep(1)
            except Exception:
                pass

            up_start2 = [time.time()]
            last_up2 = [0]
            async def up_progress(c, t):
                now = time.time()
                is_complete = (c >= t and t > 0)
                p = 100.0 if is_complete else ((c / t) * 100 if t > 0 else 0)
                if not is_complete and (now - last_up2[0] < 3.5): return
                last_up2[0] = now
                speed = c / (now - up_start2[0] + 0.1)
                eta = 0 if is_complete else ((t - c) / speed if speed > 0 else 0)
                bar = get_progress_bar(p)
                txt = (
                    f"<b>ꜱᴛᴀᴛᴜꜱ ᴜᴘʟᴏᴀᴅɪɴɢ :</b>\n"
                    f"<code>{bar}</code>\n"
                    f"<b>ꜱɪᴢᴇ :</b> {human_readable_size(c)} | {human_readable_size(t)}\n"
                    f"<b>ᴅᴏɴᴇ :</b> {make_fancy(int(p))}%\n"
                    f"<b>ꜱᴘᴇᴇᴅ :</b> {human_readable_size(speed)}\n"
                    f"<b> ᴇᴛᴀ :</b> {make_fancy(int(eta))} s"
                )
                try: await status_msg.edit_text(txt,parse_mode=ParseMode.HTML)
                except Exception: pass

             if local_file and os.path.exists(local_file):
                await client.send_video(
                    chat_id=message.chat.id,
                    video=local_file,
                    supports_streaming=True,
                    progress=up_progress,
                )
                try:
                    await status_msg.delete()
                except Exception:
                    pass


    # --- AUTOMATIC FILE KACHRA (CLEANUP) SYSTEM ---
    finally:
        if local_file:
            safe_remove(local_file)

if __name__ == "__main__":
    app.run()
