.PHONY: test test-unit test-cov install install-dev lint typecheck validate-evidence new-feature new-bug

install:
	pip install -e .

install-dev:
	pip install -e .[dev]

test: test-unit

test-unit:
	pytest tests/unit -v

test-cov:
	pytest tests/unit --cov=agilev --cov-report=term-missing --cov-report=html

lint:
	ruff check src/ tests/

typecheck:
	mypy src/agilev/

validate-evidence:
	python scripts/validate_evidence.py --root evidence

new-feature:
	python scripts/new_task.py --type feature --id AAV-001 --title "Example feature"

new-bug:
	python scripts/new_task.py --type bug --id AAV-002 --title "Example bug"
