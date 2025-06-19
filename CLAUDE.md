# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python FastAPI web crawler backend for Jinjiang Literature City (晋江文学城). The project crawls ranking data and novel information, providing RESTful APIs for data access. The project follows an **interface-driven development** approach where APIs are defined first, then functionality is broken down into independent modules.

## Development Workflow

### 1. Interface-First Development
1. Define all API endpoints based on requirements
2. Specify input/output formats for each endpoint
3. Break down functionality into independent modules based on interface responsibilities
4. Develop each module independently with its own tests

### 2. Module Structure
```
modules/
├── crawler.py          # Crawling functionality (/api/v1/crawl/*)
├── data_service.py     # Data queries (/api/v1/rankings/*, /api/v1/novels/*)
├── task_service.py     # Task management (/api/v1/tasks/*)
└── stats_service.py    # Statistics (/api/v1/stats)
```

## Development Commands

### Environment Setup
```bash
# Install dependencies
poetry install

# Activate virtual environment
poetry shell
```

### Running the Application
```bash
# Start the FastAPI development server
poetry run uvicorn main:app --reload --port 8000

# Or if in poetry shell
uvicorn main:app --reload --port 8000
```

### Development Tools
```bash
# Add new dependencies
poetry add package_name

# Add development dependencies
poetry add --group dev package_name

# Run tests (when implemented)
poetry run pytest

# Format code (when configured)
poetry run black .
poetry run isort .
```

### Testing
Use the provided `test_main.http` file to test endpoints manually. API documentation is available at `http://127.0.0.1:8000/docs` when the server is running.

## Project Architecture

### Core API Endpoints
- `GET /health` - Health check
- `GET /api/v1/rankings/latest` - Latest ranking data
- `GET /api/v1/rankings` - Historical rankings with filters
- `GET /api/v1/novels/{novel_id}` - Novel details
- `GET /api/v1/novels` - Novel list with filters
- `POST /api/v1/crawl/jiazi` - Trigger jiazi ranking crawl
- `POST /api/v1/crawl/page` - Trigger specific page crawl
- `GET /api/v1/tasks` - Task status and history
- `GET /api/v1/stats` - System statistics

### Data Storage
Uses JSON file storage organized by date and type:
```
data/
├── rankings/YYYY-MM-DD/
│   ├── jiazi.json
│   └── fenlei.json
├── novels/
│   └── novel_details.json
└── tasks/
    └── task_history.json
```

### Key Dependencies
- FastAPI: Web framework
- httpx: Async HTTP client for crawling
- Poetry: Dependency management
- Uvicorn: ASGI server

## Development Notes

- **Modular Design**: Each module should be independently testable and deployable
- **Error Handling**: Implement proper error handling and logging in each module
- **Rate Limiting**: Respect target site's rate limits (1 second intervals)
- **Data Validation**: Use Pydantic models for request/response validation
- **Async Operations**: Use async/await for I/O operations