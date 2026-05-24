.PHONY: dev install ingest-sample eval test docker-up docker-down clean

dev:
	@echo "Starting FastAPI Backend Server..."
	cd backend && poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
	@echo "Starting Next.js Frontend Server..."
	cd frontend && npm run dev &
	@wait

install:
	@echo "Installing Backend dependencies using Poetry..."
	cd backend && poetry install
	@echo "Installing Frontend dependencies using NPM..."
	cd frontend && npm install

ingest-sample:
	@echo "Ingesting sample documents..."
	cd backend && poetry run python ../scripts/ingest_sample_docs.py

eval:
	@echo "Running RAG evaluation suite..."
	cd backend && poetry run python ../evals/run_eval.py

test:
	@echo "Running unit tests..."
	cd backend && poetry run pytest app/tests/

docker-up:
	@echo "Spinning up Docker Compose services..."
	docker-compose up --build -d

docker-down:
	@echo "Stopping Docker Compose services..."
	docker-compose down

clean:
	@echo "Cleaning up temporary cache and index files..."
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	rm -rf backend/data/processed/qdrant_storage
	rm -f backend/data/processed/tasks.db
