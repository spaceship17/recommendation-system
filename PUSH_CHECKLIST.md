# Pre-push checklist (security & what to commit)

## 1. No secrets in repo

Before **every** push, confirm no env or keys are staged:

```bash
# Must show ".env.dev" is ignored (do not commit)
git check-ignore -v .env.dev

# Must NOT list .env.dev or any file under .env
git status --short
git diff --cached --name-only
```

**Never add:** `.env`, `.env.dev`, `.env.prod`, or any file containing `TMDB_API_KEY`, `DOCKERHUB_TOKEN`, or other secrets.

## 2. What to push (recommended adds)

**Stage MLOps / app (safe to commit):**
```bash
git add .dockerignore
git add .env.example
git add .github/
git add .gitignore
git add Dockerfile
git add docker-compose.yaml
git add dvc.yaml
git add VERSION
git add configs/
git add run_pipeline.py
git add scripts/
git add src/
git add ui/
git add requirements.txt
git add README.md
git add DEPLOY.md
git add PUSH_CHECKLIST.md
```

**Stage model dir (structure only; .pkl are gitignored):**
```bash
git add models/
# (only non-.pkl files, e.g. README, .gitkeep)
```

**Deletions (if you intend to remove these):**
```bash
git add -u
# then review: git status
```

**Do not add (or remove if already staged):**
- `.env`, `.env.dev`, `.env.prod`, or any `.env*` with real keys
- `*.pkl` (large; use DVC or deploy mount)
- `data/` (raw/processed; use DVC if needed)

## 3. One-shot safe add (then review)

```bash
git add .dockerignore .env.example .github/ .gitignore Dockerfile docker-compose.yaml dvc.yaml VERSION configs/ run_pipeline.py scripts/ src/ ui/ requirements.txt README.md DEPLOY.md PUSH_CHECKLIST.md models/
git add -u
git status
# If .env.dev or any .env* appears, run: git restore --staged .env.dev
```

## 4. After push

- Rotate **TMDB_API_KEY** if it was ever committed in the past.
- In GitHub: set **DOCKERHUB_USERNAME** and **DOCKERHUB_TOKEN** in repo Secrets (Settings → Secrets and variables → Actions).
