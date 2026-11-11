# Simplify a Unix path

Collapse an absolute Unix path: resolve `.` and `..`, squash repeated slashes, drop a trailing slash. The result starts with `/` and `..` at the root stays at the root.

### Signature

`def simplify_path(path: str) -> str`

### Examples

```python
simplify_path("/a/./b/../../c/") == "/c"
simplify_path("/../") == "/"
simplify_path("/home//foo/") == "/home/foo"
```

### Idiom

`path.split("/")` yields the parts (empty strings for repeated slashes), a stack of real names, `continue` for `""` and `"."`, pop for `".."` guarded by `if stack`, and `"/" + "/".join(stack)` to rebuild.
