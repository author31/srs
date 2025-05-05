VENV_DIR=".venv/bin"
PYTHON="$(VENV_DIR)/python"
PIP="$(VENV_DIR)/pip"

install-uv:
	@command -v uv >/dev/null 2>&1 || { \
		echo "Installing uv..."; \
		curl -LsSf https://astral.sh/uv/install.sh | sh; \
	}

# Create a virtual environment
venv:
	uv venv .venv

# Install dependencies from pyproject.toml
dep: venv
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
	$(PYTHON) -m isort .
	$(PYTHON) -m ruff check --fix .

.PHONY: install-uv venv dep run-dev launch-telegram-bot lint lintfix
