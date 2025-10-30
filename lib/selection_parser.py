"""Selection parser utility for multi-select prompts"""


def parse_selection(input_str: str, max_count: int) -> list[int]:
    """Parse user selection string into list of indices

    Supports:
        - Single: "1" -> [0]
        - Multiple: "1,3,5" or "1 3 5" -> [0,2,4]
        - Range: "1-5" -> [0,1,2,3,4]
        - Mixed: "1,3-5,7" -> [0,2,3,4,6]

    Args:
        input_str: User input string
        max_count: Maximum valid number (total items)

    Returns:
        List of 0-based indices (sorted, deduplicated)

    Raises:
        ValueError: If input contains invalid numbers or ranges
    """
    indices = set()

    # Normalize separators: replace spaces around commas/hyphens, then spaces -> commas
    # But preserve hyphens for ranges
    input_str = input_str.replace(" - ", "-")  # "1 - 5" -> "1-5"
    input_str = input_str.replace(" ", ",")  # "1 3 5" -> "1,3,5"

    for part in input_str.split(","):
        part = part.strip()
        if not part:
            continue

        if "-" in part:
            # Range: "1-5"
            try:
                start, end = part.split("-", 1)
                start = start.strip()
                end = end.strip()

                # Skip if either side is empty
                if not start or not end:
                    continue

                start_idx = int(start) - 1  # Convert to 0-based
                end_idx = int(end) - 1
            except ValueError:
                raise ValueError(f"Invalid range format: {part}")

            if start_idx < 0 or end_idx >= max_count:
                raise ValueError(f"Range out of bounds (1-{max_count}): {part}")

            if start_idx > end_idx:
                raise ValueError(f"Invalid range (start > end): {part}")

            indices.update(range(start_idx, end_idx + 1))
        else:
            # Single number
            try:
                idx = int(part) - 1  # Convert to 0-based
            except ValueError:
                raise ValueError(f"Invalid number: {part}")

            if idx < 0 or idx >= max_count:
                raise ValueError(f"Number out of range (1-{max_count}): {int(part)}")

            indices.add(idx)

    return sorted(list(indices))


__all__ = ["parse_selection"]
