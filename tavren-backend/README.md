# Tavren Backend

A FastAPI-based backend for the Tavren platform, providing API endpoints for consent event tracking, wallet management, and buyer trust scoring.

## Getting Started

### Prerequisites

- Python 3.9 or higher
- PostgreSQL (for production) or SQLite (for development)
- Redis (optional, for caching)

### Installation

1. Clone the repository
   ```bash
   git clone https://github.com/yourusername/tavren.git
   cd tavren/tavren-backend
   ```

2. Create a virtual environment
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. For Linux/macOS users, make scripts executable
   ```bash
   chmod +x scripts/linux_setup.sh
   ./scripts/linux_setup.sh
   ```

6. Run the application
   ```bash
   uvicorn app.main:app --reload
   ```

The application will be available at http://localhost:8000.

API documentation is available at http://localhost:8000/docs.

## Architecture

The application follows a modular architecture with the following components:

- **Routers**: Separate modules for different API endpoints (static, consent, buyers, wallets)
- **Models**: SQLAlchemy ORM models for database entities
- **Schemas**: Pydantic models for request/response validation
- **Utils**: Helper functions for common operations
- **Exceptions**: Custom exception classes and handlers
- **Config**: Centralized configuration using pydantic-settings

## Project Structure

```
tavren-backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # Application entry point
│   ├── config.py            # Centralized configuration
│   ├── database.py          # Database connection setup
│   ├── models.py            # SQLAlchemy ORM models
│   ├── schemas.py           # Pydantic validation schemas
│   ├── exceptions/          # Custom exception handling
│   │   ├── __init__.py
│   │   ├── custom_exceptions.py
│   │   └── handlers.py
│   ├── routers/             # API route modules
│   │   ├── __init__.py
│   │   ├── static.py        # Static content routes
│   │   ├── consent.py       # Consent event endpoints
│   │   ├── buyers.py        # Buyer and offer endpoints
│   │   └── wallet.py        # Wallet and payout endpoints
│   ├── utils/               # Helper utilities
│   │   ├── __init__.py
│   │   ├── wallet.py        # Wallet helper functions
│   │   └── buyer_insights.py # Buyer trust calculations
│   └── static/              # Static files (HTML, JS, CSS)
└── tests/                   # Test directory
    ├── conftest.py          # Test fixtures and configuration
    └── test_main.py         # API tests
```

## Configuration

The application uses [pydantic-settings](https://docs.pydantic.dev/latest/usage/settings/) for configuration management. Settings are defined in `app/config.py`.

### Environment Variables

Create a `.env` file in the root directory (`tavren-backend/`) with the following variables. Adjust the values based on your local setup.

```dotenv
# Database connection URL (SQLAlchemy format)
# Example for SQLite (relative path):
DATABASE_URL=sqlite+aiosqlite:///./app/tavren_dev.db
# Example for PostgreSQL (requires psycopg2 or asyncpg):
# DATABASE_URL=postgresql+asyncpg://user:password@host:port/database

# Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
LOG_LEVEL=INFO

# Minimum amount required in wallet before a user can claim a payout
MINIMUM_PAYOUT_THRESHOLD=5.00

# Directory for static files (HTML, CSS, JS for dashboards)
STATIC_DIR=app/static
```

*   `DATABASE_URL`: Specifies the connection string for the database. Uses `sqlite+aiosqlite` for async SQLite support by default.
*   `LOG_LEVEL`: Sets the minimum severity level for log messages.
*   `MINIMUM_PAYOUT_THRESHOLD`: Defines the minimum balance a user must have to request a payout.
*   `STATIC_DIR`: Path to the directory containing static assets served by the application.

## Running the Application

### Development Server

To run the application in development mode:

```bash
# From the project root (tavren-backend/)
python -m app.main
```

Or using Uvicorn directly:

```bash
uvicorn app.main:app --reload
```

The API will be available at http://127.0.0.1:8000 and the API documentation at http://127.0.0.1:8000/docs.

### Using Docker Compose (Recommended for Development)

Docker Compose provides a way to run the application and its dependencies (like a PostgreSQL database) in isolated containers, closely mimicking a production setup.

1.  **Ensure Docker and Docker Compose are installed.**
2.  **Build and run the services**:
    ```bash
    # From the project root (tavren-backend/)
    docker-compose up --build
    ```
    *   The `--build` flag ensures the backend image is built before starting.
    *   Services will run in the foreground. Press `