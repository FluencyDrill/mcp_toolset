.DEFAULT_GOAL := help
PIPELINES_DIR ?= ./pipeline_wrappers

.PHONY: help install run mcp mcp-stdio test lint fmt

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

install: ## Create the env and install deps (editable)
	uv sync

run: ## Run the Hayhooks REST server (http://localhost:1416, /docs)
	HAYHOOKS_PIPELINES_DIR=$(PIPELINES_DIR) uv run hayhooks run

mcp: ## Run the Hayhooks MCP server (http://localhost:1417/mcp)
	HAYHOOKS_PIPELINES_DIR=$(PIPELINES_DIR) uv run hayhooks mcp run

mcp-stdio: ## Bridge the MCP server to stdio via supergateway (server must be running)
	npx -y supergateway --streamableHttp http://localhost:1417/mcp

test: ## Run the test suite
	uv run pytest

lint: ## Lint with ruff
	uv run ruff check .

fmt: ## Format with ruff
	uv run ruff format .
	uv run ruff check --fix .
