# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Vulnerability-Lookup is a platform for correlating vulnerabilities from various sources, managing Coordinated Vulnerability Disclosure (CVD), and providing a collaborative space for security advisories. It operates with a modular feeder system that imports vulnerabilities from 30+ sources including national vulnerability databases, CSAF providers, and community databases.

## Key Commands

### Setup and Installation
```bash
# Install dependencies
poetry install

# Initialize database (first time only)
poetry run flask --app website.app db_init
poetry run flask --app website.app db stamp head

# Update the system (including dependencies, config, database migrations)
poetry run update
```

### Running the Application
```bash
# Start all services (backend Redis/Kvrocks, feeders, website)
poetry run start

# Start individual components
poetry run run_backend --start    # Start Redis cache and Kvrocks storage
poetry run feeders_manager --start # Start all enabled feeders
poetry run start_website           # Start Flask website

# Stop all services
poetry run stop
```

### Feeders Management
```bash
# Manage feeders (start/stop all enabled feeders)
poetry run feeders_manager --start
poetry run feeders_manager --stop

# Run individual feeders manually
poetry run nvd_importer
poetry run cvelist_importer
poetry run github_importer
# See pyproject.toml [project.scripts] for all available feeder commands
```

### Database Operations
```bash
# Create admin user
poetry run flask --app website.app create_admin

# Create regular user
poetry run flask --app website.app create_user

# List users
poetry run flask --app website.app user_list

# Update MISP warning lists
poetry run flask --app website.app update_warninglists

# Database migrations
poetry run flask --app website.app db upgrade
poetry run flask --app website.app db_backup
```

### Testing
```bash
# Run all tests
poetry run pytest

# Run specific test file
poetry run pytest tests/test_web.py

# Run with verbose output
poetry run pytest -v
```

### Code Quality
```bash
# Type checking
mypy .

# Pre-commit hooks (configured in .pre-commit-config.yaml)
pre-commit run --all-files
```

### Documentation
```bash
# Build documentation
cd docs
poetry run make html
```

## Architecture

### Three-Tier System

1. **Storage Layer (Kvrocks)**: Primary persistent storage for vulnerabilities, running on TCP (default port 10002). Uses Redis-compatible key-value store (Kvrocks) for scalability.

2. **Cache Layer (Redis)**: Fast temporary cache, runs on Unix socket at `cache/cache.sock`. Handles pub/sub messaging and temporary data.

3. **Web Layer (Flask)**: Gunicorn-served Flask application with Blueprint-based modular architecture, running on port 10001 by default.

### Core Components

**VulnerabilityLookup Core** (`vulnerabilitylookup/vulnerabilitylookup.py`):
- Main class providing abstraction over storage and cache layers
- Methods: `get_vulnerability()`, `get_vulnerability_meta()`, `get_linked_vulnerabilities()`
- Connection pooling for both storage and cache Redis instances

**Feeder System** (`vulnerabilitylookup/feeders/`):
- All feeders inherit from `AbstractFeeder` base class
- CSAF-based feeders use `CSAFGeneric` parent class
- Each feeder has: main module (e.g., `nvd.py`), logging config (`nvd_logging.json`), and bin script (`bin/nvd_fetcher.py`)
- Feeders publish to Redis pub/sub channels when new vulnerabilities are imported
- Configured in `config/modules.cfg` with per-feeder settings

**Website** (`website/`):
- Flask application with Blueprints (`website/web/views/`)
- API v1 at `website/web/api/v1/`
- SQLAlchemy models in `website/models/`
- User authentication with Flask-Login and Flask-Principal
- PostgreSQL for user accounts, comments, bundles, sightings, watchlists
- Templates use Bootstrap-Flask

**Pub/Sub Streaming** (`website/stream/`):
- Real-time updates for comments, bundles, and sightings
- Listeners register on Redis pub/sub channels
- Global subscription mechanism for server-side message processing

### Data Flow

1. Feeders fetch vulnerability data from external sources
2. Data normalized and stored in Kvrocks with cross-references (e.g., `cve-2024-1234:link` contains linked vulnerability IDs)
3. Metadata stored separately (e.g., CVSS scores, EPSS data)
4. Redis cache provides quick lookups and pub/sub notifications
5. Web interface queries VulnerabilityLookup core which abstracts storage access
6. API provides REST access to vulnerability data

### Key Storage Patterns

- Vulnerabilities stored by ID (lowercase): `cve-2024-1234` → JSON blob
- Metadata: `cve-2024-1234:meta` → hash mapping meta types to UUIDs
- Links: `cve-2024-1234:link` → set of related vulnerability IDs
- Source indexes: `index:<source_name>` → sorted set of vulnerability IDs
- Last update tracking: `last_updates` hash with timestamps per source

## Configuration

Configuration files are in `config/` directory:

- `generic.json`: Core settings (database ports, paths, logging level, instance identity)
- `modules.cfg`: Feeder configurations (which feeders enabled, API keys, log levels)
- `website.py`: Flask settings (sources list, module toggles, secret keys)
- `stream.json`: Pub/Sub streaming configuration
- `logging.json`: Logging configuration

Sample files (`.sample` suffix) are templates. Copy and customize for your instance.

## Adding a New Vulnerability Source

Follow `new_source.md` for detailed instructions. High-level steps:

1. Create feeder class in `vulnerabilitylookup/feeders/<name>.py` inheriting from `AbstractFeeder` (or `CSAFGeneric` for CSAF sources)
2. Create logging config `vulnerabilitylookup/feeders/<name>_logging.json`
3. Create bin script in `bin/<name>.py` with `main()` function
4. Add entry to `pyproject.toml` under `[project.scripts]`
5. Add feeder config to `config/modules.cfg.sample`
6. If GitHub source, add as git submodule: `git submodule add --name <name> <repo> vulnerabilitylookup/feeders/<name>`
7. Update web interface: add to `config/website.py.sample` and update templates in `website/web/templates/`

## Development Notes

- Python 3.10+ required
- Uses Poetry for dependency management (requires Poetry >= 1.3.0)
- Type hints enforced with mypy (strict configuration in `pyproject.toml`)
- Ruff for linting (line length: 140 chars, auto-fix enabled)
- Pre-commit hooks for code quality (pyupgrade for Python 3.8+ syntax)
- Kvrocks must be running before application starts (checked in `run_backend.py`)
- When testing feeders, check Kvrocks with `redis-cli` to verify data structure: `SMEMBERS <vuln-id>:link`

## Project Scripts Structure

All entry points defined in `pyproject.toml` under `[project.scripts]`:
- Service management: `start`, `stop`, `shutdown`, `update`, `restart_website`
- Backend: `run_backend`, `start_website`, `feeders_manager`
- Importer scripts: Named as `<source>_importer` (e.g., `nvd_importer`, `github_importer`)
- Database tools: `dump`, `index_cwe`

## Important Paths

- `bin/`: Entry point scripts for CLI commands
- `vulnerabilitylookup/`: Core library and feeder implementations
- `website/`: Flask web application
  - `website/web/views/`: Blueprint view controllers
  - `website/web/api/v1/`: REST API endpoints
  - `website/models/`: SQLAlchemy database models
  - `website/web/templates/`: Jinja2 templates
- `config/`: Configuration files (copy `.sample` files and customize)
- `storage/`: Kvrocks data directory and startup script
- `cache/`: Redis cache data directory and startup script
- `tests/`: Pytest test suite with fixtures in `conftest.py`
- `docs/`: Sphinx documentation (build with `make html`)

## Testing Environment

Tests use pytest with custom fixtures (`tests/conftest.py`):
- `app`: Session-wide Flask application
- `db`: Session-wide test database (PostgreSQL)
- `session`: Function-scoped database session with transaction rollback

Environment variable `TESTING=gh_action` is set during test runs (configured in `pyproject.toml`).
