import logging
import re
import asyncio
from playwright.async_api import async_playwright
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

# Headless Browser Bypass Engine
async def playwright_bypass(url: str) -> str:
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    async with async_playwright() as p:
        # Launch Headless Chromium Browser
        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"]
        )
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        try:
            # Navigate to shortener link
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            
            # Wait for timers and redirects (up to 12 seconds)
            await asyncio.sleep(10)

            # Extract current final URL
            final_url = page.url

            # If redirected to secondary runner page, wait a bit more
            if "runner" in final_url or "go" in final_url:
                await asyncio.sleep(5)
                final_url = page.url

            await browser.close()
            return final_url

        except Exception as e:
            await browser.close()
            return f"Error: {str(e)}"

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = "⚡ **Headless Chrome Link Bypass Bot** ⚡\n\nMujhe koi bhi shortener link bhejo, main Playwright browser se bypass karke final link nikal dunga!"
    await update.message.reply_text(welcome_text, parse_mode="Markdown")

async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    url = extract_url(text)

    if not ("http://" in url or "https://" in url or "." in url):
        await update.message.reply_text("❌ Kripya ek valid URL bhejein!")
        return

    status_msg = await update.message.reply_text("🌐 **Opening Headless Browser & Bypassing...**\n⏳ *Isme 10-15 seconds lag sakte hain...*", parse_mode="Markdown")

    final_url = await playwright_bypass(url)

    if final_url and final_url.startswith("http") and final_url != url:
        response_text = f"✅ **Link Bypassed Successfully!**\n\n🔗 **Original Link:**\n`{final_url}`"
        keyboard = [[InlineKeyboardButton("Open Final Link 🚀", url=final_url)]]
        await status_msg.edit_text(response_text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await status_msg.edit_text(f"❌ **Bypass Failed / Same URL:**\n`{final_url}`", parse_mode="Markdown")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link))
    app.run_polling()

if __name__ == "__main__":
    main()
    
