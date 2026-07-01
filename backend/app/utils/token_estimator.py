def estimate_tokens(text: str) -> int:
    """Estimate token count for a text string (approx 4 characters per token)."""
    if not text:
        return 0
    return max(1, len(text) // 4)
