.PHONY: help install test run-api run-listener test-tavily test-mic lint format secrets-push secrets-pull secrets-list

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-20s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Install dependencies
	@echo "📦 Installing dependencies..."
	uv sync

install-audio-macos: ## Install audio dependencies on macOS
	@echo "📦 Installing audio dependencies for macOS..."
	brew install portaudio
	uv pip install pyaudio rnnoise-python

install-audio-ubuntu: ## Install audio dependencies on Ubuntu
	@echo "📦 Installing audio dependencies for Ubuntu..."
	sudo apt install portaudio19-dev
	uv pip install pyaudio rnnoise-python

test: ## Run all tests
	@echo "🧪 Running tests..."
	uv run pytest

test-unit: ## Run unit tests only
	@echo "🧪 Running unit tests..."
	uv run pytest tests/unit

test-integration: ## Run integration tests only
	@echo "🧪 Running integration tests..."
	uv run pytest tests/integration

test-tavily: ## Test Tavily integration
	@echo "🧪 Testing Tavily integration..."
	uv run python scripts/test_tavily_pipeline.py

test-mic: ## Test microphone pipeline
	@echo "🧪 Testing microphone pipeline..."
	uv run python scripts/test_mic_pipeline.py

run-api: ## Run the FastAPI server
	@echo "🚀 Starting FastAPI server..."
	cd .. && (uv run --directory warmth uvicorn warmth.apps.api.main:app --reload --port 8000 || PYTHONPATH=. warmth/.venv/bin/uvicorn warmth.apps.api.main:app --reload --host 0.0.0.0 --port 8000)

run-meet-local: ## Run the lightweight MEET test server
	@echo "🚀 Starting MEET local server..."
	cd .. && uv run --directory warmth python warmth/scripts/serve_meet_local.py

run-gmail-mcp: ## Run the Gmail MCP bridge (port 3000)
	@echo "📬 Starting Gmail MCP bridge..."
	cd .. && PYTHONPATH=. warmth/.venv/bin/uvicorn warmth.services.google_mcp_server.main:app --reload --host 0.0.0.0 --port $${GOOGLE_MCP_PORT:-3000}

setup-gmail-mcp: ## OAuth setup for getwarmth@gmail.com Gmail MCP
	@echo "🔐 Gmail OAuth setup..."
	cd .. && PYTHONPATH=. warmth/.venv/bin/python warmth/scripts/setup_gmail_oauth.py

install-gmail: ## Install Gmail MCP Python dependencies
	@echo "📦 Installing Gmail MCP deps..."
	cd .. && uv pip install --directory warmth google-api-python-client google-auth-oauthlib google-auth-httplib2

run-listener: ## Run the listener service
	@echo "🚀 Starting listener service..."
	uv run python apps/listener/main.py

secrets-push: ## Push local .env secrets to Google Secret Manager
	@echo "🔐 Pushing secrets to Google Secret Manager..."
	uv run python scripts/secrets_sync.py push --env-file .env

secrets-pull: ## Pull team secrets from Google Secret Manager into .env
	@echo "🔐 Pulling secrets from Google Secret Manager..."
	uv run python scripts/secrets_sync.py pull --env-file .env

secrets-list: ## List secrets stored in Google Secret Manager
	@echo "🔐 Listing secrets in Google Secret Manager..."
	uv run python scripts/secrets_sync.py list

lint: ## Run linting
	@echo "🔍 Running linting..."
	uv run ruff check .

format: ## Format code
	@echo "✨ Formatting code..."
	uv run black .
	uv run ruff check --fix .

typecheck: ## Run type checking
	@echo "🔍 Running type checking..."
	uv run mypy .

dev: ## Run development setup (install + format + lint)
	@echo "🛠️  Running development setup..."
	make install
	make format
	make lint

clean: ## Clean up cache files
	@echo "🧹 Cleaning up..."
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete