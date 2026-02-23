# Deploy & CI/CD

## Repo ready to push?

Before pushing and relying on CI/CD:

| Check | Notes |
|-------|--------|
| `models/trained/` exists | At least `.gitkeep` (or real `.pkl`) so `COPY models/trained/` in Dockerfiles succeeds. |
| No secrets in repo | `.env.dev` / `.env` are in `.gitignore`; never commit TMDB or Docker Hub tokens. |
| GitHub secrets (for Docker Hub) | In repo **Settings → Secrets and variables → Actions** add: `DOCKERHUB_USERNAME`, `DOCKERHUB_TOKEN`. |
| VERSION file | Present at repo root (e.g. `1.0.1`). Used for `:v{VERSION}` and `:latest` on push to `main`. |

**Workflow DAG (4 jobs):** `check` → `set-version` → `push-api` and `push-ui` (parallel). Both images are pushed to **GHCR** and **Docker Hub** with the same tags.

**Image names (align with `scripts/test-docker.sh`):**
- Local test: `movie-recommendation-api:local`, `movie-recommendation-ui:local`
- GHCR: `ghcr.io/<owner>/<repo>/api`, `ghcr.io/<owner>/<repo>/ui`
- Docker Hub: `docker.io/<DOCKERHUB_USERNAME>/movie-recommendation-api`, `movie-recommendation-ui`

---

## 1. Test Docker locally

From repo root (image names match CI: `movie-recommendation-api`, `movie-recommendation-ui`):

```bash
# API only (port 8000)
docker build -t movie-recommendation-api:local -f Dockerfile .
docker run -d -p 8000:8000 -v $(pwd)/models/trained:/app/models/trained:ro movie-recommendation-api:local
curl http://localhost:8000/health

# UI only (port 8501)
docker build -t movie-recommendation-ui:local -f ui/Dockerfile .
docker run -d -p 8501:8501 -v $(pwd)/models/trained:/app/models/trained:ro movie-recommendation-ui:local
# Open http://localhost:8501

# Both with Compose
docker compose build && docker compose up -d
# API: 8000, UI: 8501
```

Or run the script (builds, runs, health-check, cleans up):

```bash
chmod +x scripts/test-docker.sh
./scripts/test-docker.sh
```

## 2. DVC pipeline

Pipeline DAG: `data` → `features` → `train` (same as `run_pipeline.py`).

```bash
# Ensure data/raw/top10K-TMDB-movies.csv exists (or dvc pull)
dvc repro
```

Track large data/model files with DVC:

```bash
dvc add data/raw/top10K-TMDB-movies.csv   # if you want to version raw data
dvc add models/trained/*.pkl              # or track trained artifacts
```

## 3. GitHub: versioned image builds (GHCR + Docker Hub)

- **Push to `main`**: runs DAG (check → set-version → push-api, push-ui); pushes to **GHCR** and **Docker Hub** as `:latest` and `:v{VERSION}` (from `VERSION` file).
- **Push tag `v*`** (e.g. `git tag v1.0.1 && git push origin v1.0.1`): same DAG; images tagged `:{tag}` (e.g. `v1.0.1`).

**Required GitHub secrets** (Settings → Secrets and variables → Actions):

- `DOCKERHUB_USERNAME`: your Docker Hub username.
- `DOCKERHUB_TOKEN`: Docker Hub access token (or password). Create at https://hub.docker.com/settings/security.

**Resulting images** (replace `OWNER/REPO` and `DH_USER`):

- GHCR: `ghcr.io/OWNER/REPO/api`, `ghcr.io/OWNER/REPO/ui` with tags `:latest`, `:v1.0.1`, etc.
- Docker Hub: `docker.io/DH_USER/movie-recommendation-api`, `docker.io/DH_USER/movie-recommendation-ui` with same tags.

Bump version before merging: edit `VERSION` (e.g. `1.0.2`). For release builds, create and push a tag:

```bash
echo "1.0.2" > VERSION
git add VERSION && git commit -m "chore: bump VERSION to 1.0.2"
git tag v1.0.2 && git push origin main --tags
```

## 4. Order of operations

1. Test API and UI Docker images locally (and optionally `docker compose up`).
2. Add DVC and run `dvc repro` when you have raw data; optionally `dvc add` and push to DVC remote.
3. Push to GitHub; ensure `models/trained/` has at least `.gitkeep` (or real `.pkl` files) so Docker build COPY succeeds.
4. After checks pass, images are built and pushed with version tags.
