import logging
import os
import datetime
import pytz  # For timezone handling
from keep_alive import keep_alive
import google.generativeai as genai
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackContext


# Load environment variables
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
OWNER_TELEGRAM_ID = 7141444882  # Replace with your actual Telegram ID

# Set up logging
logging.basicConfig(level=logging.INFO)

# Configure the Gemini AI client
genai.configure(api_key=GEMINI_API_KEY)

# Dictionary to track users filing complaints
pending_complaints = {}

# Dictionary to track user start times
user_start_times = {}

def get_gemini_response(prompt, purpose="general"):
    """Fetch response from Gemini AI using a customer service tone."""
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")

        if purpose == "complaint_check":
            response = model.generate_content(
                f"Classify the following text as a complaint or not a complaint. Respond only with 'complaint' or 'not complaint'.: {prompt}"
            )
            if response and response.text:
                return response.text.strip().lower()
            else:
                return "not complaint"  # Default to not complaint if classification fails

        # Detect specific requests related to NewJeans business
        lowered_prompt = prompt.lower()

        if "what merch do you have" in lowered_prompt or "newjeans merch" in lowered_prompt:
            return (
                "We have a variety of **NewJeans merchandise** available, including:\n"
                "👕 **T-Shirts & Hoodies**\n"
                "📀 **Albums & Photocards**\n"
                "🛍️ **Posters & Lightsticks**\n"
                "💿 **Limited Edition Collectibles**\n\n"
                "Would you like to see the latest catalog? 😊"
            )

        elif "recommend me a newjeans song" in lowered_prompt or "which newjeans song is the best" in lowered_prompt:
            return (
                "If you're new to **NewJeans**, I recommend starting with:\n"
                "🎵 **Hype Boy** - A catchy, feel-good song!\n"
                "🎵 **Ditto** - A soft, nostalgic vibe.\n"
                "🎵 **OMG** - Upbeat and fun!\n\n"
                "Want me to recommend more based on your mood? 😊"
            )

        # Default AI response with Gemini
        response = model.generate_content(
            f"You are a friendly customer service assistant specializing in NewJeans merchandise and music. {prompt}"
        )
        if response and response.text:
            return response.text.strip()
        else:
            return "I'm here to help! Could you provide more details?"

    except Exception as e:
        logging.error(f"Error connecting to Gemini API: {e}")
        return "There seems to be an issue at the moment. Let me check on that for you."

async def start(update: Update, context: CallbackContext):
    """Handle /start command"""
    user_id = update.message.chat_id

    await update.message.reply_text("Hello! Welcome to **NewJeans Customer Service**. How can I assist you today? 🎶🛍️")

    # Check if this is the user's first time
    if user_id not in user_start_times:
        user_start_times[user_id] = datetime.datetime.now()
        await send_initial_promotion(update, context)  # Send immediate promotion
        await schedule_weekly_promotion(context, user_id)  # Schedule weekly job

async def send_weekly_promotion(context: CallbackContext):
    """Send weekly promotion to all users."""
    for user_id in user_start_times:
        try:
            promotion_message = get_promotion_message()
            await context.bot.send_message(chat_id=user_id, text=promotion_message)
            logging.info(f"Sent weekly promotion to user {user_id}")
        except Exception as e:
            logging.error(f"Error sending weekly promotion to user {user_id}: {e}")

async def schedule_weekly_promotion(context: CallbackContext, user_id: int):
    """Schedule the weekly promotion job for a specific user."""
    # Define the desired day of the week (0=Monday, 6=Sunday)
    promotion_day = 6  # Sunday
    # Define the desired time (in hours and minutes)
    promotion_hour = 10
    promotion_minute = 0
    # Get the current time in the user's timezone (replace with actual user timezone if known)
    now = datetime.datetime.now(pytz.timezone('Asia/Singapore'))  # Example timezone

    # Calculate the time for the next promotion
    target_time = now.replace(hour=promotion_hour, minute=promotion_minute, second=0, microsecond=0)
    days_ahead = (promotion_day - now.weekday() + 7) % 7
    if days_ahead == 0 and target_time <= now:
        days_ahead = 7
    target_time += datetime.timedelta(days=days_ahead)

    # Calculate the time difference in seconds
    time_diff_seconds = (target_time - now).total_seconds()

    # Schedule the job
    context.job_queue.run_repeating(
        send_weekly_promotion,
        interval=datetime.timedelta(weeks=1).total_seconds(),  # Reverted back to weekly
        first=time_diff_seconds,
        name=f"weekly_promotion_{user_id}"
    )
    logging.info(f"Scheduled weekly promotion for user {user_id} to start in {time_diff_seconds} seconds")


async def send_initial_promotion(update: Update, context: CallbackContext):
    """Send a promotion immediately when the user starts the bot."""
    promotion_message = get_promotion_message(initial=True)
    await update.message.reply_text(promotion_message)


def get_promotion_message(initial=False):
    """
    Generate the promotion message.

    You should customize this function to provide actual promotional content.
    """
    if initial:
        return (
            "🎉 **Welcome to NewJeans Customer Service!** 🎉\n\n"
            "As a special welcome gift, enjoy 10% off your first merchandise order! Use code 'WELCOME10' at checkout. 🛍️\n\n"
            "Stay tuned for weekly updates on new releases, exclusive offers, and more! 🎶"
        )
    else:
        return (
            "📢 **Weekly NewJeans Update!** 📢\n\n"
            "This week's featured item: Limited Edition 'OMG' Photocards! Collect them all! ✨\n\n"
            "Don't miss out on our ongoing sale: Get 20% off all albums! 💿"
        )

async def help_command(update: Update, context: CallbackContext):
    """Handle /help command"""
    await update.message.reply_text(
        "You can ask me about **NewJeans merchandise, song recommendations, orders, prices, and complaints**.\n\n"
        "🛒 **/merch** - View available merchandise\n"
        "🎵 **/recommend** - Get a NewJeans song recommendation\n"
        "📦 **/orderstatus** - Check your order status\n"
        "📞 **/contact** - Contact support\n"
        "⚠ **/complain** - File a complaint\n"
        "🎁 **/promotions** - View current promotions"
    )

async def contact_command(update: Update, context: CallbackContext):
    """Handle /contact command"""
    await update.message.reply_text("You can reach us at **newjeansupport@gmail.com** or reply here for assistance. 📧")

async def complain_command(update: Update, context: CallbackContext):
    """Handle /complain command"""
    user_id = update.message.chat_id
    pending_complaints[user_id] = True  # Mark this user as making a complaint
    await update.message.reply_text(
        "I'm sorry to hear that! 😢 Please describe your complaint, including the product or issue, "
        "and I will forward it to the team."
    )

async def promotions_command(update: Update, context: CallbackContext):
    """Handle /promotions command"""
    promotion_message = get_promotion_message()  # Get the latest promotion message
    await update.message.reply_text(promotion_message)

async def handle_complaint_request(update: Update, context: CallbackContext):
    """Check if the message is a complaint and ask for details if it is."""
    user_id = update.message.chat_id
    user_message = update.message.text

    # Use Gemini AI to classify the message
    classification = get_gemini_response(user_message, purpose="complaint_check")

    if classification == "complaint":
        pending_complaints[user_id] = True  # Mark this user as making a complaint
        await update.message.reply_text(
            "I'm sorry to hear that! 😢 Please describe your complaint, including the product or issue, "
            "and I will forward it to the team."
        )
    else:
        await update.message.reply_text("I’m here to assist! Could you clarify your request?")

async def handle_complaint_details(update: Update, context: CallbackContext):
    """Process complaint details only if it was classified as a complaint."""
    user = update.message.from_user
    user_id = user.id
    username = user.username  # Get Telegram username
    complaint_text = update.message.text

    # Verify that the user has a pending complaint
    if user_id not in pending_complaints:
        return  # Ignore if no complaint was expected

    # Classify the message again to ensure it's a complaint
    classification = get_gemini_response(complaint_text, purpose="complaint_check")
    if classification != "complaint":
        await update.message.reply_text("It seems like this may not be a complaint. How else can I assist you?")
        return

    del pending_complaints[user_id]  # Remove tracking after submission
    user_identifier = f"@{username}" if username else f"ID: {user_id}"

    # Send complaint to business owner
    owner_message = (
        f"📢 **New Complaint Received!** 📢\n\n"
        f"👤 **User:** {user_identifier}\n"
        f"💬 **Complaint:** {complaint_text}\n\n"
        f"📞 Please reach out to the customer directly."
    )
    await context.bot.send_message(chat_id=OWNER_TELEGRAM_ID, text=owner_message)

    # Confirm submission with user
    await update.message.reply_text(
        "Thank you for your feedback! 🙏 Your complaint has been forwarded to our team, "
        "and we will get back to you as soon as possible."
    )

async def handle_message(update: Update, context: CallbackContext):
    """Handle user messages"""
    user_id = update.message.chat_id
    user_message = update.message.text

    # If the user has a pending complaint, treat their next message as the complaint details
    if user_id in pending_complaints:
        await handle_complaint_details(update, context)
        return

    # Check if the message itself is a complaint
    classification = get_gemini_response(user_message, purpose="complaint_check")
    if classification == "complaint":
        # Send complaint to business owner
        user = update.message.from_user
        username = user.username
        user_identifier = f"@{username}" if username else f"ID: {user_id}"
        owner_message = (
            f"📢 **New Complaint Received!** 📢\n\n"
            f"👤 **User:** {user_identifier}\n"
            f"💬 **Complaint:** {user_message}\n\n"
            f"📞 Please reach out to the customer directly."
        )
        await context.bot.send_message(chat_id=OWNER_TELEGRAM_ID, text=owner_message)
        await update.message.reply_text(
            "Thank you for your feedback! 🙏 Your complaint has been forwarded to our team, "
            "and we will get back to you as soon as possible."
        )
        return

    # General AI response
    bot_response = get_gemini_response(user_message)
    await update.message.reply_text(bot_response)

def main():
    """Start the bot"""
    keep_alive()
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    # Add handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("contact", contact_command))
    app.add_handler(CommandHandler("complain", complain_command)) #add this line
    app.add_handler(CommandHandler("promotions", promotions_command)) #add this line
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Start the bot
    app.run_polling()

if __name__ == "__main__":
    main()