import logging
import os
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
import telegram.error
from logger_config import setup_logger, log_error
from text_handler import correct_text
from speech_handler import process_voice_message
from database import get_user_level, set_user_level, add_message, get_conversation, clear_conversation

# Load environment variables
load_dotenv()
TOKEN = os.getenv('TELEGRAM_TOKEN')

# Setup logger
logger = setup_logger('bot', 'bot.log')

# Add this constant near the top of the file after imports
TOPICS = [
    "Daily Life", "Travel", "Food & Cooking", "Movies & TV", 
    "Music", "Sports", "Technology", "Work & Career",
    "Hobbies", "Culture", "Education", "Environment"
]

# Command handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a welcome message when the command /start is issued."""
    user_id = update.effective_user.id
    logger.info(f"User {user_id} started the bot")
    
    keyboard = [
        [
            InlineKeyboardButton("Beginner", callback_data="level_beginner"),
            InlineKeyboardButton("Intermediate", callback_data="level_intermediate"),
        ],
        [InlineKeyboardButton("Advanced", callback_data="level_advanced")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    clear_conversation(user_id)  # Clear any previous conversation
    logger.info(f"Cleared previous conversation for user {user_id}")
    
    await update.message.reply_text(
        "Welcome to English Tutor Bot! I'll chat with you in English and help improve your language skills.\n\n"
        "Please select your English level:",
        reply_markup=reply_markup
    )
    await update.message.reply_text(
        "You can use /topic to choose a conversation topic at any time!"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a help message when the command /help is issued."""
    user_id = update.effective_user.id
    logger.info(f"User {user_id} requested help")
    help_text = """
    I can help you improve your English through conversation! Here's what you can do:
    
    - Just chat with me normally in English! I'll respond and correct any mistakes
    - Send me a voice message and I'll listen, respond, and help improve your speaking
    - Use /topic to choose a specific conversation topic
    - Use /level to change your proficiency level
    - Use /clear to start a new conversation
    - Use /help to see this message again
    """
    await update.message.reply_text(help_text)

async def level_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Change user's English level."""
    user_id = update.effective_user.id
    logger.info(f"User {user_id} requested level change")
    keyboard = [
        [
            InlineKeyboardButton("Beginner", callback_data="level_beginner"),
            InlineKeyboardButton("Intermediate", callback_data="level_intermediate"),
        ],
        [InlineKeyboardButton("Advanced", callback_data="level_advanced")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Select your English level:", reply_markup=reply_markup)

async def clear_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Clear conversation history."""
    user_id = update.effective_user.id
    logger.info(f"User {user_id} cleared conversation history")
    clear_conversation(user_id)
    await update.message.reply_text("Conversation history cleared. Let's start a new chat!")

# Add this new command handler
async def topic_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Let user select a conversation topic."""
    user_id = update.effective_user.id
    logger.info(f"User {user_id} requested topic selection")
    keyboard = [[topic] for topic in TOPICS]
    reply_markup = ReplyKeyboardMarkup(
        keyboard,
        one_time_keyboard=True,
        resize_keyboard=True
    )
    await update.message.reply_text(
        "Choose a topic you'd like to discuss:",
        reply_markup=reply_markup
    )

# Callback query handler
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the callback queries from inline keyboards."""
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()
    
    if query.data.startswith("level_"):
        level = query.data.split("_")[1]
        logger.info(f"User {user_id} set level to {level}")
        set_user_level(user_id, level)
        await query.edit_message_text(f"Your level has been set to: {level.capitalize()}. Let's practice your English!")

# Message handlers
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle user text messages."""
    try:
        user_id = update.message.from_user.id
        user_text = update.message.text
        logger.info(f"Received text message from user {user_id}: {user_text[:50]}...")  # Log first 50 chars
        level = get_user_level(user_id)
        
        # Check if the message is a topic selection
        if user_text in TOPICS:
            logger.info(f"User {user_id} selected topic: {user_text}")
            await update.message.reply_text(
                f"Great! Let's talk about {user_text}. I'll start with a question.",
                reply_markup=ReplyKeyboardRemove()
            )
            # Generate a topic-specific question
            topic_question = correct_text(f"generate_topic_question_{user_text}", level)
            # For topic questions, just get the AI response part without corrections
            if "AI:" in topic_question:
                ai_response = topic_question.split("AI:")[1].split("\n\nCorrected:")[0].strip()
                # Save the AI's question to conversation history
                add_message(user_id, "assistant", ai_response)
                await update.message.reply_text(ai_response)
            return

        # Get conversation history before adding new message
        conversation_history = get_conversation(user_id, limit=5)  # Get last 5 messages
        
        # Add user message to conversation history
        add_message(user_id, "user", user_text)
        
        # Get AI response and correction with conversation history
        response = correct_text(user_text, level, conversation_history)
        
        # Split the response into AI reply and correction parts
        ai_part = ""
        correction_part = ""
        
        if "AI:" in response and "Corrected:" in response:
            parts = response.split("\n\nCorrected:")
            ai_part = parts[0].split("AI:")[1].strip()
            correction_part = parts[1].strip()
            
            # Only show correction if there are actual changes
            if "Better:" in correction_part:
                # Format the response with the AI reply first, then the educational correction
                formatted_response = (
                    f"{ai_part}\n\n"
                    f"💡 Let me help you improve your English:\n"
                    f"{correction_part}"
                )
            else:
                formatted_response = ai_part
        else:
            formatted_response = response
        
        # Add AI response to conversation history
        add_message(user_id, "assistant", ai_part)
        
        await update.message.reply_text(formatted_response)
    
    except telegram.error.TimedOut:
        log_error(logger, f"Telegram timeout error for user {user_id}")
        try:
            await update.message.reply_text(
                "I'm sorry, I experienced a timeout. Please try sending your message again."
            )
        except:
            pass
    
    except Exception as e:
        log_error(logger, f"Error handling text from user {user_id}: {str(e)}")
        try:
            await update.message.reply_text(
                "I'm sorry, something went wrong. Please try again."
            )
        except:
            pass

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle user voice messages."""
    try:
        user_id = update.message.from_user.id
        logger.info(f"Received voice message from user {user_id}")
        level = get_user_level(user_id)
        
        # First, let the user know we're processing their audio
        processing_msg = await update.message.reply_text("Processing your voice message...")
        
        # Get the voice message file
        voice_file = await update.message.voice.get_file()
        os.makedirs("voice_messages", exist_ok=True)
        file_path = f"voice_messages/{update.message.voice.file_id}.ogg"
        await voice_file.download_to_drive(file_path)
        
        # Process the voice message and get transcription, correction, and AI response
        result, corrected_audio_path = process_voice_message(file_path, level)
        
        # Add transcribed message to conversation history
        if "I heard:" in result:
            transcribed_text = result.split("I heard:")[1].split("\n\nAI:")[0].strip()
            add_message(user_id, "user", transcribed_text)
        
        # Add AI response to conversation history
        if "AI:" in result:
            ai_response = result.split("AI:")[1].split("\n\nCorrected:")[0].strip()
            add_message(user_id, "assistant", ai_response)
        
        # Delete the processing message
        await context.bot.delete_message(chat_id=update.message.chat_id, 
                                       message_id=processing_msg.message_id)
        
        # Send text response
        await update.message.reply_text(result)
        
        # If there's a correction, send the corrected pronunciation as voice
        if corrected_audio_path:
            logger.info(f"Generated correction audio for user {user_id}")
            with open(corrected_audio_path, 'rb') as audio:
                await update.message.reply_voice(
                    voice=audio,
                    caption="Here's how to pronounce it correctly 🎯"
                )
            os.remove(corrected_audio_path)  # Clean up the correction audio file
        
        # Clean up the original file
        os.remove(file_path)
        
        logger.info(f"Completed voice message processing for user {user_id}")

    except Exception as e:
        log_error(logger, f"Error handling voice from user {user_id}: {str(e)}")
        try:
            await update.message.reply_text(
                "I'm sorry, I had trouble processing your voice message. Please try again."
            )
        except:
            pass

def main() -> None:
    """Start the bot."""
    try:
        # Log startup
        logger.info("Starting English Tutor Bot...")
        
        # Create the Application
        application = Application.builder().token(TOKEN).build()
        logger.info("Bot application created")

        # Add handlers
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("level", level_command))
        application.add_handler(CommandHandler("clear", clear_command))
        application.add_handler(CommandHandler("topic", topic_command))
        application.add_handler(CallbackQueryHandler(button))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
        application.add_handler(MessageHandler(filters.VOICE, handle_voice))
        logger.info("All handlers registered")

        # Start the Bot
        logger.info("Bot is starting polling...")
        application.run_polling()
        
    except Exception as e:
        log_error(logger, f"Failed to start bot: {str(e)}")
        raise

if __name__ == '__main__':
    main()