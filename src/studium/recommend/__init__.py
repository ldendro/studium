"""Recommendation models and deterministic assembly."""

from studium.recommend.models import (
    AddLearningEncounterRecommendation,
    AddScaffoldModuleRecommendation,
    AliasSuggestion,
    ConceptRecommendation,
    CreateNewConceptRecommendation,
    MarkRedundantRecommendation,
    RecommendationFailure,
    RequestClarificationRecommendation,
    UpdateLearningEncounterRecommendation,
    UseExistingConceptRecommendation,
)
from studium.recommend.service import (
    assemble_alias_suggestion,
    assemble_recommendation_failure,
    calculate_recommendation_confidence,
    recommend,
)

__all__ = [
    "AddLearningEncounterRecommendation",
    "AddScaffoldModuleRecommendation",
    "AliasSuggestion",
    "ConceptRecommendation",
    "CreateNewConceptRecommendation",
    "MarkRedundantRecommendation",
    "RecommendationFailure",
    "RequestClarificationRecommendation",
    "UpdateLearningEncounterRecommendation",
    "UseExistingConceptRecommendation",
    "assemble_alias_suggestion",
    "assemble_recommendation_failure",
    "calculate_recommendation_confidence",
    "recommend",
]
