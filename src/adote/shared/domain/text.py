def only_digits(raw: str) -> str:
    """The ASCII digits of `raw`, in order. Masks, spaces and punctuation are typing, not data."""
    return "".join(char for char in raw if "0" <= char <= "9")
