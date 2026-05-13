PYTHON ?= python3

.PHONY: install dev lint typecheck test run docker-up docker-down import-threads import-agents collect-markets collect-trades validate-data compute-metrics scan-inefficiencies run-backtest run-paper-trading

install:
	$(PYTHON) -m pip install -e ".[dev,research]"

dev:
	uvicorn polybot.main:app --reload --host 0.0.0.0 --port 8000

lint:
	ruff check src scripts tests

typecheck:
	mypy src/polybot

test:
	pytest

run:
	uvicorn polybot.main:app --host 0.0.0.0 --port 8000

docker-up:
	docker compose up -d --build

docker-down:
	docker compose down

import-threads:
	PYTHONPATH=src $(PYTHON) scripts/import_twitter_threads.py

import-agents:
	PYTHONPATH=src $(PYTHON) scripts/import_agents_git.py --no-clone

collect-markets:
	PYTHONPATH=src $(PYTHON) scripts/collect_markets.py

collect-trades:
	PYTHONPATH=src $(PYTHON) scripts/collect_trades.py

validate-data:
	PYTHONPATH=src $(PYTHON) scripts/validate_data.py

compute-metrics:
	PYTHONPATH=src $(PYTHON) scripts/compute_market_metrics.py

scan-inefficiencies:
	PYTHONPATH=src $(PYTHON) scripts/scan_inefficiencies.py

run-backtest:
	PYTHONPATH=src $(PYTHON) scripts/run_backtest.py

run-paper-trading:
	PYTHONPATH=src $(PYTHON) scripts/run_paper_trading.py
