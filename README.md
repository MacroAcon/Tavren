# Tavren Backend

Tavren Backend is a powerful FastAPI-based service that powers the Tavren platform's core infrastructure for privacy-focused data consent management, trust scoring, and micro-compensation systems.

## Overview

The Tavren Backend is responsible for:

- **Consent Management**: Processing and storing user consent flows and data posture
- **Trust Scoring**: Evaluating and ranking data buyers based on privacy practices
- **Wallet Operations**: Tracking user earnings and managing micro-compensation
- **Payout Processing**: Handling automated payouts through the payout processor
- **LLM & Agent Integration**: Supporting AI-powered features and agent-to-agent communication
- **Data Packaging**: Secure bundling and delivery of user-approved data

## Project Structure

```
app/
├── routers/         # API route definitions and endpoint handlers
├── services/        # Business logic implementation
├── schemas/         # Pydantic models for request/response validation
├── models.py        # SQLAlchemy ORM models for database tables
├── database.py      # Database connection and session management
├── auth.py          # Authentication and authorization logic
├── config.py        # Configuration settings and environment variables
├── constants/       # Application constants and enumerations
├── errors/          # Error handling and custom exceptions
├── logging/         # Logging configuration and utilities
├── utils/           # Helper functions and utility modules
├── middleware.py    # FastAPI middleware components
├── main.py          # Application entry point and router registration
└── run_payout_processor.py  # Script for processing user payouts
```

## Getting Started

### Prerequisites
- Python 3.8+
- Virtual environment tool

### Environment Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/your-org/tavren-backend.git
   cd tavren-backend
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: .\venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Copy the environment template:
   ```bash
   cp .env.example .env
   ```
   
5. Edit `.env` with your configuration settings

### Database Setup

Tavren supports both SQLite (default for development) and PostgreSQL:

**SQLite (default)**:
- No additional setup required
- Development database will be created as `tavren_dev.db`

**PostgreSQL**:
- Install PostgreSQL
- Create a database
- Update the `DATABASE_URL` in your `.env` file

### Running in Dev Mode

Start the development server:

```bash
python -m app.main
```

This will:
- Create necessary database tables
- Start the API server on http://localhost:8000
- Enable hot reloading for code changes
- Output logs to the console

Access the API documentation:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Development Notes

- The development database (`tavren_dev.db`) contains test data for development
- API endpoints have rate limiting configured via the `slowapi` package
- Hot reloading is enabled in development mode
- Log level can be configured in `.env` (default: INFO)

## Testing

Run the test suite with pytest:

```bash
pytest
```

Run tests with coverage report:

```bash
pytest --cov=app tests/
```

The test suite includes:
- Unit tests for core functionality
- Integration tests for API endpoints
- Mock services for external dependencies
- Database fixtures for consistent test environments

## Docker Support

Build and run with Docker:

```bash
docker build -t tavren-backend .
docker run -p 8000:8000 -v $(pwd)/.env:/app/.env tavren-backend
```

Or use Docker Compose for a complete development environment:

```bash
docker-compose up --build
```

## Related Projects

- [Tavren Frontend](../tavren-frontend/): React-based user interface
- [Tavren Documentation](../docs/): Comprehensive project documentation

## License

This project is licensed under the terms specified in [LICENSE.md](../LICENSE.md). 