# UI

Streamlit app for the movie recommender.

## Run locally

From **project root**:

```bash
streamlit run ui/app.py
```

Optional: set port and bind address:

```bash
streamlit run ui/app.py --server.port=8501 --server.address=0.0.0.0
```

## Environment

- `.env.dev` (or `.env.test` / `.env.prod` via `APP_ENV`) in project root.
- Required: `TMDB_API_KEY` (for posters from TMDB).

## Data

- Place `movies_dic.pkl` and `tag_similarity.pkl` in the **project root** (or in `models/trained/`). The app looks in the root first, then in `models/trained/`, and skips Git LFS pointer files.
