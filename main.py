import logging
import re
import aiohttp
from bs4 import BeautifulSoup
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Logging setup
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

# Yahan apna Telegram Bot Token daalein
BOT_TOKEN = "8999902623:AAHCG_nOmigLksRniYj3WVoK0zDYZD8H6O8"

# Clean link extractor helper
def extract_url(text: str) -> str:
    url_pattern = r'https?://[^\s]+'
    match = re.search(url_pattern, text)
    return match.group(0) if match else text.strip()

# Universal Bypass Logic
async def bypass_url(url: str) -> str:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    }
    
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    try:
        async with aiohttp.ClientSession(headers=headers) as session:
            # Step 1: Follow HTTP Redirects
            async with session.get(url, allow_redirects=True, timeout=15) as response:
                final_dest = str(response.url)
                html_text = await response.text()

                # Step 2: Meta Refresh / JS Redirect Check
                soup = BeautifulSoup(html_text, "html.parser")
                meta_refresh = soup.find("meta", attrs={"http-equiv": re.compile(r"refresh", re.I)})
                
                if meta_refresh and "content" in meta_refresh.attrs:
                    content = meta_refresh["content"]
                    if "url=" in content.lower():
                        extracted_url = content.split("url=")[-1].strip("'\"")
                        return await bypass_url(extracted_url)

                return final_dest

    except Exception as e:
        return f"Error: {str(e)}"

# Start Command
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "⚡ **Universal Link Bypass Bot** ⚡\n\n"
        "Mujhe koi bhi shortener link bhejo, main aapko uska original/final destination link nikal kar dunga!"
    )
    keyboard = [[InlineKeyboardButton("Updates Channel 📢", url="https://t.me/Telegram")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(welcome_text, parse_mode="Markdown", reply_markup=reply_markup)

# Message Handler
async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    url = extract_url(text)

    if not ("http://" in url or "https://" in url or "." in url):
        await update.message.reply_text("❌ Kripya ek valid link/URL bhejein!")
        return

    status_msg = await update.message.reply_text("🔎 **Bypassing / Expanding Link...**\n⏳ *Kripya thoda wait karein...*", parse_mode="Markdown")

    final_url = await bypass_url(url)

    if final_url.startswith("http"):
        response_text = (
            "✅ **Link Bypassed Successfully!**\n\n"
            f"🔗 **Original Link:**\n`{final_url}`"
        )
        keyboard = [[InlineKeyboardButton("Open Final Link 🚀", url=final_url)]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await status_msg.edit_text(response_text, parse_mode="Markdown", reply_markup=reply_markup)
    else:
        await status_msg.edit_text(f"❌ **Bypass Failed!**\n\n`{final_url}`", parse_mode="Markdown")

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link))

    print("🚀 Bypass Bot Running Successfully...")
    app.run_polling()

if __name__ == "__main__":
    main()
                                 
