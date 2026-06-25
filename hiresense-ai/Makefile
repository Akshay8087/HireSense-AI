.PHONY: help install dev run test test-cov build-index docker-build docker-up docker-down lint clean

help:
	@echo "HireSense AI — available commands:"
	@echo "  make install       Install Python dependencies"
	@echo "  make build-index   Build the FAISS index from the sample resume corpus"
	@echo "  make run           Run the Flask dev server (python app.py)"
	@echo "  make run-prod      Run via gunicorn locally, as in production"
	@echo "  make test          Run the test suite"
	@echo "  make test-cov      Run tests with coverage report"
	@echo "  make docker-build  Build the production Docker image"
	@echo "  make docker-up     Start the app with docker-compose"
	@echo "  make docker-down   Stop the docker-compose stack"
	@echo "  make lint          Run ruff lint checks"
	@echo "  make clean         Remove caches and build artifacts"

install:
	pip install -r requirements.txt
	cp -n .env.example .env || true
	@echo "Edit .env and add your GEMINI_API_KEY if you want LLM-generated suggestions."

build-index:
	python scripts/build_index.py

run:
	python app.py

run-prod:
	gunicorn -c gunicorn.conf.py wsgi:app

test:
	pytest tests/ -v

test-cov:
	pytest tests/ -v --cov=app --cov-report=term-missing --cov-report=html

docker-build:
	docker build -t hiresense-ai:latest .

docker-up:
	docker compose up --build

docker-down:
	docker compose down

lint:
	ruff check app/ tests/ scripts/

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache .coverage htmlcov .cache
