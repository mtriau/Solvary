# Citation renumbering

A generated answer cites sources as `[n]` where `n` indexes into a source
list. Renumber citations by **order of first appearance**, drop sources that
are never cited, and merge duplicate citations of the same source.

```python
text = "Cats purr [3]. Dogs bark [1]. Cats also meow [3][2]."
sources = ["dogs.com", "birds.com", "cats.com"]
renumber(text, sources)
# -> ("Cats purr [1]. Dogs bark [2]. Cats also meow [1][3].",
#     ["cats.com", "dogs.com", "birds.com"])
```

- `[n]` is 1-indexed into `sources`.
- An out-of-range citation (`[0]`, or `n` greater than `len(sources)`)
  raises ValueError.
- Text with no citations returns `(text, [])`. The same source cited many
  times gets one number. Renumbering is a single pass over the original
  text, so `[2] ... [1]` becomes `[1] ... [2]` without the new `[1]` being
  rewritten again.
- Follow-up: adjacent duplicates `[1][1]` collapse to `[1]`; ranges `[1-3]`.
