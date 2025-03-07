import logging
import google.generativeai as genai
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext

from dotenv import load_dotenv
import os

load_dotenv()  # Load environment variables from .env file

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


# Set up logging
logging.basicConfig(level=logging.INFO)

# Configure the Gemini AI client
genai.configure(api_key=GEMINI_API_KEY)

def get_gemini_response(prompt):
    """Fetch response from Gemini AI using the correct SDK with a customer service tone."""
    try:
        # Check if the user is asking about Combain
        if "what does combain do" in prompt.lower() or "tell me about combain" in prompt.lower() or "what services does combain provide" in prompt.lower():
            return (
                "Combain offers advanced AI-powered solutions to enhance customer engagement and business efficiency:\n\n"
                "✅ **AI Customer Service Chatbot** – 24/7 support on Telegram, WhatsApp, and your website specifically for your business needs.\n"
                "✅ **Customer Sentiment Analysis** – Get real-time insights from reviews to fine-tune services and products.\n"
                "✅ **Personalized Gmail Responses** – Tailored, quick replies to customer inquiries.\n"
                "✅ **Custom AI Training** – Empower your team with hands-on AI skills.\n"
                "✅ **Continuous AI Support** – Ongoing tech assistance and service updates.\n\n"
                "Would you like to learn more about any of these features? 😊"
            )

        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(f"You are a friendly and helpful customer service assistant. Respond politely and professionally. {prompt}")
        return response.text if response.text else "I'm here to help! Could you provide more details?"
    except Exception as e:
        logging.error(f"Error connecting to Gemini API: {e}")
        return "There seems to be an issue at the moment. Let me check on that for you."

async def start(update: Update, context: CallbackContext):
    """Handle /start command"""
    await update.message.reply_text("Hello! Thanks for reaching out. How can I assist you today?")

async def help_command(update: Update, context: CallbackContext):
    """Handle /help command"""
    await update.message.reply_text(
        "I'm here to assist you! You can use the following commands:\n"
        "/start - Start the bot\n"
        "/help - Get help\n"
        "/about - Learn more about this bot\n"
        "/enquire - Ask a specific question\n"
        "/contact - Get our contact information\n"
        "/authors - Meet the developers"
    )

async def about_command(update: Update, context: CallbackContext):
    """Handle /about command"""
    await update.message.reply_text(
        "This bot is powered by Gemini AI and developed by the Combain team to support small businesses "
        "with customer inquiries. Feel free to ask anything, and I'll be happy to assist!"
    )

async def enquire_command(update: Update, context: CallbackContext):
    """Handle /enquire command"""
    await update.message.reply_text("Please enter your enquiry, and I'll do my best to assist you promptly!")

async def contact_command(update: Update, context: CallbackContext):
    """Handle /contact command"""
    await update.message.reply_text("You can reach us at **CombainAi@gmail.com** for any further inquiries or support. 📧")

async def authors_command(update: Update, context: CallbackContext):
    """Handle /authors command"""
    await update.message.reply_text(
        "Meet the developers behind this bot:\n\n"
        "👨‍💻 **Melson**\n"
        "🔗 LinkedIn: [Your LinkedIn](https://www.linkedin.com/in/melson-wang/)\n"
        "🐙 GitHub: [Your GitHub](https://github.com/Melsonwang1)\n\n"
        "👨‍💻 **Noel**\n"
        "🔗 LinkedIn: [Friend 1 LinkedIn](https://www.linkedin.com/in/noelngzhien/)\n"
        "🐙 GitHub: [Friend 1 GitHub](https://github.com/retartle)\n\n"
        "👨‍💻 **Julian**\n"
        "🔗 LinkedIn: [Friend 2 LinkedIn](https://www.linkedin.com/in/julian-goh-286b1b272/?utm_source=share&utm_campaign=share_via&utm_content=profile&utm_medium=ios_app)\n"
    )

async def handle_message(update: Update, context: CallbackContext):
    """Handle user messages"""
    user_message = update.message.text
    bot_response = get_gemini_response(user_message)
    await update.message.reply_text(bot_response)

def main():
    """Start the bot"""
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Add handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("about", about_command))
    app.add_handler(CommandHandler("enquire", enquire_command))
    app.add_handler(CommandHandler("contact", contact_command))
    app.add_handler(CommandHandler("authors", authors_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Start the bot
    app.run_polling()

if __name__ == "__main__":
    main()