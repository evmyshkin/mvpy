# Local
dev:
	uv run uvicorn app.main:app --reload

# Container stack
up:
	docker compose up -d
up_stack:
	docker compose up --build -d
down:
	docker compose down

# Test
test:
	pytest --cov=app --cov-branch --cov-report=term-missing

# Lint
lint:
	pre-commit run --all-files