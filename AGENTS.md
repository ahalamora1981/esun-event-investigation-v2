# AGENTS.md

This file provides guidelines for agentic coding agents working in this repository.

## Build, Lint, Test Commands

This project uses **uv** as the package manager.

```bash
# Install dependencies
uv sync

# Run the main application
python src/score_records.py

# Run specific record retrieval modules
python src/records/email.py
python src/records/qtrade.py
python src/records/ideal.py
python src/records/call_recording.py

# Run utility modules
python src/utils/logger.py
python src/utils/config.py
python src/records/auth.py
```

**Note**: This project currently does not have a test framework. No tests exist in the codebase. When adding tests, check with the user for the preferred testing approach.

## Project Structure

```
src/
├── score_records.py       # Main application - event scoring logic
├── records/                # Communication record retrieval modules
│   ├── auth.py            # CCS authentication token management
│   ├── content.py         # Content retrieval from records
│   ├── email.py           # Email record retrieval
│   ├── call_recording.py  # Phone call recording retrieval
│   ├── qtrade.py          # QTrade messaging retrieval
│   ├── ideal.py           # Ideal messaging retrieval
│   └── trading_recording.py
├── utils/                  # Utility modules
│   ├── config.py          # Configuration loader (TOML)
│   ├── config.toml        # Application configuration
│   ├── logger.py          # Loguru logging setup
│   └── llm.py             # AI/LLM agent setup (agno)
└── logs/                   # Application logs (rotated daily)
```

## Code Style Guidelines

### Imports
- Standard library imports first, third-party next, local imports last
- Use relative imports within packages: `from .auth import get_token`, `from ..utils import load_config`
- Group imports with blank lines between sections

### Type Hints
- Use modern Python 3.12 union syntax: `str | None` instead of `Optional[str]`
- Use generic syntax: `list[dict]` instead of `List[Dict[str, Any]]`
- Always include return types for public functions
- Example: `async def get_email_records(..., content: bool = False) -> list[dict]:`

### Naming Conventions
- **Functions/Variables**: `snake_case` (e.g., `get_token`, `participant_ids`)
- **Classes**: `PascalCase` (e.g., `TimeScore`, `ScoreWeights`)
- **Constants**: `SCREAMING_SNAKE_CASE` (e.g., `API_BASE_URL`, `CHANNEL`)
- **Private/Internal**: Prefix with underscore if needed (rarely used)
- **Async Functions**: No special prefix, just use `async def`

### Async/Await Patterns
- All record retrieval functions are async: `async def get_*_records(...) -> list[dict]:`
- Include `main()` async function for module testing
- Run with: `if __name__ == "__main__": asyncio.run(main())`
- Measure execution time: `start_time = time.time()` at start, print elapsed time at end

### Error Handling
- Use `requests.raise_for_status()` for HTTP errors
- Validate API response messages: check `response.json()["message"] == "success"`
- Raise descriptive exceptions on failure: `raise Exception(f"get email records failed: {response.json()['message']}")`
- Use `logger.error()` for error logging
- Handle missing fields gracefully (e.g., `record.get("endTime", record_start_time)`)

### Docstrings
- Use triple quotes for docstrings
- Include Chinese descriptions and English Args/Returns
- Format:
  ```python
  """
  Get the email records.

  Args:
      participant_ids (str, mandatory): Comma-separated participant IDs.
      start_time (str, mandatory): Start time, format "2025-10-01 00:00:00".
      content (bool, optional): Whether to get content. Defaults to False.

  Returns:
      list[dict]: List of email records.
  """
  ```

### Logging
- Import: `from loguru import logger`
- Initialize in modules: call `setup_logger()` from `utils.logger` once at module level
- Use `logger.info()`, `logger.error()`, `logger.exception()` appropriately
- Use `print()` only in `main()` for user-facing output or debugging
- Use `rich.Console` and `rich.Table` for formatted table output (see score_records.py)
- Logger configuration is in `src/utils/logger.py` - outputs to stdout and daily rotated files

### Configuration
- All configuration stored in `src/utils/config.toml`
- Load using: `config = load_config()` from `utils.config`
- Access via keys: `config["CCS_SERVER"]["API_BASE_URL"]`
- Module-level constants initialized from config at import time

### Module Structure Pattern
- Import dependencies
- Load config
- Define constants (API URLs, endpoints, channel names)
- Define async functions
- Define `main()` function for module testing
- Add `if __name__ == "__main__": asyncio.run(main())` block

### Code Organization
- Constants defined at module level (UPPER_CASE)
- Functions grouped by purpose
- Each record type (email, qtrade, ideal, call_recording) follows same pattern
- Use list comprehensions for data transformation
- Deduplicate records by ID when aggregating

### String Formatting
- Use f-strings: `f"{API_BASE_URL}{END_POINT}"`
- Format numbers: `f"{score['total_score']:.2f}"`
- For table output, use width specifiers: `f"{record['channel']:<6}"`

### Time Handling
- Use `datetime` from standard library
- Parse with: `datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")`
- Support both ISO format (`T`) and space-separated format
- Use `datetime.fromisoformat()` for parsing ISO strings

### Main Execution Pattern
```python
import time
import asyncio

async def main():
    # Application logic here
    pass

if __name__ == "__main__":
    start_time = time.time()
    asyncio.run(main())
    end_time = time.time()
    print(f"[OK] Total time: {end_time - start_time:.2f} seconds")
```

## External Dependencies

- **agno** >= 2.4.8 - AI agent framework
- **dashscope** >= 1.25.12 - Alibaba's AI service
- **openai** >= 2.17.0 - OpenAI-compatible API
- **loguru** >= 0.7.3 - Logging
- **pydantic** >= 2.12.5 - Data validation
- **cachetools** >= 7.0.0 - Caching (used for token caching with TTL)
- **requests** - HTTP client
- **rich** - Terminal formatting for tables and colored output

## Key Integration Points

- **CCS API**: Main external service for communication records
- **Reranker Service**: Content relevance scoring
- **DashScope/VLLM**: LLM models for AI analysis
- Authentication token is cached for 1 hour using `@cached` decorator

## Important Notes

- Python version: >= 3.12 (uses modern type hint syntax)
- Package manager: uv (use `uv sync` for dependencies)
- No current test framework - always verify by running modules directly
- All time formats should handle both ISO and space-separated formats
- Always use `requests.raise_for_status()` for error handling
- Check API response `"message"` field equals `"success"` before processing data
