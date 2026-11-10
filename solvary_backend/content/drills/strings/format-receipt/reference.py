def format_receipt(items: list[tuple[str, float]]) -> list[str]:
    lines = [f"{name:<12}{price:>8.2f}" for name, price in items]
    total = sum(price for _, price in items)
    lines.append(f"{'TOTAL':<12}{total:>8.2f}")
    return lines
