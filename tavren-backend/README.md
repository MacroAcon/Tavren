# Tavren Backend

A FastAPI-based backend for the Tavren platform, providing API endpoints for consent event tracking, wallet management, and buyer trust scoring.

## Setup

Follow these steps to set up the project locally:

1.  **Clone the repository** (if you haven't already):
    ```bash
    git clone <your-repo-url>
    cd tavren-backend
    ```

2.  **Create and activate a virtual environment**:
    *   On macOS/Linux:
        ```bash
        python3 -m venv venv
        source venv/bin/activate
        ```
    *   On Windows:
        ```bash
        python -m venv venv
        .\venv\Scripts\activate
        ```

3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Create an environment file**:
    *   Copy the example environment file (if one exists) or create a new file named `.env` in the `tavren-backend/` directory.
    *   Add the necessary environment variables (see "Environment Variables" section below).

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
    *   Services will run in the foreground. Press `Ctrl+C` to stop.
    *   To run in detached mode (background), use `docker-compose up -d --build`.
3.  **Accessing the application**:
    *   API: [http://localhost:8000](http://localhost:8000)
    *   Swagger Docs: [http://localhost:8000/docs](http://localhost:8000/docs)
    *   PostgreSQL DB (if needed for inspection): Connect to `localhost:5433` using the credentials in `docker-compose.yml` (user: `tavren_user`, password: `tavren_password`, db: `tavren_db`).
4.  **Stopping the services**:
    ```bash
    # If running in foreground, press Ctrl+C
    # If running in detached mode:
    docker-compose down
    ```

## Testing

The project uses `pytest` for testing. Tests are located in the `tests/` directory.

### Running Tests Locally

Tests utilize an in-memory SQLite database by default when run locally without Docker.

```bash
# Ensure virtual environment is active and requirements installed
pytest
```

### Running Tests with Docker Compose

This method runs tests against the PostgreSQL database defined in `docker-compose.yml`, providing a more integration-focused test environment.

1.  **Ensure Docker Compose services are not already running** (`docker-compose down` if necessary).
2.  **Run the test command**: This command starts the database container, waits for it to be healthy, then runs `pytest` inside a temporary backend container linked to the database.
    ```bash
    # From the project root (tavren-backend/)
    docker-compose run --rm backend pytest tests
    ```
    *   `--rm`: Removes the temporary container after tests finish.
    *   This uses the `DATABASE_URL` configured in `docker-compose.yml`.
3.  **Cleanup**: The database container will stop automatically after the tests finish because the `backend` service it depends on exits.

## API Documentation

When the application is running, you can access the interactive API documentation at:

- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

## Future Improvements

### Deployment

- Add Dockerfile and docker-compose.yml for containerization
- Configure CI/CD pipeline for automated testing and deployment
- Create deployment configurations for popular cloud platforms

### Technical Improvements

- Add async support using SQLAlchemy 2.0's async features
- Implement more advanced caching strategies
- Add rate limiting for public-facing endpoints
- Implement comprehensive metrics collection
- Add health check endpoints

### Features

- Implement user authentication and authorization
- Add support for webhooks for event-driven architecture
- Create admin dashboard for managing consent events and payouts

## Continuous Integration (CI)

This project uses GitHub Actions for Continuous Integration. The workflow is defined in `.github/workflows/ci.yml`.

On every push or pull request to the `main` or `develop` branches, the CI pipeline automatically performs the following:

1.  **Checks out the code.**
2.  **Builds the Docker image.**
3.  **Starts a PostgreSQL container using Docker Compose.**
4.  **Waits for the database to be healthy.**
5.  **Runs the `pytest` test suite** inside a Docker container connected to the test database.
6.  **Runs the `ruff` linter** inside a Docker container to check code style and quality.
7.  **Cleans up Docker Compose services.**

This ensures that code changes are automatically tested and linted before merging.

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Commit your changes (`git commit -am 'Add new feature'`)
4. Push to the branch (`git push origin feature/your-feature`)
5. Create a new Pull Request 