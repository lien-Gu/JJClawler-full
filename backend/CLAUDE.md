# CLAUDE.md

always response in chinese

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python FastAPI web crawler backend for Jinjiang Literature City (晋江文学城). The project crawls ranking data and novel information, providing RESTful APIs for data access. The project follows an **interface-driven development** approach where APIs are defined first, then functionality is broken down into independent modules.

## Development Workflow

### 1. API-First Development Approach
The project follows a strict API-First development methodology:

**Phase 1: Project Setup (Day 1-2)**
1. Project structure and environment configuration
2. uv dependency management setup
3. Basic FastAPI application framework

**Phase 2: API Design Priority (Day 3-4)**
1. Define all API endpoints based on business requirements
2. Create Pydantic models for request/response validation
3. Implement Mock APIs returning fake data for frontend development
4. Generate and review API documentation

**Phase 3: Database Implementation (Day 5-6)**
1. Design SQLModel models based on API requirements
2. Database schema creation and migrations
3. Basic CRUD operations implementation

**Phase 4: Module Development (Day 7-11)**
1. Replace Mock APIs with real implementations
2. Develop crawler, data service, and task management modules
3. Integrate all components

**Phase 5: Testing & Optimization (Day 12-14)**
1. End-to-end testing and performance optimization
2. Documentation and deployment preparation

### 2. Simplified Project Structure
```
JJClawer3/
├── app/
│   ├── __init__.py
│   ├── main.py                   # FastAPI application entry
│   ├── models.py                 # SQLModel data models (4 tables only)
│   ├── database.py               # Database connection and config
│   ├── config.py                 # Configuration management
│   ├── api/                      # API routes
│   │   ├── __init__.py
│   │   ├── pages.py              # Page configuration APIs
│   │   ├── rankings.py           # Ranking data APIs
│   │   ├── books.py              # Book information APIs
│   │   └── crawl.py              # Crawler management APIs
│   └── modules/                  # Business modules
│       ├── __init__.py
│       ├── crawler.py            # Crawling functionality
│       ├── data_service.py       # Data queries and filtering
│       └── task_service.py       # Task management (JSON files)
├── data/
│   ├── urls.json                 # Crawling configuration
│   ├── tasks/                    # Task JSON storage
│   │   ├── tasks.json           # Current task status
│   │   └── history/             # Historical task records
│   └── example/                  # Example data
├── tests/                        # Test directory
├── pyproject.toml
└── .env.example
```

## Development Commands

### Environment Setup
```bash
# Install dependencies
uv sync

# Activate virtual environment (optional, can use uv run directly)
source .venv/bin/activate  # Linux/Mac
# or .venv\Scripts\activate  # Windows
```

### Running the Application
```bash
# Start the FastAPI development server
uv run uvicorn main:app --reload --port 8000

# Or if in activated environment
uvicorn main:app --reload --port 8000
```

### Development Tools
```bash
# Add new dependencies
uv add package_name

# Add development dependencies
uv add --dev package_name

# Run tests (when implemented)
uv run pytest

# Format code (when configured)
uv run black .
uv run isort .
uv run ruff check . --fix
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

### Database Design

Uses SQLite with SQLModel ORM for type-safe database operations:

**Database Tables (SQLite):**
- `rankings`: Ranking configuration (metadata)
- `books`: Book static information (title, author, etc.)
- `book_snapshots`: Book dynamic information over time (clicks, favorites)
- `ranking_snapshots`: Book positions in rankings over time

**JSON File Storage:**
- `data/tasks/tasks.json`: Current and completed task status
- `data/tasks/history/`: Historical task records by date
- `data/urls.json`: Crawling configuration

**Key Design Decisions:**
1. **Separation of Concerns**: Database for core data, JSON for simple task management
2. **Time Series Data**: Snapshot approach for trend analysis
3. **Simplified Architecture**: Flat structure, minimal layers

**Database Schema:**
```sql
-- Static book information
books: book_id, title, author_id, author_name, novel_class, tags, first_seen, last_updated

-- Dynamic book statistics over time
book_snapshots: book_id, total_clicks, total_favorites, comment_count, chapter_count, snapshot_time

-- Ranking positions over time
ranking_snapshots: ranking_id, book_id, position, snapshot_time

-- Ranking metadata
rankings: ranking_id, name, channel, frequency, update_interval, parent_id
```

**Task JSON Format:**
```json
{
  "current_tasks": [
    {
      "task_id": "jiazi_20240101_120000",
      "task_type": "jiazi",
      "status": "running", 
      "created_at": "2024-01-01T12:00:00Z",
      "progress": 50,
      "items_crawled": 25
    }
  ],
  "completed_tasks": [...] 
}
```

### BookSnapshot Design Rationale

**Why separate dynamic information?**

The decision to use a separate `book_snapshots` table was made based on:

1. **Business Requirements**: User explicitly needs "book click/favorite change trends"
2. **Data Nature**: Static info (title, author) vs dynamic stats (clicks, favorites)
3. **Query Patterns**: Different access patterns for metadata vs time-series data
4. **Data Integrity**: Prevents loss of historical data during updates

**Benefits:**
- ✅ Complete trend analysis capabilities
- ✅ Clear separation of concerns
- ✅ Optimized indexes for different query types
- ✅ Supports both global and ranking-specific statistics

**Trade-offs:**
- ❌ Additional storage space required
- ❌ More complex data maintenance
- ⚠️ Need to manage snapshot creation timing

### Key Dependencies
- FastAPI: Web framework
- SQLModel: Type-safe ORM based on SQLAlchemy and Pydantic
- httpx: Async HTTP client for crawling
- APScheduler: Task scheduling
- uv: Dependency management
- Uvicorn: ASGI server

## Detailed Task Breakdown

### Task Categories by Module

**Crawler Module Tasks:**
- T4.1.1: HTTP Client Setup (httpx configuration, retry mechanism, rate limiting)
- T4.1.2: Jiazi Ranking Scraper (parse jiazi API response, extract book data)
- T4.1.3: Category Page Scraper (parse ranking pages, extract book lists)
- T4.1.4: Book Detail Scraper (fetch complete book information)
- T4.1.5: Data Parser (clean and standardize scraped data)

**Data Service Module Tasks:**
- T4.2.1: Page Service (generate page config from urls.json, manage hierarchy)
- T4.2.2: Ranking Service (ranking queries, history comparison, rank change calculation)
- T4.2.3: Book Service (book detail queries, ranking history, trend analysis)
- T4.2.4: Pagination Service (generic pagination, multi-dimension filtering, sorting)

**Task Management Module Tasks:**
- T4.3.1: JSON File Operations (read/write tasks.json, status management)
- T4.3.2: Task Status Management (pending, running, completed, failed states)
- T4.3.3: Scheduler Integration (APScheduler setup, cron configuration)
- T4.3.4: Task Monitoring (progress tracking, error handling)

**API Implementation Tasks:**
- T4.4.1: Replace Page Mock APIs with real implementations
- T4.4.2: Replace Ranking Mock APIs with real implementations  
- T4.4.3: Replace Book Mock APIs with real implementations
- T4.4.4: Replace Crawler Mock APIs with real implementations

### Task Dependencies and Sequencing

**Critical Path:**
1. T2.1 → T3.1 → T4.4.x (API models → DB models → API implementation)
2. T3.2 → T4.2.x (DB operations → Data services)
3. T4.1.x → T4.3.x (Crawler → Task management)

**Parallel Development Opportunities:**
- T4.1.x and T4.2.x can be developed simultaneously
- T4.3.x (JSON task management) is independent and can be developed early
- Frontend development can start after T2.x completion

## Development Notes

- **Simplicity First**: Choose the simplest implementation that works
- **API-First**: Always define APIs before implementing backend logic
- **Flat Architecture**: Minimal layers, direct module communication
- **Mixed Storage**: Database for complex data, JSON for simple state management
- **Type Safety**: Use SQLModel for database models and Pydantic for API models
- **Task Isolation**: Each sub-task has clear inputs/outputs, avoiding cross-module coupling
- **Mock-to-Real**: Staged replacement of mock implementations with real functionality
- **Error Handling**: Implement proper error handling and logging in each module
- **Rate Limiting**: Respect target site's rate limits (1 second intervals)
- **Data Validation**: Use Pydantic models for request/response validation
- **Async Operations**: Use async/await for I/O operations
- **Testing Strategy**: Mock APIs early to enable frontend development