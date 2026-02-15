# AGENTS.md

This file provides guidelines for agentic coding agents working in this repository.

## Build, Lint, Test Commands

This project uses **uv** as the package manager.

```bash
# Install dependencies
uv sync

# Run the FastAPI server
uvicorn src.app:app --reload

# Run specific modules for testing
python src/score/score_records.py
python src/records/email.py
python src/records/qtrade.py
python src/records/ideal.py
python src/records/call_recording.py
python src/records/trading_recording.py
python src/records/auth.py
python src/utils/logger.py
python src/test.py
```

**Note**: No test framework or linting tools configured. Verify modules by running directly.

## Project Structure

```
src/
├── app.py                  # FastAPI application entry point
├── test.py                 # API endpoint test script
├── score/                  # Event scoring module
│   └── score_records.py   # Main scoring logic and event reconstruction
├── records/                # Communication record retrieval
│   ├── auth.py            # CCS authentication with token caching
│   ├── content.py         # Content retrieval from records
│   ├── email.py           # Email records
│   ├── call_recording.py  # Phone call recordings
│   ├── trading_recording.py  # Trading phone records
│   ├── qtrade.py          # QTrade messaging
│   └── ideal.py           # Ideal messaging
├── utils/                  # Utility modules
│   ├── config.py          # TOML configuration loader
│   ├── config.toml        # Application settings
│   ├── logger.py          # Loguru logging with rotation
│   └── llm.py             # LLM clients (VLLM, DashScope)
├── prompts/                # System prompts for AI tasks
├── output/                 # JSON results with timestamps
└── logs/                   # Daily rotated log files
```

## Code Style Guidelines

### General
- Python >= 3.12 required (modern type hint syntax: `str | None`, `list[dict]`)
- Standard library imports first, third-party next, local imports last
- Use relative imports within packages: `from .auth import get_token`
- Constants: `SCREAMING_SNAKE_CASE`, functions/variables: `snake_case`, classes: `PascalCase`

### Async Patterns
- All record retrieval functions are async: `async def get_*_records(...) -> list[dict]:`
- Include `main()` for testing with: `if __name__ == "__main__": asyncio.run(main())`
- Measure execution: `start_time = time.time()`; print elapsed at end

### Module Structure
1. Import dependencies
2. Load config: `config = load_config()` from utils.config
3. Define constants from config at module level
4. Define async functions
5. Define `main()` for testing
6. Add `__all__` exports in `__init__.py` files

### Error Handling
- Use `requests.raise_for_status()` for HTTP errors
- Add timeout parameter: `requests.post(url, json=data, timeout=10)` (default 10s, test.py uses 300s)
- Validate API responses: `response.json()["message"] == "success"`
- Raise descriptive exceptions: `raise Exception(f"failed: {response.json()['message']}")`
- Use `logger.error()` for logging, handle missing fields with `.get()`

### Logging
- Import: `from loguru import logger`, call `setup_logger()` once at module level
- Use `logger.info()`, `logger.error()`, `logger.exception()`
- `print()` only in `main()` for user output
- Console: `rich.Console` and `rich.Table` for formatted output

### Docstrings
- Triple quotes, Chinese description, English Args/Returns
- Format: `"""Description. Args: ... Returns: ..."""`

### String Formatting
- Use f-strings: `f"{API_BASE_URL}{END_POINT}"`
- Numbers: `f"{score:.2f}"`, table widths: `f"{val:<10}"`
- Multi-line: `textwrap.dedent()` (especially for prompts)

### Time Handling
- Use `datetime` from standard library
- Parse: `datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")`
- Support both ISO (`T`) and space-separated formats

### File I/O
- Use `pathlib.Path` for all file operations
- JSON: `json.dump(data, f, ensure_ascii=False, indent=2)`
- Create dirs: `mkdir(parents=True, exist_ok=True)`
- Results: `src/output/result_YYYYMMDD_HHMMSS.json`
- Read: `path.read_text(encoding="utf-8")`

### Configuration
- All config in `src/utils/config.toml`
- Load: `config = load_config()`, access: `config["CCS_SERVER"]["API_BASE_URL"]`

### Pydantic Models
- Use `pydantic.BaseModel`, `Field(..., description="...")`
- Access data via `.model_dump()`

### LLM Integration
- Prompts in `src/prompts/*.md`
- Read: `Path("path.md").read_text(encoding="utf-8")`
- Format with: `prompt.format(var=value)`
- For JSON outputs, include backticks and strip from response

### Caching
- `cachetools.TTLCache(maxsize=1, ttl=3600)` with `@cached` decorator
- Used for authentication tokens (1 hour TTL)

### FastAPI Pattern
- Add project root to sys.path if needed
- Use `uvicorn.run(app, host="0.0.0.0", port=8000)` for local dev

## External Dependencies

- **agno** >= 2.4.8 - AI agent framework
- **dashscope** >= 1.25.12 - Alibaba AI service
- **fastapi** >= 0.128.7 - Web framework
- **openai** >= 2.17.0 - OpenAI-compatible client
- **loguru** >= 0.7.3 - Logging
- **pydantic** >= 2.12.5 - Data validation
- **cachetools** >= 7.0.0 - Caching
- **requests** - HTTP client (add to dependencies manually if missing)
- **rich** - Terminal formatting
- **textwrap** (stdlib) - Multi-line string dedent for prompts
- **pathlib** (stdlib) - File path operations

## Key Integration Points

- **CCS API**: Communication records with auth token caching
- **Reranker Service**: Content relevance scoring
- **DashScope/VLLM**: LLM models for AI analysis and risk assessment
- All time formats support both ISO and space-separated strings
- Check API `"message"` field equals `"success"` before processing

## Important Notes

- Verify by running modules directly (no test framework)
- Always use `requests.raise_for_status()` for error handling
- Records deduplicated by ID when aggregating
- Logger outputs to stdout and rotates daily to `src/logs/`
- Use list comprehensions for data transformation
