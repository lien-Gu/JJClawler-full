c# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python FastAPI web application called "jjclawer3" that provides basic HTTP endpoints. The project uses Poetry for dependency management and packaging.

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
poetry run uvicorn main:app --reload

# Or if in poetry shell
uvicorn main:app --reload
```

The application will be available at `http://127.0.0.1:8000` by default.

### Testing
Use the provided `test_main.http` file to test endpoints manually, or use curl/Postman for API testing.

## Architecture

- **main.py**: Contains the FastAPI application instance and all route handlers
- **pyproject.toml**: Project configuration, dependencies, and metadata managed by Poetry
- **test_main.http**: HTTP request file for manual API testing

## Dependencies

- FastAPI (>=0.115.13): Web framework for building APIs
- Uvicorn (>=0.34.3): ASGI server for running the FastAPI application
- Python >=3.13 required