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

# Channel - yaha apna channel dal de, warna check hata dunga
REQUIRED_CHANNEL = "zexon_Bot_updates"
CHANNEL_URL = "https://t.me/zexon_Bot_updates"

MEDIAFIRE_MAX_SIZE = 4 * 1024 * 1024 * 1024 # 4 GB Limit
USERS_FILE = "users.json"
executor = ThreadPoolExecutor(max_workers=4)

# Rename store
rename_dict = {}

def load_users():
  if os.path.exists(USERS_FILE):
    try:
      with open(USERS_FILE, "r") as f:
        return set(json.load(f))
    except: return set()
  return set()

def save_users(s):
  try:
    with open(USERS_FILE, "w") as f: json.dump(list(s), f)
  except: pass

users_set = load_users()
def add_user(uid):
  if uid not in users_set:
    users_set.add(uid)
    save_users(users_set)

def make_fancy(text):
  normal = "0123456789."
  fancy = "𝟶𝟷𝟸𝟹𝟺𝟻𝟼𝟽𝟾𝟿."
  return str(text).translate(str.maketrans(normal, fancy))

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

async def check_join(client, uid):
  if uid == ADMIN_ID: return True
  try:
    m = await client.get_chat_member(REQUIRED_CHANNEL, uid)
    if m.status in [ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]: return True
  except: pass
  return False

def get_join_keyboard():
  return InlineKeyboardMarkup([
      [InlineKeyboardButton("𝙷𝙴𝚁𝙴 𝙹𝙾𝙸𝙽 𝙲𝙷𝙰𝙽𝙽𝙴𝙻", url=CHANNEL_URL)],
      [InlineKeyboardButton("𝗖𝗟𝗜𝗖𝗞 𝗧𝗢 𝗩𝗘𝗥𝗜𝗙𝗬 ✅", callback_data="check_joined")]
  ])

def extract_mediafire_link(url):
  headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0"}
  for _ in range(3):
    try:
      r = requests.get(url, headers=headers, timeout=30)
      if r.status_code == 200:
        soup = BeautifulSoup(r.text, "html.parser")
        btn = soup.find("a", id="downloadButton") or soup.find("a", class_=re.compile("input|download", re.I))
        if btn and btn.get("href"):
          dlink = btn["href"]
          if dlink.startswith("//"): dlink = "https:" + dlink
          fname = soup.find("div", class_="filename")
          fname = fname.text.strip() if fname else dlink.split("/")[-1].split("?")[0]
          try:
            h = requests.head(dlink, headers=headers, allow_redirects=True, timeout=20)
            fsize = int(h.headers.get("content-length", 0))
          except: fsize = 0
          return dlink, fsize, fname
    except: time.sleep(2)
  return None, None, None

def extract_devuploads_link(url):
  headers = {"User-Agent": "Mozilla/5.0"}
  for _ in range(3):
    try:
      r = requests.get(url, headers=headers, timeout=30)
      if r.status_code == 200:
        soup = BeautifulSoup(r.text, "html.parser")
        data = {}
        for inp in soup.find_all("input"):
          if inp.get("name"): data[inp.get("name")] = inp.get("value", "")
        post_r = requests.post(url, data=data, headers=headers, timeout=30)
        if post_r.status_code == 200:
          post_soup = BeautifulSoup(post_r.text, "html.parser")
          btn = post_soup.find("a", class_="download-btn") or post_soup.find("a", id="downloadbtn")
          if btn and btn.get("href"):
            dlink = btn["href"]
            fname = dlink.split("/")[-1].split("?")[0]
            try: fsize = int(requests.head(dlink, headers=headers, allow_redirects=True, timeout=20).headers.get("content-length", 0))
            except: fsize = 0
            return dlink, fsize, fname
    except: time.sleep(2)
  return None, None, None

app = Client("zexon_4gb_rename", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

@app.on_message(filters.command("start"))
async def start_cmd(client, message):
  add_user(message.from_user.id)
  if not await check_join(client, message.from_user.id):
    await message.reply_text("𝐅ɪʀsᴛ ᴊᴏɪɴ ᴍʏ ᴄʜᴀɴɴᴇʟ ᴛʜᴇɴ ᴄʟɪᴄᴋ ᴠᴇʀɪғʏ.", reply_markup=get_join_keyboard(), parse_mode=ParseMode.HTML)
    return

  welcome_text = f"<b> 𝐇ᴇʟʟᴏ <code>{message.from_user.first_name}</code>!!</b>\n\n<blockquote><b>𝐖ᴇʟᴄᴏᴍᴇ 𝐓ᴏ 𝟺𝙶𝙱 𝐔ᴘʟᴏᴀᴅᴇʀ 𝐁ᴏᴛ</b>\n\n<i>ᴍᴇᴅɪᴀꜰɪʀᴇ + ᴅᴇᴠᴜᴘʟᴏᴀᴅꜱ + ʀᴇɴᴀᴍᴇ ꜱᴜᴘᴘᴏʀᴛ 𝟺ɢʙ ᴛᴀᴋ</i></blockquote>"

  # 6 BUTTONS - 2 UPAR, 2 NICHE, 1 BEECH, 1 SABSE NICHE
  kb = InlineKeyboardMarkup([
      [InlineKeyboardButton("🔗 MEGA", callback_data="mega_info"), InlineKeyboardButton("☁️ MediaFire", callback_data="mf_info")],
      [InlineKeyboardButton("📁 Dupload", callback_data="dupload_info"), InlineKeyboardButton("🚀 DevUploads", callback_data="dev_info")],
      [InlineKeyboardButton("✏️ Rename Help", callback_data="rename_help")],
      [InlineKeyboardButton("❌ Close", callback_data="bot_close")]
  ])
  await message.reply_text(welcome_text, reply_markup=kb, parse_mode=ParseMode.HTML)

@app.on_message(filters.command("rename"))
async def rename_cmd(client, message):
  if len(message.command) < 2:
    await message.reply_text("Use: <code>/rename new_file_name.mp4</code> - file ko reply karke likho", parse_mode=ParseMode.HTML)
    return
  if not message.reply_to_message or not message.reply_to_message.document:
    await message.reply_text("Kisi file ko reply karke /rename likho bhai!", parse_mode=ParseMode.HTML)
    return
  new_name = " ".join(message.command[1:])
  rename_dict[message.reply_to_message.id] = new_name
  await message.reply_text(f"✅ Rename set: <code>{new_name}</code>\nAb us file ko forward karo ya download karne bolo", parse_mode=ParseMode.HTML)

@app.on_callback_query()
async def all_callbacks(client, cq):
  data = cq.data
  if data == "bot_close":
    try: await cq.message.delete()
    except: pass
  elif data == "check_joined":
    if await check_join(client, cq.from_user.id):
      try: await cq.message.delete()
      except: pass
      await client.send_message(cq.from_user.id, "Verified ✅ Ab link bhejo")
    else: await cq.answer("Pehle Join Karo!", show_alert=True)
  elif data == "rename_help":
    await cq.answer("Kisi bhi file ko /rename newname.mp4 se rename kar sakte ho", show_alert=True)
  else:
    await cq.answer(f"{data} - Bas link bhejo, auto download ho jayega", show_alert=True)

@app.on_message(filters.command("status") & filters.user(ADMIN_ID))
async def status_cmd(client, message):
  await message.reply_text(f"👥 Users: {len(users_set)}")

@app.on_message(filters.text & ~filters.command(["start", "status", "rename"]))
async def process(client, message):
  user_id = message.from_user.id
  add_user(user_id)
  if not await check_join(client, user_id):
    await message.reply_text("First join My Channel ⚠️", reply_markup=get_join_keyboard(), parse_mode=ParseMode.HTML)
    return
  text = message.text.strip()
  is_mf = "mediafire.com" in text
  is_dev = "devuploads.com" in text

  if not (is_mf or is_dev):
    await message.reply_text("Bhai sirf Mediafire / Devuploads link bhejo (4GB tak)", parse_mode=ParseMode.HTML)
    return

  status_msg = await message.reply_text("𝐏ʀᴏsᴇssɪɴɢ...⏳", parse_mode=ParseMode.HTML)
  loop2 = asyncio.get_running_loop()
  local_file = None

  def safe_edit(txt):
    try:
      fut = asyncio.run_coroutine_threadsafe(status_msg.edit_text(txt, parse_mode=ParseMode.HTML), loop2)
      fut.result(timeout=5)
    except: pass

  try:
    if is_mf:
      dlink, fsize, oname = await loop2.run_in_executor(executor, extract_mediafire_link, text)
      err_msg = "Mediafire Link Expired ❌"
    else:
      dlink, fsize, oname = await loop2.run_in_executor(executor, extract_devuploads_link, text)
      err_msg = "Devuploads Link not supported ❌"

    if not dlink:
      await status_msg.edit_text(err_msg, parse_mode=ParseMode.HTML)
      return
    if fsize and fsize > MEDIAFIRE_MAX_SIZE:
      await status_msg.edit_text(f"File Big: {human_readable_size(fsize)}\nLimit: 4 GB", parse_mode=ParseMode.HTML)
      return

    # Rename check - agar user ne pehle se naam set kiya ho
    final_name = rename_dict.get(message.id, oname)
    if len(message.command) > 1: # agar link ke sath naam bhi diya
      pass

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
              txt = f"<b>ᴅᴏᴡɴʟᴏᴀᴅɪɴɢ:</b>\n<code>{bar}</code>\n<b>ꜱɪᴢᴇ:</b> {human_readable_size(downloaded)} | {human_readable_size(total)}\n<b>ᴅᴏɴᴇ:</b> {make_fancy(int(percent))}%"
              safe_edit(txt)

    await loop2.run_in_executor(executor, dl_file)

    upload_start = [time.time()]
    last_up = [0]
    async def upload_progress(current, total):
      now = time.time()
      if now - last_up[0] < 3: return
      last_up[0] = now
      percent = current * 100 / total
      bar = get_progress_bar(percent)
      try: await status_msg.edit_text(f"<b>ᴜᴘʟᴏᴀᴅɪɴɢ:</b>\n<code>{bar}</code>\n<b>{make_fancy(int(percent))}%</b>", parse_mode=ParseMode.HTML)
      except: pass

    await client.send_document(message.chat.id, document=local_file, file_name=final_name, caption=f"<b>✅ {final_name}</b>\n<b>Size: {human_readable_size(fsize)}</b>", progress=upload_progress, force_document=True)
    await status_msg.delete()

  except Exception as e:
    print(e)
    try: await status_msg.edit_text(f"❌ Error: {e}")
    except: pass
  finally:
    safe_remove(local_file)
    # Pella ka 5GB bachane ke liye turant delete
    if local_file and os.path.exists(local_file):
      os.remove(local_file)

async def main():
  await app.start()
  print("Bot Running 4GB + Rename + 6 Buttons ✅")
  await idle()
  await app.stop()

if __name__ == "__main__":
  try: loop.run_until_complete(main())
  except KeyboardInterrupt: print("Bot stopped!")
