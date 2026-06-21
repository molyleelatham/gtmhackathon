.PHONY: help install test run-api run-listener test-tavily test-mic lint format secrets-push secrets-pull secrets-list smoke-docker deploy-rules

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

test: ## Run all tests (excluding external APIs)
	@echo "🧪 Running tests..."
	uv run pytest -m "not external"

test-unit: ## Run unit tests only
	@echo "🧪 Running unit tests..."
	uv run pytest tests/unit -m unit

test-integration: ## Run integration tests only
	@echo "🧪 Running integration tests..."
	uv run pytest tests/integration -m integration

test-cov: ## Run tests with coverage report
	@echo "🧪 Running tests with coverage..."
	uv run pytest -m "not external" --cov=apps --cov=packages --cov=infra --cov-report=term-missing

test-external: ## Run external API integration tests (requires secrets)
	@echo "🧪 Running external integration tests..."
	uv run pytest -m external

test-web: ## Run web Vitest + Playwright E2E
	@echo "🧪 Running web tests..."
	cd web && npm run test && npm run test:e2e

test-ios: ## Run iOS unit + UI tests
	@echo "🧪 Running iOS tests..."
	cd iOS/Warmth-iOS && xcodegen generate && xcodebuild test -scheme Warmth -destination 'platform=iOS Simulator,name=iPhone 17 Pro' -quiet

test-all: test test-web test-ios ## Run Python, web, and iOS test suites

test-tavily: ## Test Tavily integration
	@echo "🧪 Testing Tavily integration..."
	uv run python scripts/test_tavily_pipeline.py

test-mic: ## Test microphone pipeline
	@echo "🧪 Testing microphone pipeline..."
	uv run python scripts/test_mic_pipeline.py

run-api: ## Run the FastAPI server
	@echo "🚀 Starting FastAPI server..."
	uv run python scripts/run_dev_api.py

run-meet-local: ## Run the lightweight MEET test server
	@echo "🚀 Starting MEET local server..."
	cd .. && uv run --directory warmth python warmth/scripts/serve_meet_local.py

run-gmail-mcp: ## Run the Gmail MCP bridge (port 3000)
	@echo "📬 Starting Gmail MCP bridge..."
	cd .. && PYTHONPATH=. warmth/.venv/bin/uvicorn warmth.services.google_mcp_server.main:app --reload --host 0.0.0.0 --port $${GOOGLE_MCP_PORT:-3000}

setup-gmail-mcp: ## OAuth setup for getwarmth@gmail.com Gmail MCP
	@echo "🔐 Gmail OAuth setup..."
	@echo "Download Desktop OAuth JSON from:"
	@echo "  https://console.cloud.google.com/apis/credentials?project=warmth-gtm-hackathon"
	@echo "Save as warmth/google-oauth-client.json then run this target again."
	cd .. && PYTHONPATH=. warmth/.venv/bin/python warmth/scripts/setup_gmail_oauth.py

test-gmail-draft: ## Send test draft to WARMTH_CLIENT_EMAIL via MCP bridge
	cd .. && PYTHONPATH=. warmth/.venv/bin/python warmth/scripts/test_gmail_mcp_draft.py

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

GCP_PROJECT ?= warmth-gtm-hackathon
GCP_REGION ?= us-central1
CLOUD_RUN_SERVICE ?= warmth-api

deploy-api: ## Deploy FastAPI to GCP Cloud Run
	gcloud run deploy $(CLOUD_RUN_SERVICE) \
		--source . \
		--project $(GCP_PROJECT) \
		--region $(GCP_REGION) \
		--allow-unauthenticated \
		--port 8000 \
		--min-instances 1 \
		--max-instances 1 \
		--concurrency 80 \
		--cpu 1 \
		--memory 1Gi \
		--env-vars-file infra/cloudrun-env.yaml

smoke-docker: ## Build Docker image and verify /health
	bash scripts/docker_smoke_test.sh

deploy-rules: ## Deploy Firestore security rules (and Storage rules when Storage is enabled)
	npx -y firebase-tools deploy --only firestore:rules --project $(GCP_PROJECT)

deploy-web: ## Build and deploy web to Firebase Hosting
	test -f web/.env.production || cp web/.env.production.example web/.env.production
	cd web && npm run build
	npx -y firebase-tools deploy --only hosting,firestore:rules --project $(GCP_PROJECT)