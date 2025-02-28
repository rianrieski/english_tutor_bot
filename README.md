# English Tutor Bot

A Telegram bot that helps users improve their English through natural conversation, with voice message support and personalized corrections.

## Features

- 🗣️ Text and voice chat support
- 📝 Real-time language corrections
- 🎯 Level-based responses (Beginner/Intermediate/Advanced)
- 🗂️ Topic-based conversations
- 🔊 Pronunciation guidance with audio examples
- 📚 Conversation history tracking

## Commands

- `/start` - Begin using the bot and set your English level
- `/level` - Change your English proficiency level
- `/topic` - Choose a conversation topic
- `/clear` - Clear conversation history
- `/help` - Show help message

## Setup

1. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

2. Create a `.env` file with your OpenAI API key, Telegram bot token, and Database Path:

   ```bash
   OPENAI_API_KEY=<your_openai_api_key>
   TELEGRAM_BOT_TOKEN=<your_telegram_bot_token>
   DATABASE_PATH=<path_to_your_database>
   ```

3. Run the bot:
   ```bash
   python main.py
   ```

## Usage

1. Start the conversation with `/start`
2. Set your English proficiency level using `/level`
3. Choose a conversation topic using `/topic`
4. Send text messages or voice messages to the bot
5. Receive real-time corrections and personalized responses

## Conversation History

The bot keeps track of the conversation history for each user. You can clear the history using `/clear`.

## Requirements

- Python 3.11+
- FFmpeg (for voice message processing)
- SQLite3

## Technical Stack

- python-telegram-bot
- OpenAI GPT-4
- SpeechRecognition
- gTTS (Google Text-to-Speech)
- SQLite3 for conversation storage

## License

MIT
