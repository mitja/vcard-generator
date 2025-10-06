# Claude Code Context

This file provides context for Claude Code when working on this project.

## Project Overview

A minimal FastHTML web application that generates vCard 3.0 (.vcf) files with QR codes. Built with FastHTML and MonsterUI for a clean, responsive interface.

## Architecture

- **Framework**: FastHTML (Python web framework)
- **UI**: MonsterUI (Tailwind-based component library)
- **QR Code Generation**: segno (pure Python QR code generator)
- **vCard Parsing**: vobject (for testing)
- **Testing**: pytest with qreader for QR code validation

## Key Files

- `app.py` - Main application file with FastHTML routes and vCard generation logic
- `test_vcard.py` - Unit tests for vCard generation and QR code functionality
- `test_integration.py` - Integration tests for Docker deployment and HTTP endpoints
- `test_integration.sh` - Convenience script for running integration tests
- `pyproject.toml` - Project dependencies and build configuration
- `Dockerfile` - Container configuration for deployment
- `.github/workflows/tests.yml` - CI/CD workflow for unit and integration tests

## Development Workflow

### Setup
```bash
uv venv
source .venv/bin/activate
uv pip install -e ".[dev]"
```

### Running the app
```bash
python app.py
# or
uvicorn app:app --reload
```

### Unit Testing
```bash
# macOS - requires DYLD_LIBRARY_PATH for zbar
DYLD_LIBRARY_PATH=/opt/homebrew/opt/zbar/lib:$DYLD_LIBRARY_PATH pytest test_vcard.py -v

# Linux - usually works without environment variables
pytest test_vcard.py -v
```

### Integration Testing
```bash
# Install integration test dependencies
uv pip install -e ".[integration]"

# Run integration tests (builds Docker image and tests deployment)
./test_integration.sh
# or
pytest test_integration.py -v
```

## Important Notes

### Dependencies
- Requires Python 3.11+
- Uses `uv` for fast package management
- Unit tests require the zbar system library (installed via brew/apt)
- Integration tests require Docker to be running
- Separate dependency groups: `dev` (unit tests), `integration` (Docker tests)

### vCard Generation
- Implements vCard 3.0 specification
- Supports: names (with prefix/suffix), organization, title, role, emails (work/home), phones (cell/work/home), addresses (work/home), URL, birthday, notes
- All fields are optional except first/last name

### QR Code Testing
- Uses `qreader` package which combines YOLOv8 detection with pyzbar decoding
- Requires converting PIL Images to RGB numpy arrays before decoding
- Tests validate full roundtrip: data → vCard → QR code → decoded vCard → parsed data

### Build Configuration
- Uses setuptools with explicit `py-modules = ["app"]` to avoid test file inclusion
- Separates runtime deps from dev deps (`[project.optional-dependencies]`)
- Three dependency groups:
  - Main: FastHTML, MonsterUI, uvicorn, segno (runtime)
  - `dev`: pytest, vobject, pillow, qreader (unit testing)
  - `integration`: pytest, requests (Docker/HTTP testing)
- Dockerfile uses `pyproject.toml` as single source of truth for dependencies

## Common Tasks

### Adding a new vCard field
1. Update the form in `app.py` (add input field)
2. Update `build_vcard()` function to handle the new field
3. Add test cases in `test_vcard.py`
4. Run unit tests to verify
5. Run integration tests to ensure HTTP endpoints still work

### Modifying QR code generation
- QR code generation is in `generate_qr_code()` using segno
- Returns PNG bytes that can be embedded in HTML or downloaded
- Unit tests validate both generation and decoding with qreader
- Integration tests verify HTTP endpoint returns valid PNG

### Testing Docker builds locally
```bash
# Quick check
./test_integration.sh

# Or step by step
docker build -t vcard-generator:test .
docker run --rm -p 8888:80 vcard-generator:test
curl http://localhost:8888
```

### Pre-deployment checklist
1. Run unit tests: `pytest test_vcard.py -v`
2. Run integration tests: `./test_integration.sh`
3. Verify Docker build works
4. Check GitHub Actions passed
5. Deploy to Dokku: `git push dokku main`

### Deployment
- Docker container runs on port 80
- Can be deployed to Dokku (see README.md)
- Includes healthcheck endpoint
- Integration tests verify deployment readiness

## Testing Philosophy

### Unit Tests (`test_vcard.py`)
Tests are organized into three classes:
1. `TestVCardGeneration` - vCard creation and parsing
2. `TestQRCodeGeneration` - QR code generation and scanning
3. `TestIntegration` - Full roundtrip workflows (data → vCard → QR → decode)

All tests use realistic data and validate both format compliance and data integrity.

### Integration Tests (`test_integration.py`)
Tests verify the complete Docker deployment stack:
1. `TestDockerDeployment` - Container health and logs
2. `TestHTTPEndpoints` - Homepage accessibility and content
3. `TestVCardGeneration` - vCard file generation via HTTP
4. `TestQRCodeGeneration` - QR code PNG generation via HTTP
5. `TestDependencies` - Verify all packages installed in container

Integration tests:
- Build Docker image once (module-scoped fixture)
- Run container on port 8889 to avoid conflicts
- Test actual HTTP endpoints with `requests` library
- Automatically clean up container after tests
- Take ~1-2 minutes to complete
- Should be run before deploying to production
