# A vCard (VCF) Generator

A tiny FastHTML app that builds **vCard 3.0 (.vcf)** files from a basic MonsterUI form.  
No persistence, just generates and streams the file to your browser.

## Features

- vCard 3.0 output with:
  - Name (including prefix/suffix), role, title, organization
  - Emails (work/home), phones (cell/work/home)
  - Addresses (home/work)
  - URL, note, birthday (YYYY-MM-DD)
- Clean, responsive UI with MonsterUI
- Zero database. Zero telemetry.

## Local Development

### Prereqs
- Python 3.11+
- [uv](https://github.com/astral-sh/uv) (Python package manager)

### Setup & run

```bash
# 1) Install deps with uv (system or venv, your choice)
uv pip install --system python-fasthtml MonsterUI uvicorn

# 2) Run the app
python app.py
# or:
uvicorn app:app --reload

# 3) Open
open http://127.0.0.1:8000
```

## Build and run as Docker container

```bash
# Build image
docker build -t vcard-generator:latest .

# Run container
docker run --rm -p 8000:8000 vcard-generator:latest

# Open
open http://127.0.0.1:8000
```

## Deployment on Dokku

These steps assume:

* You have a Dokku host ready (with a domain, DNS pointing to the host)
* You want a public URL like https://vcard-generator.mitja.app (used here)

### Create the Dokku app

```bash
dokku apps:create vcard-generator
```

### Set the domain

```bash
# Add the custom domain
dokku domains:add vcard-generator vcard-generator.mitja.app
# (Optional) Remove the default subdomain if present
# dokku domains:clear vcard-generator && dokku domains:add vcard-generator vcard-generator.mitja.app
```

Ensure your DNS has an A (and/or AAAA) record pointing vcard-generator.mitja.app to your Dokku host.

### 3) Configure proxy port mapping

Our app listens on 8000 inside the container; map it to HTTP(80):

```bash
dokku proxy:ports-set vcard-generator http:80:8000
```

### Enable HTTPS (Let’s Encrypt)

```bash
dokku config:set vcard-generator DOKKU_LETSENCRYPT_EMAIL=you@mitja.app
dokku letsencrypt:enable vcard-generator
# auto-renew
dokku letsencrypt:cron-job --add
```

### Add the dokku host as git remote

```bash
# Add Dokku remote (replace host)
git remote add dokku dokku@YOUR_DOKKU_HOST:vcard-generator
```

### Git Push to deploy

```bash
git push dokku main
```

### Check

```curl -I https://vcard-generator.mitja.app```