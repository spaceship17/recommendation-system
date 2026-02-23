"""
FastAPI app for movie recommendations.
Serves /health and /recommend; loads models from models/trained/.
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .inference import get_recommendations, is_model_loaded
from .schemas import RecommendationRequest, RecommendationResponse

app = FastAPI(
    title="Sorted Cinema Recommendation API",
    description="Get movie recommendations by title. Maintained by Hector Labs.",
    version="1.0.0",
    contact={"name": "Amit Choubey", "url": "https://hectorlabs.co.uk"},
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "healthy", "model_loaded": is_model_loaded()}


@app.post("/recommend", response_model=RecommendationResponse)
def recommend(req: RecommendationRequest):
    try:
        recs = get_recommendations(req.movie_title, top_n=req.top_n)
        return RecommendationResponse(
            recommendations=recs,
            source_movie=req.movie_title,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
