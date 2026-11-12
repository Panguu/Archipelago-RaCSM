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
    """Keep large contiguous blocks available for wrappers and flag tables."""
    if size <= 0:
        raise ValueError("Hook allocation must have a positive size")
    candidates = [(end - start, start) for start, end in free_blocks(ranges, patches)
                  if end - start >= size]
    return min(candidates)[1] if candidates else None


def plan_storage(ranges, patches, sizes):
    """Place the whole request set before emitting address-dependent code.

    Largest-first search backtracks when a locally good placement strands a
    later request. Equal-capacity gaps are interchangeable for packing.
    """
    if any(size <= 0 for size in sizes):
        raise ValueError("Hook allocation must have a positive size")
    blocks = free_blocks(ranges, patches)
    capacities = [(end - start) // 4 * 4 for start, end in blocks]
    requests = sorted(enumerate((size + 3) // 4 * 4 for size in sizes),
                      key=lambda entry: -entry[1])
    placement = [None] * len(sizes)
    failed = set()

    def place(index):
        if index == len(requests):
            return True
        key = (index, tuple(sorted(capacities)))
        if key in failed:
            return False
        if sum(size for _, size in requests[index:]) > sum(capacities):
            return False
        request, size = requests[index]
        seen = set()
        for block in sorted(range(len(blocks)), key=capacities.__getitem__):
            capacity = capacities[block]
            if capacity < size or capacity in seen:
                continue
            seen.add(capacity)
            start, end = blocks[block]
            placement[request] = start + (end - start) // 4 * 4 - capacity
            capacities[block] -= size
            if place(index + 1):
                return True
            capacities[block] += size
        failed.add(key)
        return False

    return placement if place(0) else None
