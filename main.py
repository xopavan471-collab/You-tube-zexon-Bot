import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
import yt_dlp
from youtube_transcript_api import YouTubeTranscriptApi
import re

# --- CONFIG ---
BOT_TOKEN = "8693251371:AAErldrjjirTtU27mN4g_QWbinQA-2KHcbk" # 【entity-GitHub¦canonical_name=GitHub】 pe Secret me dalna
logging.basicConfig(level=logging.INFO)

# YouTube ka link se ID nikalne ka function
def get_youtube_id(url):
    pattern = r'(?:v=|\/)([0-9A-Za-z_-]{11}).*'
    match = re.search(pattern, url)
    return match.group(1) if match else None

# --- START COMMAND ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "Welcome to**You Tube All-in-One Bot.\n\n"
        "Bas YouTube ka link bhejo, main options de dunga:\n\n"
        "🎬 Video Download\n"
        "🎵 Audio MP3\n"
        "🖼️ HD Thumbnail\n"
        "📝 Info + Transcript\n\n"
        "Bot ko 24/7 chalane ke liye Render/Railway pe deploy kar dena."
    )
    await update.message.reply_text(text, parse_mode='Markdown')

# --- LINK HANDLE ---
async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    if "youtube.com" not in url and "youtu.be" not in url:
        await update.message.reply_text("please send you tube Link!")
        return

    keyboard = [
        [
            InlineKeyboardButton("Video 720 🎬", callback_data=f"video_720|{url}"),
            InlineKeyboardButton("Video 360 🎬", callback_data=f"video_360|{url}")
        ],
        [
            InlineKeyboardButton("Audio 🎵", callback_data=f"audio|{url}"),
            InlineKeyboardButton("Thumbnail 🖼️", callback_data=f"thumb|{url}")
        ],
        [
            InlineKeyboardButton("📝 Info + Transcript", callback_data=f"info|{url}")
        ]
    ]
    await update.message.reply_text(
        f"✅ Link mil gaya:\n`{url}`\n\nWhat Do you to Download this ?",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

# --- BUTTON ACTIONS ---
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    try:
        action, url = query.data.split("|", 1)
    except:
        return

    await query.edit_message_text(f"Downloading...⏳", parse_mode='Markdown')

    # Common ydl options - bade bots yahi use karte hain stability ke liye
    ydl_opts_base = {
        'quiet': True,
        'no_warnings': True,
        'noplaylist': True,
    }

    try:
        if "video" in action:
            height = 720 if "720" in action else 360
            ydl_opts = {
                **ydl_opts_base,
                'format': f'bestvideo[height<={height}]+bestaudio/best[height<={height}]',
                'outtmpl': '/tmp/%(title)s.%(ext)s',
                'merge_output_format': 'mp4'
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                file_path = ydl.prepare_filename(info)

            await context.bot.send_document(
                chat_id=query.message.chat_id,
                document=open(file_path, 'rb'),
                caption=f"🎬 {info.get('title')}"
            )
            os.remove(file_path)

        elif action == "audio":
            ydl_opts = {
                **ydl_opts_base,
                'format': 'bestaudio/best',
                'outtmpl': '/tmp/%(title)s.%(ext)s',
                'postprocessors': [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3','preferredquality': '192'}]
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                file_path = ydl.prepare_filename(info).rsplit(".", 1)[0] + ".mp3"

            await context.bot.send_audio(
                chat_id=query.message.chat_id,
                audio=open(file_path, 'rb'),
                title=info.get('title')
            )
            os.remove(file_path)

        elif action == "thumb":
            ydl_opts = {**ydl_opts_base, 'skip_download': True}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                thumb_url = info.get('thumbnail')

            await context.bot.send_photo(
                chat_id=query.message.chat_id,
                photo=thumb_url,
                caption=f"🖼️ Thumbnail - {info.get('title')}"
            )

        elif action == "info":
            ydl_opts = {**ydl_opts_base, 'skip_download': True}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)

            video_id = get_youtube_id(url)
            transcript_text = "Transcript available nahi hai."
            try:
                if video_id:
                    transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['en', 'hi'])
                    transcript_text = " ".join([t['text'] for t in transcript[:30]]) + "..."
            except:
                pass

            info_text = (
                f"**Title:** {info.get('title')}\n"
                f"**Channel:** {info.get('uploader')}\n"
                f"**Views:** {info.get('view_count')}\n"
                f"**Duration:** {info.get('duration_string')}\n\n"
                f"**Description:**\n{info.get('description')[:500]}...\n\n"
                f"**Transcript Sample:**\n{transcript_text}"
            )
            await context.bot.send_message(chat_id=query.message.chat_id, text=info_text, parse_mode='Markdown')

    except Exception as e:
        logging.error(f"Error: {e}")
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text=f"❌ Error aa gaya bhai: {str(e)[:300]}\n\nYe video private/age-restricted ho sakta hai ya YouTube ne limit laga di hai. Dusra link try karo."
        )

# --- MAIN ---
def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link))
    app.add_handler(CallbackQueryHandler(button_handler))
    print("Bot started...")
    app.run_polling()

if __name__ == "__main__":
    main()
