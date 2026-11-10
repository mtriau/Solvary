# Topic sort

Sort names of the form `<prefix><number>` by prefix (alphabetical), then by
the numeric suffix (numerically, so `topic2` before `topic10`). Names with
no numeric suffix sort before numbered names with the same prefix.

```python
sort_topics(["topic10", "topic2", "alpha", "alpha7", "beta1", "topic1"])
# -> ["alpha", "alpha7", "beta1", "topic1", "topic2", "topic10"]
```

Prefix is everything up to the trailing digit run: `a1b2` has prefix `a1b`
and number 2; an all-digit name such as `42` has prefix `""`. Leading zeros:
`topic02` and `topic2` compare equal numerically; keep input order for ties
(stable).
