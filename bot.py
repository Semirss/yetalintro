import os
import time
import logging
from datetime import datetime
from dotenv import load_dotenv
import requests
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode, Bot
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler, Dispatcher
from flask import Flask, render_template_string, request
import threading

# Load environment variables
load_dotenv()
BOT_VERSION = "1.2.0"
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_CODE = os.getenv("ADMIN_CODE")
REGISTRATION_BOT_URL = os.getenv("REGISTRATION_BOT_URL", "https://t.me/YourRegistrationBot")
CONTACT_EMAIL = os.getenv("CONTACT_EMAIL", "contact@yetal.com")
WEBSITE_URL = os.getenv("WEBSITE_URL", "https://yetal.com")
RENDER_EXTERNAL_URL = os.getenv("RENDER_EXTERNAL_URL", "https://yetalads.onrender.com")

# Validate URLs
def validate_url(url):
    """Validate and clean URL"""
    if not url:
        return None
    url = url.strip()
    if url.startswith("http://") or url.startswith("https://"):
        return url
    elif url.startswith("t.me/"):
        return f"https://{url}"
    else:
        return f"https://{url}"

# Validate all URLs
REGISTRATION_BOT_URL = validate_url(REGISTRATION_BOT_URL)
WEBSITE_URL = validate_url(WEBSITE_URL)

# Log startup info
print("=" * 60)
print(f"🚀 Yetal Bot Starting...")
print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"🌐 Render URL: {RENDER_EXTERNAL_URL}")
print(f"🤖 Bot Token: {'✅ Set' if BOT_TOKEN else '❌ Missing'}")
print("=" * 60)

# Initialize Flask app
app = Flask(__name__)

# Store bot instance globally
bot_instance = None
dispatcher_instance = None

@app.route('/')
def home():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Yetal Bot</title>
        <meta http-equiv="refresh" content="30">
        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
            }
            .container {
                background: rgba(255, 255, 255, 0.1);
                backdrop-filter: blur(10px);
                border-radius: 20px;
                padding: 40px;
                margin-top: 50px;
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
            }
            h1 {
                color: #FFD700;
                text-align: center;
                font-size: 2.5em;
                margin-bottom: 30px;
            }
            .status {
                background: rgba(0, 255, 0, 0.2);
                padding: 15px;
                border-radius: 10px;
                margin: 20px 0;
                text-align: center;
                font-size: 1.2em;
            }
            .info-box {
                background: rgba(255, 255, 255, 0.15);
                border-radius: 15px;
                padding: 20px;
                margin: 20px 0;
                border: 1px solid rgba(255, 255, 255, 0.2);
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🚀 Yetal Advertising Bot</h1>
            
            <div class="status">
                ✅ <strong>BOT IS RUNNING AND ACTIVE</strong><br>
                Last updated: <span id="currentTime"></span>
            </div>
            
            <div class="info-box">
                <h2>📢 Bot Status</h2>
                <p><strong>Status:</strong> ✅ Operational 24/7</p>
                <p><strong>Mode:</strong> Webhook (Always Online)</p>
                <p><strong>Uptime:</strong> Continuously monitored by Render</p>
                <p><strong>Last Check:</strong> <span id="lastCheck"></span></p>
            </div>
            
            <div class="info-box">
                <h2>📞 Contact Us</h2>
                <p><strong>Email:</strong> contact@yetal.com</p>
                <p><strong>Telegram:</strong> @YetalSupport</p>
                <p><strong>Phone:</strong> +251 911 234 567</p>
            </div>
            
            <p style="text-align: center; font-size: 0.9em; margin-top: 30px;">
                🔄 This page auto-refreshes every 30 seconds to confirm bot is alive
            </p>
        </div>
        
        <script>
            function updateTime() {
                const now = new Date();
                document.getElementById('currentTime').textContent = now.toLocaleString();
                document.getElementById('lastCheck').textContent = now.toLocaleTimeString();
            }
            updateTime();
            setInterval(updateTime, 1000);
        </script>
    </html>
    """

@app.route('/health')
def health_check():
    """Health check endpoint - Render pings this to keep service alive"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "yetal-bot",
        "bot_status": "active" if bot_instance else "initializing"
    }, 200

@app.route(f'/{BOT_TOKEN}', methods=['POST'])
def webhook():
    """Handle Telegram webhook updates"""
    try:
        # Parse update
        update_data = request.get_json()
        
        if update_data:
            # Create update object
            from telegram import Update
            update = Update.de_json(update_data, bot_instance)
            
            # Process update
            dispatcher_instance.process_update(update)
            
            return 'ok', 200
        else:
            return 'no data', 400
            
    except Exception as e:
        print(f"❌ Webhook error: {e}")
        return 'error', 500
def start(update, context):
    """Send a welcome message with inline keyboard"""
    keyboard = [
        [InlineKeyboardButton("🔥 Daily Subscription Promo", callback_data='daily_promo')],
        [InlineKeyboardButton("ℹ️ About yetal", callback_data='about')],
    ]

    keyboard.append([InlineKeyboardButton("📞 Contact Info", callback_data='contact')])
    
    if WEBSITE_URL and WEBSITE_URL.startswith('http'):
        keyboard.append([InlineKeyboardButton("🌐 Visit Website", url=WEBSITE_URL)])
    if REGISTRATION_BOT_URL and REGISTRATION_BOT_URL.startswith('http'):
        keyboard.append([InlineKeyboardButton("📱 If u are a shop owner use this to register", url=REGISTRATION_BOT_URL)])
    else:
        keyboard.append([InlineKeyboardButton("📱 If u are a shop owner use this to register", callback_data='register_info')])
    
    reply_markup = InlineKeyboardMarkup(keyboard)

    welcome_text = f"""
*✨ hi i'm Yetal*

🔎 *pick your option*

• 🔥 *Daily subscription = daily offers*
• ℹ️ About yetal= Information about yetal
• 📞 Contact us = customer support
• 🌐 Visit website = explore yetals website   
• 📱 if u are a shop owner use this to register = This is for shop owners  


Use the buttons below to explore Yetal 👇
"""

    update.message.reply_text(
        welcome_text,
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN
    )
def show_daily_promo(update, context):
    query = update.callback_query
    query.answer()

    promo_text = """
🔥 *Daily First Subscribers Rush – Win Big with Every Purchase!* 🔥

⏳ *Duration:* 5 Days  
📅 *Runs:* Every Day  

🎯 *How It Works*
• Winners are selected strictly by *subscription time*
• First-come, first-served (exact timestamp)
• Every buyer gets a *15% discount* 🎉

🏆 *Daily Prize Tiers*

🥇 *Top 2 Fastest Subscribers*
🎁 Extra chewing gum + chocolate prize pack  
💰 Value: ~1,000 ETB each

🥈 *Next 3 Subscribers (3–5)*
🍫 Chocolate prize pack  
💰 Value: ~500 ETB each

🥉 *Next 20 Subscribers (6–25)*
🎁 Assorted products or vouchers  
💰 Value: ~250 ETB each

✅ *All Other Subscribers*
• Guaranteed **15% discount** (cash or in-kind)

📌 *Important Notes*
• Total daily winners: **25**
• Unlimited participants
• Prizes reset every day
• 100% transparent & fair (timestamp-based)

🚀 *Subscribe early every day to win BIG!*
"""

    keyboard = [
        [InlineKeyboardButton("📱 Subscribe / Buy Now", url=WEBSITE_URL)],
        [InlineKeyboardButton("🔙 Back to Main Menu", callback_data='main_menu')]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    query.edit_message_text(
        promo_text,
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN
    )

def show_rewards(update, context):
    """Show rewards program information"""
    query = update.callback_query
    query.answer()
    
    rewards_text = """
🌟 *Why Use Yetal?* 🌟

Yetal is built to make searching smarter and business discovery easier.

🔍 *For Users*
• Find products & services instantly  
• Compare offers from different sellers  
• Discover trusted local businesses  
• Save time & effort  

🏪 *For Businesses*
• Advertise without building a website  
• Appear in user searches  
• Reach customers by location & category  
• Affordable promotion plans  

📈 *Why It Works*
• Search-based discovery  
• Real users, real businesses  
• Designed for Ethiopia  

Yetal connects people with what they need — faster.
"""

    
    keyboard = [[InlineKeyboardButton("🔙 Back to Main Menu", callback_data='main_menu')]]
    
    if REGISTRATION_BOT_URL and REGISTRATION_BOT_URL.startswith('http'):
        keyboard.append([InlineKeyboardButton("📱 If u are a shop owner use this to register", url=REGISTRATION_BOT_URL)])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    query.edit_message_text(
        rewards_text,
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN
    )

def show_discounts(update, context):
    """Show current discounts and promotions"""
    query = update.callback_query
    query.answer()
    
    discounts_text = """
💎 *Special Discounts & Promotions* 💎
coming soon...
"""
    
    keyboard = [[InlineKeyboardButton("🔙 Back to Main Menu", callback_data='main_menu')]]
    
    if WEBSITE_URL and WEBSITE_URL.startswith('http'):
        keyboard.append([InlineKeyboardButton("🛒 Shop Now", url=WEBSITE_URL)])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    query.edit_message_text(
        discounts_text,
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN
    )

def show_contact(update, context):
    """Show contact information - SIMPLE VERSION"""
    query = update.callback_query
    query.answer()
    
    contact_text = f"""
📞 *Contact Yetal* 📞

Here's how to reach us:

📧 *Email:* {CONTACT_EMAIL or "contact@yetal.com"}

📱 *Phone:* +251 911 234 567

📱 *Telegram Support:* @YetalSupport

🌐 *Website:* {WEBSITE_URL or "https://yetal.com"}



📧 *For urgent inquiries, please email us directly at:* {CONTACT_EMAIL or "contact@yetal.com"}
"""
    
    keyboard = [
        [InlineKeyboardButton("🔥 Daily Subscription Promo", callback_data='daily_promo')],
        [InlineKeyboardButton("ℹ️ About yetal", callback_data='about')],

    ]
    

    
    keyboard.append([InlineKeyboardButton("📞 Contact Us", callback_data='contact')])
    
    if WEBSITE_URL and WEBSITE_URL.startswith('http'):
        keyboard.append([InlineKeyboardButton("🌐 Visit Website", url=WEBSITE_URL)])
    if REGISTRATION_BOT_URL and REGISTRATION_BOT_URL.startswith('http'):
        keyboard.append([InlineKeyboardButton("📱 If u are a shop owner use this to register", url=REGISTRATION_BOT_URL)])
    else:
        keyboard.append([InlineKeyboardButton("📱 If u are a shop owner use this to register", callback_data='register_info')])  
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    query.edit_message_text(
        contact_text,
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN
    )

def back_to_main(update, context):
    """Return to main menu"""
    query = update.callback_query
    query.answer()
    
    keyboard = [
        [InlineKeyboardButton("🔥 Daily Subscription Promo", callback_data='daily_promo')],
        [InlineKeyboardButton("ℹ️ About yetal", callback_data='about')],

    ]
    

    
    keyboard.append([InlineKeyboardButton("📞 Contact Us", callback_data='contact')])
    
    if WEBSITE_URL and WEBSITE_URL.startswith('http'):
        keyboard.append([InlineKeyboardButton("🌐 Visit Website", url=WEBSITE_URL)])
    if REGISTRATION_BOT_URL and REGISTRATION_BOT_URL.startswith('http'):
        keyboard.append([InlineKeyboardButton("📱 If u are a shop owner use this to register", url=REGISTRATION_BOT_URL)])
    else:
        keyboard.append([InlineKeyboardButton("📱 If u are a shop owner use this to register", callback_data='register_info')])  
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    main_text = """
*✨ hi i'm Yetal*

🔎 *pick your option*

• 🔥 *Daily subscription = daily offers*
• ℹ️ About yetal= Information about yetal
• 📞 Contact us = customer support
• 🌐 Visit website = explore yetals website   
• 📱 if u are a shop owner use this to register = This is for shop owners  


Use the buttons below to explore Yetal 👇
"""
    
    query.edit_message_text(
        main_text,
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN
    )
def showabout(update, context):
    """Detailed information about Yetal - FIXED VERSION"""
    query = update.callback_query
    query.answer()
    
    about_text = """
🔎 *About Yetal – Ethiopia's Digital Search Hub* 🔎

🌍 *Our Purpose*
Yetal was created to solve one problem:
*People struggle to find the right products and services online.*

We make discovery simple.

🎯 *What We Do*
• Index shops, products & services  
• Help users search & compare  
• Promote businesses
• Connect buyers directly with sellers  

🏪 *Who Uses Yetal?*
• Customers searching for options  
• Shops wanting visibility  
• Service providers advertising locally  

🔒 *Trust & Transparency*
• Verified business listings  
• Clear contact information  
• No hidden transactions  
• User-focused design  

🚀 *Our Vision*
To become Ethiopia's most trusted search and discovery platform.
"""

    keyboard = [
        [InlineKeyboardButton("🔥 Daily Subscription Promo", callback_data='daily_promo')],
        [InlineKeyboardButton("ℹ️ About yetal", callback_data='about')],
        [InlineKeyboardButton("📞 Contact Us", callback_data='contact')],
    ]
    
    if WEBSITE_URL and WEBSITE_URL.startswith('http'):
        keyboard.append([InlineKeyboardButton("🌐 Visit Website", url=WEBSITE_URL)])
    if REGISTRATION_BOT_URL and REGISTRATION_BOT_URL.startswith('http'):
        keyboard.append([InlineKeyboardButton("📱 If u are a shop owner use this to register", url=REGISTRATION_BOT_URL)])
    else:
        keyboard.append([InlineKeyboardButton("📱 If u are a shop owner use this to register", callback_data='register_info')])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    query.edit_message_text(
        about_text,
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN
    )
def about_command(update, context):
    """Handle /about command"""
    update.message.reply_text(
        """
🔎 *About Yetal – Ethiopia's Digital Search Hub* 🔎

🌍 *Our Purpose*
Yetal was created to solve one problem:
*People struggle to find the right products and services online.*

We make discovery simple.

🎯 *What We Do*
• Index shops, products & services  
• Help users search & compare  
• Promote businesses
• Connect buyers directly with sellers  

🏪 *Who Uses Yetal?*
• Customers searching for options  
• Shops wanting visibility  
• Service providers advertising locally  

🔒 *Trust & Transparency*
• Verified business listings  
• Clear contact information  
• No hidden transactions  
• User-focused design  

🚀 *Our Vision*
To become Ethiopia's most trusted search and discovery platform.
""",
        parse_mode=ParseMode.MARKDOWN
    )

def showabout(update, context):
    """Handle about button callback - FIXED VERSION"""
    query = update.callback_query
    query.answer()
    
    about_text = """
🔎 *About Yetal – Ethiopia's Digital Search Hub* 🔎

🌍 *Our Purpose*
Yetal was created to solve one problem:
*People struggle to find the right products and services online.*

We make discovery simple.

🎯 *What We Do*
• Index shops, products & services  
• Help users search & compare  
• Promote businesses
• Connect buyers directly with sellers  

🏪 *Who Uses Yetal?*
• Customers searching for options  
• Shops wanting visibility  
• Service providers advertising locally  

🔒 *Trust & Transparency*
• Verified business listings  
• Clear contact information  
• No hidden transactions  
• User-focused design  

🚀 *Our Vision*
To become Ethiopia's most trusted search and discovery platform.
"""

    keyboard = [
        [InlineKeyboardButton("🔥 Daily Subscription Promo", callback_data='daily_promo')],
        [InlineKeyboardButton("ℹ️ About yetal", callback_data='about')],
        [InlineKeyboardButton("📞 Contact Us", callback_data='contact')],
    ]
    
    if WEBSITE_URL and WEBSITE_URL.startswith('http'):
        keyboard.append([InlineKeyboardButton("🌐 Visit Website", url=WEBSITE_URL)])
    if REGISTRATION_BOT_URL and REGISTRATION_BOT_URL.startswith('http'):
        keyboard.append([InlineKeyboardButton("📱 If u are a shop owner use this to register", url=REGISTRATION_BOT_URL)])
    else:
        keyboard.append([InlineKeyboardButton("📱 If u are a shop owner use this to register", callback_data='register_info')])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    query.edit_message_text(
        about_text,
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN
    )
def help_command(update, context):
    """Help command with all available commands"""
    help_text = """
🆘 *Yetal Bot Help* 🆘

Here are all available commands:

📋 *Main Commands:*
• /start - Welcome message and main menu
• /about - Learn about Yetal
• /contact - Contact information
• /register - Get registration bot link
• /help - Show this help message

📞 *Contact Information:*
• Email: yetal@gmail.com
• Phone: +251 911 234 565
• Telegram: @YetalSupport
• Website: https://yetal.com

*We're here 24/7 to assist you!* 🌙
"""
    
    update.message.reply_text(
        help_text,
        parse_mode=ParseMode.MARKDOWN
    )

def register(update, context):
    """Registration information"""
    register_text = """
📱 *Register Your Business on Yetal* 📱

Get discovered by customers searching every day.

🚀 *Why Register?*
• 🔍 Appear in search results  
• 📍 Reach local customers  
• 📢 Promote your services or products  
• 📈 Increase visibility & inquiries  

📝 *How It Works*
1. Register your business  
2. Add products or services   
3. Customers find & contact you directly  

⏱️ Registration takes less than 10 minutes.
"""
    
    keyboard = []
    
    if REGISTRATION_BOT_URL and REGISTRATION_BOT_URL.startswith('http'):
        keyboard.append([InlineKeyboardButton("🤖 Start Registration", url=REGISTRATION_BOT_URL)])
    else:
        keyboard.append([InlineKeyboardButton("🤖 Start Registration", callback_data='register_info')])
    
    keyboard.append([InlineKeyboardButton("📞 Contact Support", callback_data='contact')])
    keyboard.append([InlineKeyboardButton("🔙 Back to Main", callback_data='main_menu')])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    update.message.reply_text(
        register_text,
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN
    )

def register_info(update, context):
    """Show registration info when URL is invalid"""
    query = update.callback_query
    query.answer()
    
    info_text = f"""
📱 *Registration Information* 📱

To register your business on Yetal:

*Registration Bot:* {REGISTRATION_BOT_URL or "Not available"}

*Contact for Help:*
• Email: {CONTACT_EMAIL or "contact@yetal.com"}
• Phone: +251 911 234 567
• Telegram: @YetalSupport

*Website:* {WEBSITE_URL or "https://yetal.com"}

We'll help you get registered as soon as possible!
"""
    
    keyboard = [
        [InlineKeyboardButton("🔙 Back to Main Menu", callback_data='main_menu')],
        [InlineKeyboardButton("📞 Contact Support", callback_data='contact')]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    query.edit_message_text(
        info_text,
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN
    )
def contact_command(update, context):
    contact_text = f"""
📞 *Contact Yetal* 📞

📧 *Email:* {CONTACT_EMAIL}
📱 *Phone:* +251 911 234 567
📱 *Telegram:* @YetalSupport
🌐 *Website:* {WEBSITE_URL}
"""

    update.message.reply_text(
        contact_text,
        parse_mode=ParseMode.MARKDOWN
    )

def unknown(update, context):
    """Handle unknown commands"""
    update.message.reply_text(
        "❌ Sorry, I didn't understand that command.\n\n"
        "Try /start to begin or /help for available commands.",
        parse_mode=ParseMode.MARKDOWN
    )

def setup_bot():
    """Set up Telegram bot with webhook"""
    global bot_instance, dispatcher_instance
    
    try:
        # Create bot instance
        bot_instance = Bot(token=BOT_TOKEN)
        
        # Create updater and dispatcher
        updater = Updater(bot=bot_instance, use_context=True)
        dispatcher_instance = updater.dispatcher
        
        # Add command handlers
        dispatcher_instance.add_handler(CommandHandler("start", start))
        dispatcher_instance.add_handler(CommandHandler("about", about_command))
        dispatcher_instance.add_handler(CommandHandler("help", help_command))
        dispatcher_instance.add_handler(CommandHandler("contact", contact_command))
        # Add callback query handlers
        dispatcher_instance.add_handler(CallbackQueryHandler(show_rewards, pattern='^rewards$'))
        dispatcher_instance.add_handler(CallbackQueryHandler(show_daily_promo, pattern='^daily_promo$'))
        dispatcher_instance.add_handler(CallbackQueryHandler(show_discounts, pattern='^discounts$'))
        dispatcher_instance.add_handler(CallbackQueryHandler(show_contact, pattern='^contact$'))
        dispatcher_instance.add_handler(CallbackQueryHandler(showabout, pattern='^about$'))
        dispatcher_instance.add_handler(CallbackQueryHandler(back_to_main, pattern='^main_menu$'))
        dispatcher_instance.add_handler(CallbackQueryHandler(register_info, pattern='^register_info$'))
        
        # Handle unknown commands
        dispatcher_instance.add_handler(MessageHandler(Filters.command, unknown))
        
        # Set webhook
        webhook_url = f"{RENDER_EXTERNAL_URL}/{BOT_TOKEN}"
        bot_instance.delete_webhook()
        time.sleep(1)
        bot_instance.set_webhook(webhook_url)
        
        print(f"✅ Bot setup complete!")
        print(f"🤖 Bot: @{bot_instance.get_me().username}")
        print(f"🌐 Webhook: {webhook_url}")
        
        return True
        
    except Exception as e:
        print(f"❌ Bot setup failed: {e}")
        return False

def start_flask():
    """Start Flask server"""
    port = int(os.environ.get("PORT", 5000))
    print(f"🌐 Starting Flask server on port {port}...")
    
    # Use production server for Render
    try:
        from waitress import serve
        serve(app, host="0.0.0.0", port=port)
    except ImportError:
        # Fallback to Flask dev server
        app.run(host="0.0.0.0", port=port, debug=False)

def keep_alive():
    """Background thread to keep the service alive"""
    while True:
        try:
            requests.get(f"{RENDER_EXTERNAL_URL}/health", timeout=5)
            print("💓 Keep-alive ping sent")
        except Exception as e:
            print("⚠️ Keep-alive ping failed:", e)

        time.sleep(240) 

def main():
    """Main function to start everything"""
    print("=" * 60)
    print("🚀 YETAL BOT - ULTRA RELIABLE VERSION")
    print("=" * 60)
    
    # Setup logging
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )
    
    # Setup bot
    print("🔄 Setting up Telegram bot...")
    if not setup_bot():
        print("❌ Bot setup failed, but continuing with Flask...")
    
    # Start keep-alive thread
    keep_alive_thread = threading.Thread(target=keep_alive, daemon=True)
    keep_alive_thread.start()
    print("✅ Keep-alive thread started")
    
    # Start Flask server (this will run forever)
    start_flask()

if __name__ == "__main__":
    main()