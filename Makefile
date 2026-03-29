.PHONY: up down rebuild sync api-test frontend-build backend-test clean

up:
	docker compose up --build

down:
	docker compose down

rebuild:
	docker compose build --no-cache

sync:
	curl -X POST http://localhost:8000/api/v1/ingest

api-test:
	curl http://localhost:8000/health

frontend-build:
	cd frontend && npm run build

backend-test:
	cd Project && python -m unittest discover -s tests -v

clean:
	rm -rf Project/data/*.db Project/data/index_store.json frontend/dist
