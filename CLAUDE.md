# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

JJClawler is a WeChat Mini-Program project for crawling Jinjiang Literature City (晋江文学城) data. It consists of two main parts:

- **Backend** (`/backend`): Python FastAPI web crawler service providing RESTful APIs
- **Frontend** (`/frontend`): Vue.js based WeChat Mini-Program interface

The project follows an API-first development approach with comprehensive data crawling, storage, and presentation capabilities.

## Development Commands

### Backend Development
```bash
# Navigate to backend directory
cd backend

# Install dependencies with Poetry
poetry install

# Activate environment
poetry shell

# Start development server
poetry run uvicorn app.main:app --reload --port 8000

# Run tests
poetry run pytest

# Format code
poetry run black .
poetry run isort .
poetry run ruff check . --fix

# Check API documentation
# Visit http://localhost:8000/docs
```

### Frontend Development
```bash
# Navigate to frontend directory
cd frontend

# Install dependencies (if using package manager)
npm install  # or equivalent for your WeChat development tools

# Development in WeChat Developer Tools
# Import the frontend directory as a WeChat Mini-Program project
```

### Testing APIs
Use the provided test files:
- Backend: `backend/test_main.http` - HTTP requests for API testing
- Test endpoints at `http://localhost:8000/api/v1/*`

## Architecture Overview

### Backend Architecture (FastAPI + SQLite + APScheduler)

```
backend/
├── app/
│   ├── main.py                     # FastAPI application entry
│   ├── config.py                   # Application configuration
│   ├── api/                        # API Routes (5-layer architecture)
│   │   ├── pages.py                # Page configuration APIs
│   │   ├── rankings.py             # Ranking data APIs  
│   │   ├── books.py                # Book information APIs
│   │   ├── crawl.py                # Crawler management APIs
│   │   └── stats.py                # Statistics APIs
│   ├── modules/                    # Business Logic Modules
│   │   ├── models/                 # SQLModel data models
│   │   ├── dao/                    # Data Access Objects
│   │   ├── service/                # Business Services
│   │   ├── crawler/                # Crawler implementations
│   │   └── database/               # Database connections
│   └── utils/                      # Utility functions
├── data/                           # Data storage
│   ├── urls.json                   # Crawling configuration
│   └── tasks/                      # Task management (JSON)
├── docs/                           # Documentation
└── tests/                          # Test suites
```

### Frontend Architecture (WeChat Mini-Program)

```
frontend/
├── pages/                          # Mini-program pages
│   ├── index/                      # Homepage (statistics)
│   ├── ranking/                    # Ranking lists and details
│   ├── book/                       # Book details
│   ├── follow/                     # User follows
│   └── settings/                   # Settings
├── components/                     # Reusable components
├── utils/                          # Utility functions
│   ├── request.js                  # API request wrapper
│   └── storage.js                  # Local storage management
├── styles/                         # SCSS styles
└── data/                           # Configuration data
```

## Key Development Patterns

### Backend Patterns
1. **5-Layer Architecture**: API → Service → DAO → Database → Models
2. **Dependency Injection**: Services injected into API endpoints
3. **SQLModel**: Combined database and API models for type safety
4. **Async/Await**: All I/O operations are asynchronous
5. **Task Scheduling**: APScheduler for automated crawling
6. **JSON Task Management**: Simple task tracking via JSON files

### Frontend Patterns
1. **Component-Based**: Reusable Vue components for UI elements
2. **Page Routing**: WeChat Mini-Program page navigation
3. **API Integration**: RESTful API consumption via utils/request.js
4. **Local Storage**: User preferences and cache management
5. **Multi-Level Navigation**: Site → Channel → Ranking → Book hierarchy

## Database Design

### SQLite Tables (4 core tables):
- `rankings`: Ranking configuration metadata
- `books`: Book static information (title, author, etc.)
- `book_snapshots`: Book dynamic statistics over time
- `ranking_snapshots`: Book positions in rankings over time

### JSON File Storage:
- `data/tasks/tasks.json`: Current task states
- `data/urls.json`: Crawling configuration

## API Interface Summary

### Core Endpoints (Backend `/api/v1`):
- **Statistics**: `GET /stats/overview` - Homepage overview data
- **Rankings**: `GET /rankings` - Ranking lists, `GET /rankings/{id}/books` - Books in ranking
- **Books**: `GET /books/{id}` - Book details, `GET /books/{id}/rankings` - Book ranking history
- **Pages**: `GET /pages` - Dynamic page configuration
- **Crawler**: `POST /crawl/jiazi`, `POST /crawl/page/{channel}` - Trigger crawling
- **Tasks**: `GET /crawl/tasks` - Task monitoring

### Frontend API Requirements:
- Homepage statistics and hot rankings
- Multi-level navigation (sites → channels → rankings)
- Book search and detail viewing
- User follow functionality (planned)

## Crawling Strategy

### Automated Scheduling (APScheduler):
- **Jiazi Rankings**: Every hour (high-frequency updates)
- **Channel Pages**: Daily with staggered execution (6 AM - 6 PM)
- **Error Handling**: Automatic retry with exponential backoff
- **Rate Limiting**: 1-second intervals between requests

### Crawling Targets:
- Jiazi ranking (most active ranking)
- Category pages (Romance, Pure Love, Derivative, etc.)
- Individual book details and statistics
- Historical ranking positions

## Deployment Guide

### Development Environment:
```bash
# Backend setup
cd backend && poetry install && poetry shell
poetry run uvicorn app.main:app --reload --port 8000

# Frontend setup  
# Import frontend/ into WeChat Developer Tools
# Configure backend API base URL in utils/request.js
```

### Production Deployment:
```bash
# Docker deployment (see backend/docs/docker-deployment.md)
docker build -t jjcrawler .
docker run -d -p 8000:8000 -v $(pwd)/data:/app/data jjcrawler

# Scheduler management (see backend/docs/scheduler-operations.md)
# Monitor at GET /api/v1/crawl/scheduler/status

# Operations guide (see backend/docs/production-operations.md)
```

## Testing Strategy

### Backend Testing:
- Unit tests for services and DAOs
- Integration tests for API endpoints
- Performance tests for crawler operations
- Database consistency tests

### API Testing:
- Use `backend/test_main.http` for manual testing
- Automated tests with pytest
- Mock data for development/testing

## Common Development Tasks

### Adding New API Endpoints:
1. Define request/response models in `app/modules/models/api.py`
2. Implement business logic in appropriate service
3. Create API route in `app/api/` directory
4. Register router in `app/main.py`
5. Add tests to `test_main.http`

### Adding New Crawling Targets:
1. Update `data/urls.json` with new site configuration
2. Implement crawler in `app/modules/crawler/` 
3. Add scheduling in `app/modules/service/scheduler_service.py`
4. Create API endpoints for manual triggering

### Extending Frontend:
1. Create page in `pages/` directory
2. Add route to `pages.json`
3. Implement API calls using `utils/request.js`
4. Add navigation to appropriate parent pages

## Troubleshooting

### Backend Issues:
- **Port conflicts**: Use different port with `--port` flag
- **Database locks**: Check SQLite WAL mode is enabled
- **Scheduler not running**: Verify APScheduler configuration
- **API errors**: Check logs and `/health` endpoint

### Frontend Issues:
- **API connection**: Verify backend URL in `utils/request.js`
- **WeChat tools**: Ensure proper project configuration
- **Component loading**: Check import paths and component registration

### Deployment Issues:
- **Docker**: Check container logs with `docker logs`
- **Permissions**: Ensure data directory is writable
- **Network**: Verify firewall and port configuration
- **SSL**: Configure Nginx reverse proxy for HTTPS

## Data Management

### Backup Procedures:
```bash
# Database backup
cp data/*.db backup/
cp data/tasks/*.json backup/

# Automated backup (see production-operations.md)
```

### Data Cleanup:
```bash
# Clean old snapshots (retain 30 days)
# See scheduled maintenance tasks in production docs
```

## Performance Considerations

- **SQLite Optimization**: WAL mode, 64MB cache, proper indexing
- **Async Operations**: All network I/O is non-blocking
- **Rate Limiting**: Respect target site limits (1 request/second)
- **Caching**: Page configuration and static data caching
- **Memory Management**: Efficient data processing and cleanup

## Security Notes

- **No exposed secrets**: All sensitive data in environment variables
- **Rate limiting**: Built-in request throttling
- **Data validation**: Pydantic models for input validation
- **Error handling**: Graceful degradation without exposing internals
- **CORS configuration**: Properly configured for frontend access

## Future Development

### Planned Features:
- User authentication and profiles
- Advanced search and filtering
- Real-time data updates
- Mobile app version
- Analytics and insights

### Scaling Considerations:
- PostgreSQL migration for larger datasets
- Redis caching layer
- Distributed crawling
- CDN for static assets
- Load balancing for high traffic

---

Always prefer editing existing files over creating new ones. Follow the established patterns and maintain consistency with the existing codebase architecture.