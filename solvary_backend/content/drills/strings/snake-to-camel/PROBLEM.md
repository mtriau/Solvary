# snake_case to camelCase

Convert a lower-case `snake_case` identifier to `camelCase`: the first word stays as it is, every following word gets its first letter upper-cased.

### Signature

`def snake_to_camel(name: str) -> str`

### Examples

```python
snake_to_camel("hello_world") == "helloWorld"
snake_to_camel("http_response_code") == "httpResponseCode"
snake_to_camel("single") == "single"
snake_to_camel("") == ""
```

### Idiom

Star-unpacking `first, *rest = name.split("_")`, then `str.join` over a generator of `capitalize()`.
