import os
from datetime import datetime
from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler
from flask import Flask
import threading
import logging

# Load environment variables
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_CODE = os.getenv("ADMIN_CODE")

REGISTRATION_BOT_URL = os.getenv("REGISTRATION_BOT_URL", "https://t.me/YourRegistrationBot")
CONTACT_EMAIL = os.getenv("CONTACT_EMAIL", "contact@yetal.com")
WEBSITE_URL = os.getenv("WEBSITE_URL", "https://yetal.com")

# ------------------ SAFETY HELPERS (MINIMAL ADDITION) ------------------

def safe_url(url: str):
    url = (url or "").strip()
    if not url.startswith(("http://", "https://", "mailto:")):
        return None
    return url

def safe_mailto(email: str):
    email = (email or "").strip()
    if "@" not in email:
        return None
    return f"mailto:{email}"

# ---------------------------------------------------------------------

# Initialize Flask app
app = Flask(__name__)

@app.route('/')
def home():
    return """<!DOCTYPE html> ... (UNCHANGED HTML) ..."""

# Run Flask in a separate thread
def run_flask():
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

# ------------------ START ------------------

def start(update, context):
    email_url = safe_mailto(CONTACT_EMAIL)
    reg_url = safe_url(REGISTRATION_BOT_URL)
    site_url = safe_url(WEBSITE_URL)

    keyboard = [
        [InlineKeyboardButton("🏆 Rewards Program", callback_data='rewards')],
        [InlineKeyboardButton("💎 Special Discounts", callback_data='discounts')],
        [InlineKeyboardButton("📞 Contact Info", callback_data='contact')],
    ]

    if reg_url:
        keyboard.append([InlineKeyboardButton("📱 Registration Bot", url=reg_url)])

    if email_url:
        keyboard.append([InlineKeyboardButton("📧 Send Email", url=email_url)])

    if site_url:
        keyboard.append([InlineKeyboardButton("🌐 Visit Website", url=site_url)])

    reply_markup = InlineKeyboardMarkup(keyboard)

    update.message.reply_text(
        """✨ *Welcome to Yetal - Ethiopia's Digital Marketplace!* ✨""",
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN
    )

# ------------------ REWARDS ------------------

def show_rewards(update, context):
    query = update.callback_query
    query.answer()

    keyboard = [[InlineKeyboardButton("🔙 Back to Main Menu", callback_data='main_menu')]]
    reg_url = safe_url(REGISTRATION_BOT_URL)
    if reg_url:
        keyboard.append([InlineKeyboardButton("📱 Registration Bot", url=reg_url)])

    query.edit_message_text(
        "🏆 *Yetal Rewards Program* 🏆",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.MARKDOWN
    )

# ------------------ DISCOUNTS ------------------

def show_discounts(update, context):
    query = update.callback_query
    query.answer()

    site_url = safe_url(WEBSITE_URL)
    keyboard = [[InlineKeyboardButton("🔙 Back to Main Menu", callback_data='main_menu')]]
    if site_url:
        keyboard.append([InlineKeyboardButton("🛒 Shop Now", url=site_url)])

    query.edit_message_text(
        "💎 *Special Discounts & Promotions* 💎",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.MARKDOWN
    )

# ------------------ CONTACT ------------------

def show_contact(update, context):
    query = update.callback_query
    query.answer()

    keyboard = [[InlineKeyboardButton("🔙 Back to Main Menu", callback_data='main_menu')]]

    reg_url = safe_url(REGISTRATION_BOT_URL)
    email_url = safe_mailto(CONTACT_EMAIL)

    if reg_url:
        keyboard.append([InlineKeyboardButton("📱 Registration Bot", url=reg_url)])

    if email_url:
        keyboard.append([InlineKeyboardButton("📧 Send Email", url=email_url)])

    query.edit_message_text(
        "📞 *Contact Yetal* 📞",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.MARKDOWN
    )

# ------------------ BACK TO MAIN ------------------

def back_to_main(update, context):
    query = update.callback_query
    query.answer()

    keyboard = [
        [InlineKeyboardButton("🏆 Rewards Program", callback_data='rewards')],
        [InlineKeyboardButton("💎 Special Discounts", callback_data='discounts')],
        [InlineKeyboardButton("📞 Contact Us", callback_data='contact')],
    ]

    reg_url = safe_url(REGISTRATION_BOT_URL)
    site_url = safe_url(WEBSITE_URL)

    if reg_url:
        keyboard.append([InlineKeyboardButton("📱 Registration Bot", url=reg_url)])

    if site_url:
        keyboard.append([InlineKeyboardButton("🌐 Visit Website", url=site_url)])

    query.edit_message_text(
        "✨ *Yetal - Your Digital Marketplace!* ✨",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.MARKDOWN
    )

# ------------------ REGISTER ------------------

def register(update, context):
    reg_url = safe_url(REGISTRATION_BOT_URL)
    keyboard = [[InlineKeyboardButton("🔙 Back", callback_data='main_menu')]]

    if reg_url:
        keyboard.insert(0, [InlineKeyboardButton("🤖 Start Registration", url=reg_url)])

    update.message.reply_text(
        "📱 *Register Your Business on Yetal* 📱",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.MARKDOWN
    )

# ------------------ UNKNOWN ------------------

def unknown(update, context):
    update.message.reply_text("❌ Unknown command. Use /start")

# ------------------ MAIN ------------------

def main():
    threading.Thread(target=run_flask, daemon=True).start()

    logging.basicConfig(level=logging.INFO)

    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("register", register))

    dp.add_handler(CallbackQueryHandler(show_rewards, pattern='^rewards$'))
    dp.add_handler(CallbackQueryHandler(show_discounts, pattern='^discounts$'))
    dp.add_handler(CallbackQueryHandler(show_contact, pattern='^contact$'))
    dp.add_handler(CallbackQueryHandler(back_to_main, pattern='^main_menu$'))

    dp.add_handler(MessageHandler(Filters.command, unknown))

    updater.start_polling(drop_pending_updates=True)
    updater.idle()

if __name__ == "__main__":
    main()
