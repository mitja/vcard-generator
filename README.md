# A vCard (VCF) Generator

A tiny FastHTML app that builds **vCard 3.0 (.vcf)** files from a basic MonsterUI form.  
No persistence, just generates and streams the file to your browser.

Live on [vcard-generator.mitja.app](https://vcard-generator.mitja.app).

## Features

- vCard 3.0 output with:
  - Name (including prefix/suffix), role, title, organization
  - Emails (work/home), phones (cell/work/home)
  - Addresses (home/work)
  - URL, note, birthday (YYYY-MM-DD)
- Clean, responsive UI with MonsterUI
- Zero database. Zero telemetry.

## Local Development

Prerequisites:

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) (Python package manager)

```bash
# 1) Create a virtual environment and install dependencies
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -e .

# 2) Run the app
python app.py
# or:
uvicorn app:app --reload

# 3) Open
open http://127.0.0.1:8000
```

## Testing

Prerequisites:

- Python 3.11+
- [uv](https://github.com/astral-sh/uv)
- [zbar](https://github.com/mchehab/zbar) library (for QR code reading in tests)

### Install test dependencies

```bash
# Install zbar system library
# macOS:
brew install zbar

# Linux (Debian/Ubuntu):
sudo apt-get install libzbar0

# Windows:
# Download and install from https://sourceforge.net/projects/zbar/

# Install Python dev dependencies
source .venv/bin/activate
uv pip install -e ".[dev]"
```

### Run tests

```bash
# Activate virtual environment
source .venv/bin/activate

# Run unit tests
DYLD_LIBRARY_PATH=/opt/homebrew/opt/zbar/lib:$DYLD_LIBRARY_PATH pytest test_vcard.py -v

# On Linux, you might not need DYLD_LIBRARY_PATH:
pytest test_vcard.py -v

# Run specific test class
pytest test_vcard.py::TestQRCodeGeneration -v

# Run a single test
pytest test_vcard.py::TestQRCodeGeneration::test_qr_code_scanning -v
```

## Integration Testing

Integration tests verify the complete Docker deployment, including HTTP endpoints, vCard generation, and QR code generation.

### Prerequisites

```bash
# Docker must be running
# Install integration test dependencies
source .venv/bin/activate
uv pip install -e ".[integration]"
```

### Run integration tests

```bash
# Using the test script (recommended)
./test_integration.sh

# Or directly with pytest
pytest test_integration.py -v

# Run specific test class
pytest test_integration.py::TestQRCodeGeneration -v
```

**Note:** Integration tests will:
- Build a Docker image (`vcard-generator:test`)
- Start a container on port 8889
- Run all HTTP endpoint tests
- Clean up the container when done
- Tests take ~1-2 minutes to complete

## Build and run as Docker container

```bash
# Build image
docker build -t vcard-generator:latest .

# Run container
docker run --rm -p 8888:80 vcard-generator:latest

# Open
open http://127.0.0.1:8888
```

## Deploy to Dokku host

Prerequisites

* You have a Dokku host ready (with a domain, DNS pointing to the host)
* You have aliased `dokku` like this `dokku='ssh dokku@mitja.app'`
* You want a public URL like `https://vcard-generator.mitja.app`

```bash
# 1) Create the Dokku app
dokku apps:create vcard-generator

# 2) Add Dokku remote (replace YOUR_DOKKU_HOST)
git remote add dokku dokku@YOUR_DOKKU_HOST:vcard-generator

# 3) Push to deploy
git push dokku main

# 4) Enable https (Let’s Encrypt)
dokku letsencrypt:enable vcard-generator

# 5) Check (should return HTTP/2 200)
curl -I https://vcard-generator.mitja.app
```