"""Weighted reciprocal rank fusion for hybrid retrieval."""

from __future__ import annotations

from collections.abc import Mapping, Sequence


def reciprocal_rank_score(rank: int, *, constant: float, weight: float = 1.0) -> float:
    """Contribution of one channel: ``weight / (constant + rank)``.

    ``rank`` is 1-based (first hit = 1).
    """
    if rank < 1:
        msg = f"rank must be >= 1, got {rank}"
        raise ValueError(msg)
    if constant <= 0:
        msg = f"constant must be > 0, got {constant}"
        raise ValueError(msg)
    return weight / (constant + rank)


def fuse_ranked_lists(
    channel_ranks: Mapping[str, Mapping[str, int]],
    *,
    channel_weights: Mapping[str, float],
    constant: float,
) -> list[tuple[str, float]]:
    """Fuse per-channel 1-based ranks keyed by candidate id.

    ``channel_ranks`` maps channel name → {candidate_id: rank}.
    Returns ``(candidate_id, fused_score)`` sorted by score desc, then id asc.
    """
    scores: dict[str, float] = {}
    for channel, ranks in channel_ranks.items():
        weight = float(channel_weights.get(channel, 0.0))
        if weight == 0.0:
            continue
        for candidate_id, rank in ranks.items():
            scores[candidate_id] = scores.get(candidate_id, 0.0) + reciprocal_rank_score(
                rank, constant=constant, weight=weight
            )
    return sorted(scores.items(), key=lambda item: (-item[1], item[0]))


def ranks_from_ordered_ids(ordered_ids: Sequence[str]) -> dict[str, int]:
    """Build 1-based ranks from an ordered list (first occurrence wins)."""
    ranks: dict[str, int] = {}
    for index, candidate_id in enumerate(ordered_ids, start=1):
        if candidate_id not in ranks:
            ranks[candidate_id] = index
    return ranks
