"""Adapters that connect external events with control evaluation requests."""

from .event_adapter import EventDrivenRecommendationAdapter
from .recommendation_sink_adapter import RecommendationSinkAdapter

__all__ = ["EventDrivenRecommendationAdapter", "RecommendationSinkAdapter"]
