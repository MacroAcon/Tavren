# Tavren Backend Documentation

This directory contains comprehensive documentation for the Tavren backend services and APIs.

## Documentation Structure

| Document | Description |
|----------|-------------|
| API.md | API endpoints, request/response formats, and authentication details |
| ARCHITECTURE.md | System architecture, component interactions, and data flow |
| DEPLOYMENT.md | Deployment procedures for various environments |
| DEVELOPMENT_SETUP.md | Local development environment setup and best practices |
| TROUBLESHOOTING.md | Common issues and their solutions |

## Development Documentation

For developers working on the Tavren backend, the most important documents to review are:

1. [Development Setup Guide](../../docs/DEVELOPMENT_SETUP.md) - Environment setup with virtual environment conventions
2. [API Documentation](../../docs/API.md) - Current API specifications and usage
3. [Architecture Documentation](../../docs/ARCHITECTURE.md) - System design and component relationships

## Standards and Conventions

The Tavren project follows these documentation standards:

- Documentation is written in Markdown format
- Code examples use syntax highlighting with triple backticks
- API examples include both request and response examples
- Configuration samples use environment variable notation consistent with `.env.example`
- Diagrams are stored in the `diagrams/` directory and referenced in the documentation

## Contributing to Documentation

When adding or updating documentation:

1. Maintain the existing format and style
2. Update the table of contents when adding new sections
3. Add examples where applicable
4. Cross-reference related documentation
5. Keep paths and links relative to enable relocating documentation

## Technical Docs vs. User Docs

- Technical documentation (for developers) is stored in this directory
- User-facing documentation is maintained in the main `/docs` directory
- API documentation serves both technical and integration audiences 