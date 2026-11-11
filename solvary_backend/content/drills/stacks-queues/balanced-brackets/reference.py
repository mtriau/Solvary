PAIRS = {")": "(", "]": "[", "}": "{"}


def balanced(s: str) -> bool:
    stack: list[str] = []
    for ch in s:
        if ch in PAIRS.values():
            stack.append(ch)
        elif ch in PAIRS:
            if not stack or stack.pop() != PAIRS[ch]:
                return False
    return not stack
