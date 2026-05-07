# Contributing to Titanium

Thank you for your interest in contributing to the Titanium Enterprise AI Platform!

## Development Setup

1. **Fork and clone** the repository
2. **Install dependencies**: `make install`
3. **Set up Ollama**: `bash deployment/scripts/setup-ollama.sh`
4. **Seed memory**: `make seed`
5. **Start dev servers**: `make dev`

## Code Style

- **Python**: Follow PEP 8, use `ruff` for linting and formatting
- **TypeScript**: Strict mode, use ESLint with the provided config
- **Commits**: Use conventional commit messages (`feat:`, `fix:`, `docs:`, etc.)

## Running Tests

```bash
make test          # Run all tests
make test-backend  # Backend tests only
make test-frontend # Frontend tests only
make lint          # Run linters
make format        # Auto-format code
```

## Pull Request Process

1. Create a feature branch from `main`
2. Make your changes with tests
3. Ensure `make test` and `make lint` pass
4. Update documentation if needed
5. Submit a PR with a clear description

## Architecture Guidelines

- New services go in `backend/services/`
- New routers go in `backend/routers/`
- Agent tools go in `agents/tools/`
- React components go in `frontend/src/components/`
- Keep components focused and single-purpose

## Reporting Issues

- Use GitHub Issues for bugs and feature requests
- Include reproduction steps for bugs
- Tag with appropriate labels

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
