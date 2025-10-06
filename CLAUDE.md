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
- `test_vcard.py` - Comprehensive test suite for vCard generation and QR code functionality
- `pyproject.toml` - Project dependencies and build configuration
- `Dockerfile` - Container configuration for deployment

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

### Testing
```bash
# macOS - requires DYLD_LIBRARY_PATH for zbar
DYLD_LIBRARY_PATH=/opt/homebrew/opt/zbar/lib:$DYLD_LIBRARY_PATH pytest test_vcard.py -v

# Linux - usually works without environment variables
pytest test_vcard.py -v
```

## Important Notes

### Dependencies
- Requires Python 3.11+
- Uses `uv` for fast package management
- QR code tests require the zbar system library (installed via brew/apt)

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

## Common Tasks

### Adding a new vCard field
1. Update the form in `app.py` (add input field)
2. Update `build_vcard()` function to handle the new field
3. Add test cases in `test_vcard.py`

### Modifying QR code generation
- QR code generation is in `generate_qr_code()` using segno
- Returns PNG bytes that can be embedded in HTML or downloaded
- Tests validate both generation and decoding

### Deployment
- Docker container runs on port 80
- Can be deployed to Dokku (see README.md)
- Includes healthcheck endpoint

## Testing Philosophy

Tests are organized into three classes:
1. `TestVCardGeneration` - vCard creation and parsing
2. `TestQRCodeGeneration` - QR code generation and scanning
3. `TestIntegration` - Full roundtrip workflows

All tests use realistic data and validate both format compliance and data integrity.
