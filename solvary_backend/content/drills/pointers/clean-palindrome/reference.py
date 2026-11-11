def is_palindrome(s: str) -> bool:
    cleaned = [c.casefold() for c in s if c.isalnum()]
    return cleaned == cleaned[::-1]


def is_palindrome_two_pointers(s: str) -> bool:
    left, right = 0, len(s) - 1
    while left < right:
        if not s[left].isalnum():
            left += 1
        elif not s[right].isalnum():
            right -= 1
        elif s[left].casefold() != s[right].casefold():
            return False
        else:
            left, right = left + 1, right - 1
    return True
