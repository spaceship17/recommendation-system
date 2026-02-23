"""Pydantic schemas for the recommendation API."""
from pydantic import BaseModel, Field


class RecommendationRequest(BaseModel):
    """Request body for /recommend."""

    movie_title: str = Field(..., description="Title of the movie to get recommendations for")
    top_n: int = Field(default=5, ge=1, le=20, description="Number of recommendations to return")


class MovieRecommendation(BaseModel):
    """A single recommended movie with optional score."""

    title: str
    poster_url: str = ""
    score_pct: int | None = None


class RecommendationResponse(BaseModel):
    """Response for /recommend."""

    recommendations: list[MovieRecommendation]
    source_movie: str
