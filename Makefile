@VENV_DIR=".venv/bin/python"

install-uv:
	curl -LsSf https://astral.sh/uv/install.sh | sh

venv:
	uv venv .venv 

dep: 
	uv sync

run-dev:
	fastapi dev app/main.py

launch-telegram-bot:
	@VENV_DIR python -m app.telegram_bot.main

lintfix:
	ruff
	isort

.PHONY: install-uv venv dep run-dev launch-telegram-bot lintfix
