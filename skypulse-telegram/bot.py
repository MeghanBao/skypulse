"""
SkyPulse Telegram Bot - Enhanced Version
AI-powered flight deal notification bot with full features
"""
import os
import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters, ConversationHandler

# Configuration
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', 'YOUR_BOT_TOKEN')

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Conversation states
DESTINATION, MAX_PRICE, TRAVEL_DATE, NOTIFICATION_PREF = range(4)

# In-memory user preferences (in production, use database)
user_preferences = {}

# Sample deals data
SAMPLE_DEALS = [
    {"route": "Berlin → Paris", "price": "€89", "date": "2026-03-15", "airline": "EasyJet"},
    {"route": "Munich → London", "price": "€120", "date": "2026-03-20", "airline": "British Airways"},
    {"route": "Frankfurt → NYC", "price": "€450", "date": "2026-04-01", "airline": "Lufthansa"},
    {"route": "Berlin → Barcelona", "price": "€95", "date": "2026-03-18", "airline": "Vueling"},
    {"route": "Hamburg → Amsterdam", "price": "€65", "date": "2026-03-22", "airline": "KLM"},
]

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    welcome_text = f"""
✈️ Welcome to SkyPulse, {user.first_name}!

I'm your AI-powered flight deal assistant.

What I can do:
🔍 Search for cheap flights
📊 Analyze price trends
🔔 Send you deal notifications
💰 Predict best buy timing

Commands:
/start - This menu
/search - Search flights
/subscribe - Get deal alerts
/deals - View latest deals
/alerts - Manage your alerts
/price - Check price prediction
/profile - Your profile
/help - More info

Try: /deals to see current offers!
"""
    await update.message.reply_text(welcome_text)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = """
📖 SkyPulse Commands

🔍 /search - Search for specific routes
📊 /price - Get price prediction for a route
🔔 /subscribe - Set up flight alerts
🔕 /unsubscribe - Remove all alerts
📋 /alerts - View/manage your alerts
💼 /profile - View your preferences
📢 /deals - Latest flight deals

Natural Language:
You can also just tell me what you want!
Examples:
• "Flights to Paris next month"
• "Berlin to London under 150 euros"
• "Notify me about weekend trips"
"""
    await update.message.reply_text(help_text)

async def search_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start conversation to search flights"""
    await update.message.reply_text("🔍 Where do you want to fly?\n\nSend me your destination (e.g., Paris, London, NYC)")
    return DESTINATION

async def destination_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle destination input"""
    destination = update.message.text
    context.user_data['destination'] = destination
    
    await update.message.reply_text(f"Great! When do you want to travel? (e.g., March 2026, next weekend)")
    return TRAVEL_DATE

async def date_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle travel date input"""
    date = update.message.text
    context.user_data['date'] = date
    
    await update.message.reply_text("What's your maximum budget? (e.g., 200 EUR)")
    return MAX_PRICE

async def price_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle price input and show results"""
    price = update.message.text
    destination = context.user_data.get('destination', 'Unknown')
    date = context.user_data.get('date', 'Any')
    
    # Find matching deals (simplified)
    deals_text = f"🔍 Results for flights to {destination}:\n\n"
    
    keyboard = [[InlineKeyboardButton("🔔 Subscribe to Alerts", callback_data=f"subscribe_{destination}")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"📭 No exact matches found for {destination}.\n\n"
        f"Try /deals for current deals or /subscribe to get notified!",
        reply_markup=reply_markup
    )
    return ConversationHandler.END

async def deals_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show latest deals with inline buttons"""
    deals_text = "✈️ Today's Best Flight Deals:\n\n"
    
    for i, deal in enumerate(SAMPLE_DEALS, 1):
        deals_text += f"{i}. {deal['route']}\n"
        deals_text += f"   💰 {deal['price']} | 📅 {deal['date']} | ✈️ {deal['airline']}\n\n"
    
    keyboard = [
        [InlineKeyboardButton("🔔 Subscribe", callback_data="subscribe_deals")],
        [InlineKeyboardButton("🔄 Refresh", callback_data="refresh_deals")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(deals_text, reply_markup=reply_markup)

async def price_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check price prediction for a route"""
    await update.message.reply_text("""
📊 Price Prediction

Which route do you want to check?
Example: Berlin-Paris, Munich-London
""")

async def subscribe_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Set up subscription with inline keyboard"""
    keyboard = [
        [InlineKeyboardButton("✈️ Flights", callback_data="pref_flights")],
        [InlineKeyboardButton("🏨 Hotels", callback_data="pref_hotels")],
        [InlineKeyboardButton("Both", callback_data="pref_both")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🔔 What do you want to be notified about?",
        reply_markup=reply_markup
    )

async def alerts_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user's current alerts"""
    user_id = update.effective_user.id
    prefs = user_preferences.get(user_id, {})
    
    if not prefs:
        await update.message.reply_text(
            "📋 You have no active alerts.\n\nUse /subscribe to create one!"
        )
    else:
        alerts_text = "📋 Your Active Alerts:\n\n"
        for alert in prefs.get('alerts', []):
            alerts_text += f"• {alert['destination']} under €{alert['price']}\n"
        
        await update.message.reply_text(alerts_text)

async def profile_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user profile"""
    user = update.effective_user
    user_id = update.effective_user.id
    prefs = user_preferences.get(user_id, {})
    
    profile_text = f"""
👤 Your Profile

Name: {user.first_name} {user.last_name or ''}
Username: @{user.username or 'Not set'}
Language: {prefs.get('language', 'EN')}

📊 Statistics:
Subscriptions: {len(prefs.get('alerts', []))}
Notifications: {prefs.get('notifications', 0)}

Preferences:
Language: {prefs.get('language', 'English')}
Notifications: {prefs.get('notify_via', 'Telegram')}
"""
    await update.message.reply_text(profile_text)

async def unsubscribe_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Unsubscribe from all alerts"""
    user_id = update.effective_user.id
    if user_id in user_preferences:
        user_preferences[user_id] = {'alerts': [], 'notifications': 0}
    
    await update.message.reply_text("✅ You've been unsubscribed from all alerts.")

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle inline button callbacks"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    
    if query.data == "subscribe_deals":
        if user_id not in user_preferences:
            user_preferences[user_id] = {'alerts': [], 'notifications': 0}
        
        await query.edit_message_text("✅ Subscribed to deal alerts!\n\nYou'll be notified when great deals appear.")
    
    elif query.data == "refresh_deals":
        await query.edit_message_text("🔄 Refreshing deals...")
        await deals_command(update, context)
    
    elif query.data.startswith("subscribe_"):
        destination = query.data.replace("subscribe_", "")
        if user_id not in user_preferences:
            user_preferences[user_id] = {'alerts': [], 'notifications': 0}
        
        user_preferences[user_id]['alerts'].append({
            'destination': destination,
            'price': 500,
            'created_at': datetime.now().isoformat()
        })
        
        await query.edit_message_text(f"✅ Subscribed to alerts for {destination}!")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle natural language input"""
    text = update.message.text.lower()
    
    if any(w in text for w in ['paris', 'london', 'berlin', 'tokyo']):
        await update.message.reply_text(f"I see you're interested in flights to {update.message.text}!\n\nTry /search for detailed search or /deals for current deals!")
    elif 'deal' in text or 'cheap' in text:
        await update.message.reply_text("Check out /deals for current offers!")
    else:
        await update.message.reply_text("I can help you find flights!\n\nTry:\n• /search - Search flights\n• /deals - View deals\n• /subscribe - Get alerts")

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Update {update} caused error {context.error}")

def main():
    """Run the bot"""
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Conversation handler for /search
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("search", search_command)],
        states={
            DESTINATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, destination_received)],
            TRAVEL_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, date_received)],
            MAX_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, price_received)]
        },
        fallbacks=[CommandHandler("cancel", lambda u, c: u.message.reply_text("Cancelled.") or ConversationHandler.END)]
    )
    
    # Add handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("deals", deals_command))
    application.add_handler(CommandHandler("price", price_command))
    application.add_handler(CommandHandler("subscribe", subscribe_command))
    application.add_handler(CommandHandler("unsubscribe", unsubscribe_command))
    application.add_handler(CommandHandler("alerts", alerts_command))
    application.add_handler(CommandHandler("profile", profile_command))
    application.add_handler(conv_handler)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(CallbackQueryHandler(button_callback))
    application.add_error_handler(error_handler)
    
    logger.info("SkyPulse Bot starting...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
