# Flight Ticket Researcher

An enterprise-grade, asynchronous, multi-engine flight price crawling and analytics application designed around **Domain-Driven Design (DDD)** and **Clean Architecture** principles.

Developed to automate flight price monitoring on Trip.com, this application isolates core business logic from automation drivers and persistence repositories, supporting flexible configurations and extensive test coverage.

---

## 🚀 Key Architectural Features

- **Domain-Driven Design (DDD)**: Adheres strictly to Domain, Application, Infrastructure, and Presentation boundaries. Core domain entities are completely framework-agnostic.
- **Asynchronous Non-blocking Core**: Fully asynchronous implementation leveraging `asyncio`, `aiofiles`, and `asyncio.to_thread` for high-throughput execution.
- **Multi-Engine Driver Support**: Seamlessly interchangeable engine adapters supporting **Selenium**, **Playwright**, **Pyppeteer (Puppeteer Python)**, and **FastMCP Stealth Browser** (via MCP Bearer Token Auth).
- **Flexible Persistence Adapters**: Integrated repository patterns supporting:
  - **DuckDB**: Structured SQL tables with native exports to Parquet and CSV.
  - **Pandas**: Structured exports to Parquet, CSV, and Excel (xlsx).
  - **JSON**: Fast serialization via `orjson` or fallback built-in `json`.
- **Advanced Observability**: Emits telemetry records and performance statistics (latency averages, success rates, anti-bot captcha detection counts) directly to structured metrics JSON files.
- **Modern Python Workspace**: Designed to run smoothly inside a `uv` project workspace.

---

## 📁 Project Directory Layout

```text
flight-ticket-researcher/
├── main.py                  # Presentation Layer (CLI entrypoint)
├── config.json              # Scraper configuration options
├── requirements.txt         # Package dependencies
├── results/                 # Ignored outputs (databases, reports, logs)
├── tests/                   # Test Suite
│   ├── unit/                # Unit tests for domain, persistence, & config
│   └── e2e/                 # Integration and Mock E2E tests
└── src/
    ├── domain/              # Core Domain Layer (Entities, Value Objects, & Interfaces)
    │   ├── entities.py      # FlightPrice entity
    │   ├── value_objects.py # Route & DateConfig value objects
    │   ├── repositories.py  # Abstract FlightRepository interface
    │   └── services.py      # Abstract BrowserEngine & FlightScraperService interfaces
    │
    ├── application/         # Core Application Layer (Use Cases)
    │   └── research_flights.py # ResearchFlightsUseCase orchestrator
    │
    └── infrastructure/      # Infrastructure Layer (Technology Adapters)
        ├── config/          # Pydantic configuration parser
        ├── engines/         # Selenium, Playwright, Puppeteer, & FastMCP drivers
        ├── scrapers/        # Trip.com parser implementation
        ├── persistence/     # JSON, Pandas, & DuckDB repository writers
        └── monitoring/      # Logger setup & ObservabilityManager
```

---

## 🛠️ Installation & Setup

1. Make sure you have [uv](https://github.com/astral-sh/uv) installed.
2. Install the dependencies inside your environment:
   ```bash
   uv pip install -r requirements.txt
   ```

---

## ⚙️ Configuration (`config.json`)

Adjust your query parameters inside `config.json`. Key properties:
- `engine_type`: Choice of `"selenium"`, `"playwright"`, `"puppeteer"`, or `"fastmcp"`.
- `storage_type`: Choice of `"duckdb"`, `"pandas"`, or `"json"`.
- `storage_options`: Directory and export target configurations for databases and files.
- `dcity` / `acity`: Origin and destination airport IATA codes (e.g. `"PLM"`, `"VIE"`).
- `months`: List of month scopes containing targeted scan days:
  ```json
  "months": [
    {
      "year_month": "2026-08",
      "days": [1, 2, 5]
    }
  ]
  ```

---

## 🖥️ Usage

Run the scraper using the CLI entrypoint:

```bash
uv run python3 main.py \
  --config config.json \
  --output-report results/prices_report.md \
  --log-file results/scraper.log
```

---

## 🧪 Testing & Code Coverage

The project uses `pytest` and `pytest-asyncio` for unit and E2E validation. Code coverage is measured using `pytest-cov`.

To run the complete test suite:
```bash
uv run pytest
```

To run tests and output a detailed statement coverage report:
```bash
uv run pytest --cov=src --cov-report=term-missing
```

*Note: All core domain modules, scraping logic, logging, and observability files have **100% unit test coverage**.*
