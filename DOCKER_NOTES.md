# Docker Setup Notes

## Playwright Browser Installation

For the MVP Docker setup, Playwright browser installation is skipped during the Docker build to avoid dependency conflicts between Debian Trixie (used by python:3.11-slim) and Playwright's Ubuntu-based dependencies.

### Options to Enable Playwright

#### Option 1: Install at Runtime (Recommended for MVP)
Once containers are running, install Playwright browsers:

```bash
# Inside the backend container
docker exec -it aeo_backend playwright install chromium

# Inside the worker container  
docker exec -it aeo_worker playwright install chromium
```

#### Option 2: Use Different Base Image
Change `backend/Dockerfile` to use an older Python image:

```dockerfile
FROM python:3.11-bullseye
```

Then uncomment the Playwright install line:
```dockerfile
RUN playwright install-deps && playwright install chromium
```

#### Option 3: Manual System Dependencies
Install compatible system packages for Debian Trixie before Playwright installation.

### Alternative: Use HTTP-Only Fetching
For initial testing, you can use simple HTTP requests instead of Playwright:

```python
import requests
response = requests.get(url)
html = response.text
```

This works for static pages but won't execute JavaScript.

## Current Setup

The MVP Docker setup focuses on getting the core infrastructure running:
- ✅ MongoDB
- ✅ Redis
- ✅ FastAPI backend (without crawler)
- ✅ Celery worker
- ✅ Next.js frontend

The crawler/Playwright can be added once the foundation is stable.

## Production Setup

For production, consider:
1. Using a dedicated crawler service with Playwright pre-installed
2. Using cloud-based browser automation (Browserless, Playwright as a Service)
3. Building custom Docker image with fixed system dependencies

