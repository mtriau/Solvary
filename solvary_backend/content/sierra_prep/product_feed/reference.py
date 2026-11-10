class TransientError(Exception):
    """The product API may raise this; the same request can be retried."""


# ── Part 1 ─────────────────────────────────────────────────────────────


def _call_with_retry(api, cursor, max_attempts: int) -> dict:
    for attempt in range(1, max_attempts + 1):
        try:
            return api.list_products(cursor=cursor)
        except TransientError:
            if attempt == max_attempts:
                raise
    raise AssertionError("unreachable")


def fetch_products(api, *, max_attempts: int = 5) -> list[dict]:
    out: list[dict] = []
    cursor = None
    while True:
        page = _call_with_retry(api, cursor, max_attempts)
        out.extend(page["items"])
        cursor = page.get("next_cursor")
        if cursor is None:
            return out


# ── Part 2 ─────────────────────────────────────────────────────────────


def _resolve_one(product_id: str, catalog: dict[str, dict]) -> dict | None:
    seen: set[str] = set()
    stack = [product_id]
    while stack:
        pid = stack.pop()
        if pid in seen:
            continue
        seen.add(pid)
        product = catalog.get(pid)
        if product is None:
            continue
        if product["available"]:
            return product
        # depth first, siblings in order: push in reverse so the first pops first
        for fb in reversed(product["fallback_ids"]):
            if fb not in seen:
                stack.append(fb)
    return None


def resolve(listings: list[dict], catalog: dict[str, dict]) -> list[dict | None]:
    return [_resolve_one(listing["product_id"], catalog) for listing in listings]


# ── Part 3 ─────────────────────────────────────────────────────────────


def merge_listings(products: list[dict | None]) -> list[dict]:
    merged: dict[str, dict] = {}
    for p in products:
        if p is None:
            continue
        sku = p["sku"]
        entry = merged.get(sku)
        if entry is None:
            merged[sku] = {
                "sku": sku,
                "name": p["name"],
                "price": p["price"],
                "stock": p["stock"],
                "tags": set(p["tags"]),
            }
        else:
            entry["price"] = min(entry["price"], p["price"])
            entry["stock"] += p["stock"]
            entry["tags"].update(p["tags"])
    out = []
    for entry in merged.values():
        entry["tags"] = sorted(entry["tags"])
        out.append(entry)
    return out
