# ── Part 1 ─────────────────────────────────────────────────────────────


def merge_segments(segments: list[tuple[int, int, str]]) -> list[tuple[int, int, str]]:
    order = sorted(range(len(segments)), key=lambda i: (segments[i][0], segments[i][1], i))
    out: list[tuple[int, int, str]] = []
    for i in order:
        s, e, t = segments[i]
        if out and s < out[-1][1]:
            ps, pe, pt = out[-1]
            out[-1] = (ps, max(pe, e), pt + " " + t)
        else:
            out.append((s, e, t))
    return out


# ── Part 2 ─────────────────────────────────────────────────────────────


def coverage_flags(segments) -> tuple[bool, bool]:
    if len(segments) < 2:
        return (False, False)
    srt = sorted((s, e) for s, e, _ in segments)
    overlap = gap = False
    reach = srt[0][1]
    for s, e in srt[1:]:
        if s < reach:
            overlap = True
        elif s > reach:
            gap = True
        reach = max(reach, e)
    return (overlap, gap)


# ── Part 3 ─────────────────────────────────────────────────────────────


def gaps(segments) -> list[tuple[int, int]]:
    if len(segments) < 2:
        return []
    srt = sorted((s, e) for s, e, _ in segments)
    out: list[tuple[int, int]] = []
    reach = srt[0][1]
    for s, e in srt[1:]:
        if s > reach:
            out.append((reach, s))
        reach = max(reach, e)
    return out


def max_concurrent(segments) -> int:
    events: list[tuple[int, int]] = []
    for s, e, _ in segments:
        events.append((s, 1))
        events.append((e, -1))
    events.sort()  # at equal time, -1 sorts before +1: ends first (half-open)
    best = cur = 0
    for _, delta in events:
        cur += delta
        best = max(best, cur)
    return best
