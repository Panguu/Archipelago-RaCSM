def free_blocks(ranges, patches):
    occupied = sorted((p.address, p.address + len(p.replacement)) for p in patches)
    blocks = []
    for start, end in ranges:
        cursor = (start + 3) & ~3
        for low, high in occupied:
            if high <= cursor or low >= end:
                continue
            if low > cursor:
                blocks.append((cursor, min(low, end)))
            cursor = max(cursor, (high + 3) & ~3)
            if cursor >= end:
                break
        if cursor < end:
            blocks.append((cursor, end))
    return blocks


def storage_address(ranges, patches, size):
    """The smallest free block that fits, keeping the big blocks free."""
    if size <= 0:
        raise ValueError("Hook allocation must have a positive size")
    candidates = [(end - start, start) for start, end in free_blocks(ranges, patches)
                  if end - start >= size]
    return min(candidates)[1] if candidates else None
