"""Ideal solution: Byte Tokenizer, all three parts.

Part 1: tokenize(text, alphabet): ordered single-pass merges.
Part 2: Tokenizer class: alphabet-sized work moves to construction,
        per-string cost independent of vocabulary size; detokenize.
Part 3: count_tokens with a cache; chunked tokenization when safe.

The spec is NOT standard BPE "merge the lowest-rank pair repeatedly". It is:
for each multi-char token in alphabet order, ONE left-to-right pass that
merges adjacent pairs whose strings concatenate to that token, never
re-examining a token formed in the same pass. The Part 1 function is that
sentence transcribed. Part 2 keeps it as the only merge primitive and just
skips passes that cannot do anything.
"""

from functools import lru_cache


# ---------------------------------------------------------------- Part 1

def tokenize(text: str, alphabet: list[str]) -> list[int]:
    char_id = {s: i for i, s in enumerate(alphabet) if len(s) == 1}
    try:
        ids = [char_id[c] for c in text]
    except KeyError as e:
        raise ValueError(f"character {e.args[0]!r} not in alphabet") from None

    for tid, tok in enumerate(alphabet):
        if len(tok) > 1:
            ids = _merge_pass(ids, alphabet, tid)
    return ids


def _merge_pass(ids: list[int], alphabet: list[str], tid: int) -> list[int]:
    """One left-to-right pass merging adjacent pairs that spell alphabet[tid].
    `i += 2` after a merge is the no-rescan rule: the new token is not
    looked at again in this pass."""
    tok = alphabet[tid]
    out, i = [], 0
    while i < len(ids):
        if i + 1 < len(ids) and alphabet[ids[i]] + alphabet[ids[i + 1]] == tok:
            out.append(tid)
            i += 2
        else:
            out.append(ids[i])
            i += 1
    return out


# ---------------------------------------------------------------- Part 2

class Tokenizer:
    """Built once per alphabet. Per-string cost is O(n * L + k * n) where
    L is the longest token and k is the number of multi-char tokens that
    actually occur in the text, independent of vocabulary size."""

    def __init__(self, alphabet: list[str]) -> None:
        self.alphabet = list(alphabet)
        self.str_to_id = {s: i for i, s in enumerate(alphabet)}
        self.char_id = {s: i for s, i in self.str_to_id.items() if len(s) == 1}
        self.max_len = max((len(s) for s in alphabet), default=0)
        self._tokenize = lru_cache(maxsize=100_000)(self._tokenize_uncached)

    def tokenize(self, text: str) -> list[int]:
        return list(self._tokenize(text))          # cache holds tuples; hand out a fresh list

    def _tokenize_uncached(self, text: str) -> tuple[int, ...]:
        try:
            ids = [self.char_id[c] for c in text]
        except KeyError as e:
            raise ValueError(f"character {e.args[0]!r} not in alphabet") from None

        # A merged token's string is always a substring of the text, so only
        # multi-char tokens that occur as substrings can ever merge. Enumerate
        # substrings up to max_len instead of scanning the whole vocabulary.
        candidates = set()
        n = len(text)
        for i in range(n):
            for j in range(i + 2, min(n, i + self.max_len) + 1):
                tid = self.str_to_id.get(text[i:j])
                if tid is not None:
                    candidates.add(tid)

        # Same primitive as Part 1, same order; passes that would be no-ops
        # are skipped, so the output is identical to Part 1 by construction.
        for tid in sorted(candidates):
            ids = _merge_pass(ids, self.alphabet, tid)
        return tuple(ids)

    def detokenize(self, ids: list[int]) -> str:
        n = len(self.alphabet)
        out = []
        for i in ids:
            if not 0 <= i < n:                     # explicit range check: -1 would silently index from the end
                raise ValueError(f"token id {i!r} out of range")
            out.append(self.alphabet[i])
        return "".join(out)

    # ------------------------------------------------------------ Part 3

    def count_tokens(self, text: str) -> int:
        """Exact count. There is no shortcut that is exact; tokenizing is
        now cheap and cached, so just do it."""
        return len(self._tokenize(text))

    def tokenize_long(self, text: str) -> list[int]:
        """Tokenize a long text in whitespace-delimited chunks. Safe only if
        no multi-char token contains whitespace: then no merge can cross a
        space, so chunk boundaries at spaces cannot change the result."""
        if any(len(s) > 1 and any(c.isspace() for c in s) for s in self.alphabet):
            return self.tokenize(text)             # not chunkable; fall back
        out: list[int] = []
        start = 0
        for i, c in enumerate(text):
            if c.isspace():
                if start < i:
                    out.extend(self._tokenize(text[start:i]))
                out.append(self.char_id[c])
                start = i + 1
        if start < len(text):
            out.extend(self._tokenize(text[start:]))
        return out


if __name__ == "__main__":
    def raises(fn):
        try:
            fn()
        except ValueError:
            return True
        return False

    A = ["a", "b", "c", "ab", "abc"]

    # part 1: spec examples
    assert tokenize("abcab", A) == [4, 3]
    assert tokenize("aab", A) == [0, 3]
    assert tokenize("cba", A) == [2, 1, 0]
    assert tokenize("", A) == []
    # no rescan inside a pass
    assert tokenize("aaa", ["a", "aa"]) == [1, 0]
    assert tokenize("aaaa", ["a", "aa"]) == [1, 1]
    assert tokenize("aaaaa", ["a", "aa"]) == [1, 1, 0]
    # alphabet order decides which merge wins
    assert tokenize("abc", ["a", "b", "c", "bc", "ab"]) == [0, 3]
    assert tokenize("abc", ["a", "b", "c", "ab", "bc"]) == [3, 2]
    # tokens formed in an EARLIER pass do participate in later passes
    assert tokenize("abab", ["a", "b", "ab", "abab"]) == [3]
    assert tokenize("aab", ["a", "b", "ab", "aab"]) == [3]
    assert raises(lambda: tokenize("abz", A))

    # part 2: identical output through the class, plus detokenize
    T = Tokenizer(A)
    for s in ["abcab", "aab", "cba", "", "abcabcabc", "bbbb"]:
        assert T.tokenize(s) == tokenize(s, A), s
        assert T.detokenize(T.tokenize(s)) == s
    T2 = Tokenizer(["a", "aa"])
    assert T2.tokenize("aaaaa") == [1, 1, 0]
    assert raises(lambda: T.detokenize([99]))
    assert raises(lambda: T.detokenize([-1]))
    assert raises(lambda: T.tokenize("abz"))
    # cache must not leak a shared list
    first = T.tokenize("abcab"); first.append(-1)
    assert T.tokenize("abcab") == [4, 3]

    # part 3
    assert T.count_tokens("abcab") == 2
    S = Tokenizer(["a", "b", " ", "ab"])
    assert S.tokenize_long("ab a ab") == S.tokenize("ab a ab") == [3, 2, 0, 2, 3]
    S2 = Tokenizer(["a", " ", "a ", "a a"])    # tokens contain a space: not chunkable
    assert S2.tokenize_long("a a") == S2.tokenize("a a") == [3]

    print("byte_tokenizer reference OK")
