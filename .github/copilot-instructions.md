# CodeCarbon Copilot Instructions

This repository contains multiple components for tracking and reducing CO2 emissions from computing. Here's what you need to know to navigate and contribute effectively.

## Repository Structure

### Main Components

1. **📦 codecarbon/** - Core Python package
   - Main library for tracking carbon emissions
   - CLI tools and utilities
   - Core emission tracking functionality

2. **🔌 carbonserver/** - API Backend
   - FastAPI-based REST API
   - PostgreSQL database integration
   - User management and data persistence
   - Run with: `hatch run api:docker` or `hatch run api:local`

3. **📊 dashboard/viz** - Python Dashboard (Dash-based)
   - Interactive dashboard using Dash/Plotly
   - Visualizes emission data from CSV files
   - Run with: `hatch run dashboard:run`

4. **🌐 webapp/** - Next.js Web Dashboard
   - Modern React/Next.js web application
   - Connects to the API backend
   - Run with: `cd webapp && pnpm dev`

### Key Directories

- **tests/** - Unit tests for the core package
- **docs/** - Sphinx documentation (build with `hatch run docs:build`)
- **examples/** - Usage examples and demos
- **deploy/** - Deployment configurations and scripts
- **requirements/** - Dependency specifications for different environments

## Development Setup

### Prerequisites
- Python 3.7+ (preferably 3.11+)
- Hatch (Python project manager): `pip install hatch`
- Node.js & pnpm (for webapp): `npm install -g pnpm` or `curl -fsSL https://get.pnpm.io/install.sh | sh -`
- Docker (for API development)

### Quick Start

1. **Core Package Development:**
   ```bash
   # Run tests
   hatch run test:package

   # Run specific test
   hatch -e test.py3.11 run pytest tests/test_emissions_tracker.py

   # Lint and format
   hatch run dev:lint
   hatch run dev:format
   ```

2. **API Development:**
   ```bash
   # Start API with Docker (recommended)
   hatch run api:docker

   # Or run locally (requires PostgreSQL setup)
   hatch run api:local

   # Test API
   hatch run api:test-unit
   hatch run api:test-integ
   ```

3. **Dashboard Development:**
   ```bash
   # Python dashboard
   hatch run dashboard:run

   # Next.js webapp
   cd webapp
   pnpm install
   pnpm dev
   ```

## Testing Strategy

### Core Package Tests
- **Unit tests**: `tests/test_*.py` - Test individual components
- **Integration tests**: Include real hardware testing with `CODECARBON_ALLOW_MULTIPLE_RUNS=True`
- **Run specific tests**: `hatch -e test.py3.11 run pytest tests/test_specific.py`

### API Tests
- **Unit tests**: `hatch run api:test-unit` - Test business logic
- **Integration tests**: `hatch run api:test-integ` - Test with database
- **See**: `carbonserver/tests/TESTING.md` for detailed testing guide

### Manual Testing
- **Stress testing**: Use `7z b` for CPU or gpu-burn for GPU testing
- **CLI testing**: Use examples in `examples/` directory
- **Monitor with**: `nvidia-smi` for GPU metrics comparison

## Common Development Patterns

### Adding New Features
1. **Check existing tests** in `tests/` for similar functionality
2. **Add unit tests** first (test-driven development)
3. **Update documentation** if public interface changes
4. **Follow coding style**: Use `hatch run dev:format` and `hatch run dev:lint`

### API Development
1. **Follow FastAPI patterns** - see routers in `carbonserver/carbonserver/api/routers/`
2. **Use dependency injection** - see `carbonserver/container.py`
3. **Database migrations** - use Alembic (see `carbonserver/carbonserver/database/alembic/`)
4. **Test with Postman** - collection in `carbonserver/tests/postman/`

### Dashboard Development
1. **Python Dashboard**: Uses Dash + Plotly, see `codecarbon/viz`
2. **Next.js Dashboard**: Modern React components in `webapp/src/`
3. **Connect to API**: Set `CODECARBON_API_URL=http://localhost:8008` for local development

## Environment Management

### Hatch Environments
```bash
# List all environments
hatch env show

# Main environments:
# - default: Core package development
# - test: Testing with multiple Python versions
# - dev: Development tools (linting, formatting)
# - api: API development and testing
# - dashboard: Dashboard development
# - docs: Documentation building
```

### Configuration Files
- **pyproject.toml**: Main project configuration
- **.codecarbon.config**: Runtime configuration for API connection
- **docker-compose.yml**: Local development with PostgreSQL
- **requirements/**: Pinned dependencies for different environments

## Documentation and Help

### Key Documentation Files
- **CONTRIBUTING.md**: Detailed contribution guidelines and setup
- **README.md**: Project overview and quickstart
- **carbonserver/README.md**: API architecture and database schema
- **webapp/README.md**: Next.js dashboard setup
- **carbonserver/tests/TESTING.md**: Comprehensive testing guide

### VS Code Debugging
The repository includes VS Code launch configurations in CONTRIBUTING.md for:
- Debugging current Python file
- Running pytest with debugger
- Testing codecarbon CLI monitor

### Getting Help
- **FAQ**: https://mlco2.github.io/codecarbon/faq.html
- **Documentation**: https://mlco2.github.io/codecarbon/
- **Issues**: https://github.com/mlco2/codecarbon/issues

## Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   codecarbon    │    │   carbonserver  │    │   dashboards    │
│   (package)     │───▶│     (API)       │◀───│  (2 versions)   │
│                 │    │                 │    │                 │
│ • CLI tools     │    │ • FastAPI       │    │ • Dash (Python) │
│ • Tracking core │    │ • PostgreSQL    │    │ • Next.js (Web) │
│ • Data output   │    │ • Authentication│    │ • Visualization │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

The package can work standalone (offline mode) or connect to the API for cloud features and dashboard visualization.

## Tips for Effective Development

1. **Start with tests**: Run existing tests first to understand current state
2. **Use examples**: Check `examples/` directory for usage patterns
3. **Environment isolation**: Use hatch environments to avoid conflicts
4. **Incremental development**: Test frequently with `hatch run test:package`
5. **Check CI**: Ensure your changes pass the same checks as GitHub Actions
6. **Read architecture docs**: Understand the emission calculation methodology in docs/

Remember: CodeCarbon is about measuring and reducing computing emissions. Every contribution helps make computing more sustainable! 🌱
