.PHONY: venv install run test lint clean help

# Default target
help:
	@echo "Available targets:"
	@echo "  venv     - Create virtual environment"
	@echo "  install  - Install dependencies in virtual environment"
	@echo "  run      - Run the Flask development server"
	@echo "  test     - Run tests"
	@echo "  lint     - Run linting tools"
	@echo "  clean    - Clean up generated files"

# Create virtual environment
venv:
	python -m venv .venv
	@echo "Virtual environment created in .venv"
	@echo "Activate with: source .venv/bin/activate (Linux/Mac) or .venv\\Scripts\\activate (Windows)"

# Install dependencies in virtual environment
install: venv
	.venv/bin/pip install --upgrade pip
	.venv/bin/pip install -r requirements.txt

# Run the Flask development server
run:
	.venv/bin/python run.py

# Run tests
test:
	.venv/bin/python -m pytest

# Run linting tools
lint:
	.venv/bin/python -m ruff check .
	.venv/bin/python -m mypy .
	.venv/bin/python -m black --check .

# Clean up
clean:
	rm -rf .venv
	rm -rf __pycache__
	rm -rf .pytest_cache
	rm -rf .ruff_cache
	rm -rf .mypy_cache
