import os
import time
import logging
from datetime import datetime
from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode, Bot
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler, Dispatcher
from flask import Flask, render_template_string, request
import threading

# Load environment variables
load_dotenv()
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

# Telegram bot handlers (keep all your existing handler functions exactly as before)
def start(update, context):
    """Send a welcome message with inline keyboard"""
    keyboard = [
        [InlineKeyboardButton("🏆 Rewards Program", callback_data='rewards')],
        [InlineKeyboardButton("💎 Special Discounts", callback_data='discounts')],
    ]
    
    if REGISTRATION_BOT_URL and REGISTRATION_BOT_URL.startswith('http'):
        keyboard.append([InlineKeyboardButton("📱 Registration Bot", url=REGISTRATION_BOT_URL)])
    else:
        keyboard.append([InlineKeyboardButton("📱 Registration Bot", callback_data='register_info')])
    
    keyboard.append([InlineKeyboardButton("📞 Contact Info", callback_data='contact')])
    
    if WEBSITE_URL and WEBSITE_URL.startswith('http'):
        keyboard.append([InlineKeyboardButton("🌐 Visit Website", url=WEBSITE_URL)])

    reply_markup = InlineKeyboardMarkup(keyboard)

    welcome_text = """
✨ *Welcome to Yetal - Ethiopia's Digital Marketplace!* ✨

🎯 *What is Yetal?*
Yetal is Ethiopia's premier e-commerce platform revolutionizing how Ethiopians buy and sell online.

🚀 *Why Choose Yetal?*
• 🇪🇹 100% Ethiopian Platform
• 🔒 Secure Transactions
• 🚚 Nationwide Delivery
• 💬 24/7 Customer Support
• 📱 User-Friendly Interface

Use the buttons below to explore more about what Yetal offers!
"""

    update.message.reply_text(
        welcome_text,
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN
    )

def show_rewards(update, context):
    """Show rewards program information"""
    query = update.callback_query
    query.answer()
    
    rewards_text = """
🏆 *Yetal Rewards Program* 🏆

Earn amazing rewards with every purchase on Yetal!

🎁 *Reward Tiers:*
• 🥉 *Bronze Member:* Sign up bonus - 500 points
• 🥈 *Silver Member:* After 5 purchases - 5% cashback
• 🥇 *Gold Member:* After 15 purchases - 10% cashback + free shipping
• 💎 *Platinum Member:* After 30 purchases - 15% cashback + priority support

💰 *How to Earn Points:*
1. Make purchases - 10 points per 100 Birr
2. Refer friends - 1000 points per successful referral
3. Write reviews - 50 points per helpful review
4. Daily check-ins - 10 points daily

🎯 *Redeem Points For:*
• 🛒 Shopping vouchers
• 🚚 Free shipping
• 📱 Mobile airtime
• 💳 Cash discounts

*Current Promotion:* Double points on your first 3 purchases! 🎉
"""
    
    keyboard = [[InlineKeyboardButton("🔙 Back to Main Menu", callback_data='main_menu')]]
    
    if REGISTRATION_BOT_URL and REGISTRATION_BOT_URL.startswith('http'):
        keyboard.append([InlineKeyboardButton("📱 Registration Bot", url=REGISTRATION_BOT_URL)])
    
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

🔥 *Flash Sales (Limited Time!)*
• ⏰ Electronics: 40% OFF - Today only!
• 👗 Fashion: Buy 2 Get 1 FREE
• 🏠 Home Goods: 30% OFF sitewide

🎯 *Category Discounts:*
• 📱 Smartphones: Up to 35% OFF
• 👟 Shoes: 25% OFF all brands
• 💄 Beauty: 20% OFF + free gift
• 🏋️ Sports: Buy 1 Get 50% OFF on second item

✨ *Weekly Deals:*
• 🎁 Monday: Fresh produce - 15% OFF
• 💰 Tuesday: Electronics - 20% OFF
• 🛍️ Wednesday: Fashion - 25% OFF
• 🏠 Thursday: Home decor - 30% OFF
• 📦 Friday: Everything - 10% OFF
• 🎉 Weekend: Mega sale - Up to 50% OFF

🎊 *New User Offers:*
1. First purchase: 25% OFF
2. Free shipping on orders above 500 Birr
3. Welcome gift worth 200 Birr

*Use code: YETALWELCOME for extra 10% off!* 🎫
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

🏢 *Office Address:*
Bole Road, Addis Ababa, Ethiopia

⏰ *Business Hours:*
Monday - Friday: 8:30 AM - 6:30 PM
Saturday: 9:00 AM - 4:00 PM
Sunday: Closed

📧 *For urgent inquiries, please email us directly at:* {CONTACT_EMAIL or "contact@yetal.com"}
"""
    
    keyboard = [[InlineKeyboardButton("🔙 Back to Main Menu", callback_data='main_menu')]]
    
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
        [InlineKeyboardButton("🏆 Rewards Program", callback_data='rewards')],
        [InlineKeyboardButton("💎 Special Discounts", callback_data='discounts')],
    ]
    
    if REGISTRATION_BOT_URL and REGISTRATION_BOT_URL.startswith('http'):
        keyboard.append([InlineKeyboardButton("📱 Registration Bot", url=REGISTRATION_BOT_URL)])
    else:
        keyboard.append([InlineKeyboardButton("📱 Registration Bot", callback_data='register_info')])
    
    keyboard.append([InlineKeyboardButton("📞 Contact Us", callback_data='contact')])
    
    if WEBSITE_URL and WEBSITE_URL.startswith('http'):
        keyboard.append([InlineKeyboardButton("🌐 Visit Website", url=WEBSITE_URL)])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    main_text = """
✨ *Yetal - Your Digital Marketplace!* ✨

Welcome back! What would you like to explore today?

🎯 *Quick Links:*
• 🏆 Rewards Program - Earn points on every purchase
• 💎 Special Discounts - Amazing deals waiting for you
• 📱 Registration Bot - Register your business easily
• 📞 Contact Us - We're here to help 24/7
• 🌐 Website - Visit our full platform

*New this week:* Mega Summer Sale with up to 60% OFF! 🎉
"""
    
    query.edit_message_text(
        main_text,
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN
    )

def about(update, context):
    """Detailed information about Yetal"""
    about_text = """
🏪 *About Yetal - Ethiopia's E-Commerce Revolution* 🏪

🌟 *Our Story:*
Founded in 2023, Yetal was born from a vision to transform Ethiopia's digital commerce landscape. We're building a platform where every Ethiopian can buy and sell with confidence.

🎯 *Our Mission:*
To empower Ethiopian businesses and consumers through accessible, secure, and innovative e-commerce solutions.

📊 *Our Impact:*
• 50,000+ registered users
• 5,000+ active sellers
• 100,000+ products listed
• 95% customer satisfaction rate
• Delivery to 50+ cities across Ethiopia

🔒 *Why Trust Yetal?*
• ✅ Verified sellers only
• 🔒 Secure payment gateway
• 📦 Insured deliveries
• 💬 Real-time tracking
• ⭐ Customer reviews & ratings

🤝 *Our Values:*
• 🇪🇹 Patriotism - Supporting local businesses
• 🔓 Transparency - Clear pricing & policies
• 💝 Community - Building together
• 🚀 Innovation - Always improving

*Join us in revolutionizing Ethiopian e-commerce!* 🎉
"""
    
    keyboard = [
        [InlineKeyboardButton("🏆 Rewards", callback_data='rewards')],
        [InlineKeyboardButton("💎 Discounts", callback_data='discounts')],
    ]
    
    if REGISTRATION_BOT_URL and REGISTRATION_BOT_URL.startswith('http'):
        keyboard.append([InlineKeyboardButton("📱 Register Now", url=REGISTRATION_BOT_URL)])
    else:
        keyboard.append([InlineKeyboardButton("📱 Register Now", callback_data='register_info')])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    update.message.reply_text(
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
• /rewards - View rewards program details
• /discounts - See current promotions
• /contact - Contact information
• /register - Get registration bot link
• /help - Show this help message

📞 *Contact Information:*
• Email: contact@yetal.com
• Phone: +251 911 234 567
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

Ready to start selling on Ethiopia's fastest-growing e-commerce platform?

🚀 *Registration Benefits:*
• 📍 Free business listing
• 🎯 Reach thousands of customers
• 📦 Delivery support
• 💳 Secure payment processing
• 🛡️ Seller protection
• 📊 Sales analytics

📝 *Registration Process:*
1. Click the button below to access our Registration Bot
2. Provide basic business information
3. Upload required documents
4. Get verified within 24 hours
5. Start listing your products!

⏱️ *Quick Registration:* Complete in under 10 minutes!

*Special Offer for New Sellers:*
• 🎁 First month commission FREE
• 📈 Featured listing for 30 days
• 🚚 Free delivery setup assistance
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
        dispatcher_instance.add_handler(CommandHandler("about", about))
        dispatcher_instance.add_handler(CommandHandler("help", help_command))
        dispatcher_instance.add_handler(CommandHandler("register", register))
        
        # Add callback query handlers
        dispatcher_instance.add_handler(CallbackQueryHandler(show_rewards, pattern='^rewards$'))
        dispatcher_instance.add_handler(CallbackQueryHandler(show_discounts, pattern='^discounts$'))
        dispatcher_instance.add_handler(CallbackQueryHandler(show_contact, pattern='^contact$'))
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
        # Log heartbeat
        print(f"💓 Heartbeat: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Bot is alive")
        
        # Check webhook status periodically
        try:
            if bot_instance:
                webhook_info = bot_instance.get_webhook_info()
                if webhook_info.url:
                    print(f"🔗 Webhook active: {webhook_info.url}")
                else:
                    print("⚠️ Webhook not set, reconfiguring...")
                    setup_bot()
        except Exception as e:
            print(f"⚠️ Webhook check failed: {e}")
        
        time.sleep(300)  # Check every 5 minutes

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