"""
Streamlit UI for the movie recommender.
Run from project root: streamlit run ui/app.py
"""
import html
import sys
from pathlib import Path

import streamlit as st

# Ensure project root is on path when run as streamlit run ui/app.py
_PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from ui import lib

VERSION = "1.0.0"

# Must be first Streamlit command
st.set_page_config(
    page_title="Sorted Cinema",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Cached data load — critical for perceived speed
@st.cache_resource
def _load_data():
    """Load movies and similarity once; reused across runs."""
    return lib.load_movies_and_similarity()


@st.cache_data(ttl=3600)
def _get_cached_recommendations(selected_title: str, top_n: int = 3, _cache_version: int = 2):
    """Cache recommendations by (title, top_n) to avoid rerun cost. _cache_version invalidates cache when logic changes."""
    movies_df, similarity = _load_data()
    return lib.get_recommendations(movies_df, similarity, selected_title, top_n=top_n)


# Netflix-style styling — single-page fit, search on top (mobile-friendly), footer below
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    html, body, [data-testid="stAppViewContainer"] {
        background: linear-gradient(180deg, #0F0F0F 0%, #1A1A1A 50%, #0F0F0F 100%) !important;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    }
    [data-testid="stHeader"] { background: rgba(15,15,15,0.85) !important; border-bottom: 1px solid rgba(255,255,255,0.06); }
    [data-testid="stBlockContainer"] { padding-top: 0.4rem !important; max-width: 100% !important; }
    [data-testid="stVerticalBlock"] > div { padding: 0.12rem 0 !important; }
    .hero-block {
        text-align: center;
        margin-bottom: 0.4rem !important;
        padding: 0.2rem 0 0.1rem !important;
        width: 100%;
    }
    .hero-block .hero-title {
        font-family: 'Inter', sans-serif !important;
        font-weight: 700 !important;
        font-size: 2.5rem !important;
        letter-spacing: 0.05em !important;
        color: #FFFFFF !important;
        margin: 0 0 0.1rem 0 !important;
        text-shadow: 0 0 40px rgba(255,255,255,0.08);
    }
    .hero-block .hero-subtitle {
        font-family: 'Inter', sans-serif !important;
        font-weight: 400 !important;
        font-size: 0.85rem !important;
        color: #8C8C8C !important;
        margin: 0 !important;
    }
    [data-testid="stVerticalBlock"] .stSelectbox > div { background: #1C1C1C !important; border-radius: 12px !important; border: 1px solid rgba(255,255,255,0.1) !important; color: #FFFFFF !important; min-height: 2.75rem !important; }
    [data-testid="stVerticalBlock"] .stButton > button {
        background: #FF2E63 !important;
        color: #FFFFFF !important;
        font-family: 'Inter', sans-serif !important;
        font-weight: 600 !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 0.6rem 1.2rem !important;
        min-height: 2.75rem !important;
        box-shadow: 0 4px 16px rgba(255,46,99,0.35) !important;
    }
    [data-testid="stVerticalBlock"] .stButton > button:hover { background: #FF4D7A !important; box-shadow: 0 6px 24px rgba(255,46,99,0.45) !important; }
    .section-label { font-family: 'Inter', sans-serif !important; font-size: 0.95rem !important; font-weight: 600 !important; color: #FFFFFF !important; margin: 0 0 0.25rem 0 !important; }
    div[data-testid="column"] > div {
        background: #1C1C1C !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 0.4rem !important;
        box-shadow: 0 8px 32px rgba(0,0,0,0.4) !important;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    div[data-testid="column"] > div:hover {
        transform: scale(1.02);
        box-shadow: 0 12px 40px rgba(0,0,0,0.5), 0 0 24px rgba(255,46,99,0.12);
    }
    div[data-testid="column"] img {
        border-radius: 10px !important;
        box-shadow: 0 4px 20px rgba(0,0,0,0.5) !important;
        width: 100% !important;
        height: 200px !important;
        object-fit: cover !important;
    }
    div[data-testid="column"] [data-testid="stMarkdown"] {
        color: #FFFFFF !important;
        font-family: 'Inter', sans-serif !important;
        font-weight: 500 !important;
        font-size: 0.85rem !important;
        margin-top: 0.2rem !important;
    }
    .stCaption { color: #8C8C8C !important; font-family: 'Inter', sans-serif !important; font-size: 0.8rem !important; }
    .stSpinner label { color: #8C8C8C !important; }
    .single-page-footer { margin-top: 0.5rem !important; padding: 8px 0 !important; font-size: 12px !important; }
    @media (max-width: 640px) {
        .hero-block .hero-title { font-size: 1.85rem !important; }
        .hero-block .hero-subtitle { font-size: 0.8rem !important; }
        div[data-testid="column"] img { height: 160px !important; }
        [data-testid="stVerticalBlock"] .stSelectbox > div, [data-testid="stVerticalBlock"] .stButton > button { min-height: 2.5rem !important; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Load data (cached) — spinner on first load for perceived speed
try:
    with st.spinner("Loading movie data…"):
        movies_df, similarity = _load_data()
except Exception as e:
    st.error(f"Could not load data: {e}")
    st.info(
        "Put movies_dic.pkl and tag_similarity.pkl in models/trained/. "
        "Set TMDB_API_KEY in .env.dev for posters."
    )
    st.stop()

# Hero — top of page
st.markdown(
    '<div class="hero-block">'
    '<h1 class="hero-title">Sorted Cinema</h1>'
    '<p class="hero-subtitle">Your Taste, Sorted.</p>'
    '</div>',
    unsafe_allow_html=True,
)

# Search on top in main area — always visible, easy on mobile (no sidebar to open)
sr1, sr2, _ = st.columns([2, 1, 1])
with sr1:
    selected = st.selectbox(
        "Choose a movie",
        options=movies_df["title"].values,
        label_visibility="collapsed",
        key="movie_select",
    )
with sr2:
    get_recs = st.button("Get recommendations", type="primary")

if get_recs and selected:
    with st.spinner("Finding perfect films for you…"):
        recs = _get_cached_recommendations(selected, top_n=3)
    st.session_state.recommendations = recs if recs else None
    st.session_state.selected_for_label = selected
    if not recs:
        st.warning("No recommendations found.")

recs = st.session_state.get("recommendations")
selected_label = st.session_state.get("selected_for_label")

if recs:
    safe_title = html.escape(str(selected_label))
    st.markdown(f'<p class="section-label">Because you liked <strong>{safe_title}</strong></p>', unsafe_allow_html=True)
    cols = st.columns(3)
    for col, movie in zip(cols, recs):
        with col:
            st.image(movie["poster"], width="stretch")
            st.markdown(f"**{movie['title']}**")
            score = movie.get("score_pct")
            st.caption(f"⭐ {score}% match" if score is not None else "⭐ High match")
else:
    # Default state: show TMDB trending posters so the page isn't empty
    get_featured = getattr(lib, "get_featured_posters", None)
    featured = list(get_featured(3)) if callable(get_featured) else []
    if featured:
        st.markdown('<p class="section-label">Popular this week</p>', unsafe_allow_html=True)
        cols = st.columns(3)
        for col, movie in zip(cols, featured):
            with col:
                st.image(movie["poster"], width="stretch")
                st.markdown(f"**{movie['title']}**")
        st.caption("Pick a movie above and tap **Get recommendations** for your picks.")
    else:
        st.caption("Pick a movie above and tap **Get recommendations**.")

# Footer — compact for single-page fit
st.markdown(
    f"""
    <div class="single-page-footer" style="text-align: center; color: #8C8C8C; font-family: 'Inter', sans-serif;">
        <p style="margin: 0;"><strong>HectorLabs</strong> · Built by <a href="https://www.amitchoubey.dev/" target="_blank" style="color: #8C8C8C; text-decoration: none;"><strong>Amit Choubey</strong></a> · <a href="https://www.hectorlabs.co.uk" target="_blank" style="color: #8C8C8C; text-decoration: none;">hectorlabs.co.uk</a> · v{VERSION}</p>
    </div>
    """,
    unsafe_allow_html=True,
)
