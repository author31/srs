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

## First-Time Setup

To set up the application for the first time, follow these steps:

1. **Install uv (if not already installed):**
   - Run `make install-uv` to install uv, a fast Python package installer and resolver.

2. **Create a Virtual Environment:**
   - Run `make venv` to create a virtual environment using uv.

3. **Install Dependencies:**
   - Run `make dep` to install the required dependencies from pyproject.toml into the virtual environment.

4. **Run the Development Server:**
   - Run `make run-dev` to start the FastAPI development server for the web dashboard.

5. **Launch the Telegram Bot:**
   - Run `make launch-telegram-bot` to start the Telegram bot in a separate terminal or background process.

6. **Linting and Code Style:**
   - Run `make lint` to check the codebase for style and errors.
   - Run `make lintfix` to automatically fix linting issues where possible.

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

## Testing

This project includes integration tests for the Notion API and related services. These tests ensure that the application correctly interacts with external APIs and manages data in the database.

### Prerequisites
- Ensure you have completed the "First-Time Setup" steps to install dependencies.
- Install any additional testing dependencies if not already included, such as `pytest` and `pytest-asyncio`

### Setting Up Test Environment
- Create a file named `.env.integration.test` in the root of the project.
- Add the following environment variables to `.env.integration.test`. Replace the placeholders with your actual values:
  ```
  NOTION_API_KEY=your_notion_api_key_here
  TEST_NOTION_PAGE_ID=your_test_page_id_here
  TEST_NOTION_DATABASE_ID=your_test_database_id_here
  ```
  - These variables are required for the tests to run without skipping. The `NOTION_API_KEY` should be a valid key from your Notion account.

### Running the Tests
- Execute the tests using pytest:
  ```
  pytest tests/
  ```
- To enable debug logging, set the `DEBUG` environment variable to `True` before running tests:
  ```
  DEBUG=True pytest tests/
  ```
- This will run the asynchronous tests and display detailed logs if configured.

### Notes
- Tests are located in the `tests/` directory.
- They use pytest-asyncio for handling asynchronous code.
- If tests are skipped, check your `.env.integration.test` file for missing variables.
- Run tests in your virtual environment to avoid conflicts.

## Project Structure

