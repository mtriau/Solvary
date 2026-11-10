# Byte Tokenizer: Part 1

Implement `tokenize(text: str, alphabet: list[str]) -> list[int]`.

`alphabet` is an ordered vocabulary. A token's id is its index in the list.
The first entries are single characters (every character that can appear in
`text` is present). Each later entry is a multi-character string formed by
concatenating **two earlier entries** that appear adjacently.

Tokenization:

1. Map each character of `text` to its id.
2. For each multi-character token, **in alphabet order**, make **one
   left-to-right pass** over the current id list. Whenever two adjacent
   tokens' strings concatenate to exactly this token's string, replace the
   pair with this token's id and continue scanning **after** the new token
   (a token formed during a pass is not re-examined in that same pass).
3. Return the final id list.

```python
alphabet = ["a", "b", "c", "ab", "abc"]
tokenize("abcab", alphabet)   # -> [4, 3]
#   chars    -> [0, 1, 2, 0, 1]
#   "ab"     -> [3, 2, 3]
#   "abc"    -> [4, 3]        ("ab" + "c")
tokenize("aab", alphabet)     # -> [0, 3]
tokenize("cba", alphabet)     # -> [2, 1, 0]
tokenize("", alphabet)        # -> []

tokenize("aaa", ["a", "aa"])  # -> [1, 0]   one pass, no rescan
```

A character not in the alphabet raises ValueError. Run the provided tests:
`pytest byte_tokenizer -q`. Later parts come with their own test files.

*(Further parts will be revealed by the interviewer as you complete each stage.)*
