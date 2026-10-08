import logging
import re
import aiohttp
from bs4 import BeautifulSoup
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

BOT_TOKEN = "8999902623:AAHCG_nOmigLksRniYj3WVoK0zDYZD8H6O8"

def extract_url(text: str) -> str:
    url_pattern = r'https?://[^\s]+'
    match = re.search(url_pattern, text)
    return match.group(0) if match else text.strip()

# Primary method: External Bypass API
async def api_bypass(url: str) -> str:
    try:
        api_endpoint = f"https://api.bypass.vip/bypass?url={url}"
        async with aiohttp.ClientSession() as session:
            async with session.get(api_endpoint, timeout=20) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if data.get("status") == "success" and data.get("destination"):
                        return data.get("destination")
    except Exception:
        pass
    return None

# Fallback method: Direct HTTP / Meta Redirects
async def fallback_bypass(url: str) -> str:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    }
    try:
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(url, allow_redirects=True, timeout=15) as response:
                final_dest = str(response.url)
                html_text = await response.text()
                soup = BeautifulSoup(html_text, "html.parser")
                meta_refresh = soup.find("meta", attrs={"http-equiv": re.compile(r"refresh", re.I)})
                
                if meta_refresh and "content" in meta_refresh.attrs:
                    content = meta_refresh["content"]
                    if "url=" in content.lower():
                        extracted_url = content.split("url=")[-1].strip("'\"")
                        return await fallback_bypass(extracted_url)

                return final_dest
    except Exception as e:
        return f"Error: {str(e)}"

# Main Bypass Logic
async def smart_bypass(url: str) -> str:
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    # Try API first
    bypassed = await api_bypass(url)
    if bypassed and bypassed != url:
        return bypassed

    # Fallback to direct redirect
    return await fallback_bypass(url)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = "⚡ **Zexon Link Bypass Bot** ⚡\n\nMujhe koi bhi shortener link bhejo, main destination link nikal dunga!"
    await update.message.reply_text(welcome_text, parse_mode="Markdown")

async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    url = extract_url(text)

    if not ("http://" in url or "https://" in url or "." in url):
        await update.message.reply_text("❌ Kripya ek valid link bhejein!")
        return

    status_msg = await update.message.reply_text("🔎 **Bypassing Link...**\n⏳ *Thoda wait karein...*", parse_mode="Markdown")

    final_url = await smart_bypass(url)

    if final_url and final_url.startswith("http") and final_url != url:
        response_text = f"✅ **Link Bypassed Successfully!**\n\n🔗 **Original Link:**\n`{final_url}`"
        keyboard = [[InlineKeyboardButton("Open Final Link 🚀", url=final_url)]]
        await status_msg.edit_text(response_text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await status_msg.edit_text("❌ **Bypass Failed!** Ye shortener protected/complex script use kar raha hai.", parse_mode="Markdown")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link))
    app.run_polling()

if __name__ == "__main__":
    main()
    
