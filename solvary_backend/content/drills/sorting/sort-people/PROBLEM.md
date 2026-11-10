# Sort by age, then name

Sort people by age ascending; people of the same age by name ascending. Return a new list and leave the input unchanged.

### Signature

`def sort_people(people: list[dict]) -> list[dict]`

Each person is a dict with `"name"` and `"age"`.

### Examples

```python
sort_people([{"name": "Bo", "age": 30}, {"name": "Al", "age": 25}, {"name": "Ab", "age": 30}])
# -> [{"name": "Al", "age": 25}, {"name": "Ab", "age": 30}, {"name": "Bo", "age": 30}]
```

### Idiom

`sorted` with a `key` that returns a tuple.
