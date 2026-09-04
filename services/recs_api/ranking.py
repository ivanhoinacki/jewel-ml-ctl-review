def score_candidates(anchor: dict, candidates: list[dict], shopper_id: str | None = None) -> list[dict]:
    """Existing ranking entry point. Returns candidates ordered by relevance to the anchor."""
    return sorted(candidates, key=lambda c: c.get("popularity", 0), reverse=True)
