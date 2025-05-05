# srs

LLM Flashcard Generator & Telegram Bot.

This application automatically generates flashcards from knowledge sources (like Notion) using an LLM and delivers them via a Telegram bot. You can also query your flashcards through Telegram commands.

## Features (Planned/Implemented)

*   Automated flashcard generation from Notion.
*   LLM integration via OpenRouter.
*   Storage in SQLite database.
*   Configuration via a simple web dashboard.
*   Scheduled delivery of new flashcards via Telegram.
*   Telegram commands (`/summary`, `/random`) to retrieve flashcards.

## Setting Up a Telegram Bot

To set up the Telegram bot for this application, follow these steps:

1. **Create a Bot with BotFather:**
   - Open Telegram and search for `@BotFather`.
   - Start a chat with BotFather and send the `/start` command.
   - Send the `/newbot` command to create a new bot.
   - Follow the instructions to name your bot and get a bot token. Keep this token secure.

2. **Get Your Chat ID:**
   - Add your bot to a chat or create a new one with your bot.
   - Send a message to your bot.
   - Open a web browser and navigate to `https://api.telegram.org/bot<YourBOTToken>/getUpdates`, replacing `<YourBOTToken>` with the token you received from BotFather.
   - Find the `chat_id` in the response. This is the ID you will use to configure where the bot sends messages.

3. **Configure the Bot in the Application:**
   - Access the web dashboard of this application.
   - Enter the bot token and chat ID in the configuration settings under the Telegram section.
   - Save the settings to update the configuration.

4. **Running the Bot:**
   - Ensure the application is running, and the bot will start polling for updates and respond to commands like `/start`, `/summary`, and `/random`.

## Project Structure

