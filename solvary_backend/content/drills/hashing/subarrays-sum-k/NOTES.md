### Why this is idiomatic

- `sum(nums[i:j])` for every pair is cubic; a running sum per start is quadratic; prefix sums plus a hash map is linear. The last test only passes the linear one.
- Seeding with `{0: 1}` means "the empty prefix has sum 0", which lets a subarray that starts at index 0 be counted without a special case.
- Order inside the loop matters: look up `prefix - k` **before** recording `prefix`, or a subarray of length zero gets counted when `k == 0`.
- `Counter` returns 0 for missing keys, so `seen[prefix - k]` needs no `.get`.

### The habit

"Count or find a contiguous range with property P" where P is about a sum: prefix sums and a dict of what you have seen. Say the invariant: "`seen` holds every prefix sum strictly before this index."
