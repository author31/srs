# Makefile for managing the SRS Flashcard Generator project

VENV_DIR=".venv/bin"
PYTHON="$(VENV_DIR)/python"
PIP="$(VENV_DIR)/pip"

# Install uv, a fast Python package installer and resolver
install-uv:
	curl -LsSf https://astral.sh/uv/install.sh | sh

# Create a virtual environment
venv:
	uv venv .venv

# Install dependencies from pyproject.toml
dep: venv
	$(PIP) install -U pip
	uv sync

# Run the FastAPI development server
run-dev: dep
	$(PYTHON) -m fastapi dev app/main.py

# Launch the Telegram bot
launch-telegram-bot: dep
	$(PYTHON) -m app.telegram_bot.main

# Lint the codebase for style and errors
lint: dep
	$(PYTHON) -m ruff check .

# Fix linting issues automatically
lintfix: dep
	$(PYTHON) -m ruff check --fix .
	$(PYTHON) -m isort .

.PHONY: install-uv venv dep run-dev launch-telegram-bot lint lintfix
