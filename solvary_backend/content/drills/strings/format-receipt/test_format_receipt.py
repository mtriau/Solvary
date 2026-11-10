from format_receipt import format_receipt


def test_example():
    assert format_receipt([("Coffee", 3.5), ("Bagel", 2.25)]) == [
        "Coffee          3.50",
        "Bagel           2.25",
        "TOTAL           5.75",
    ]


def test_empty_has_only_total():
    assert format_receipt([]) == ["TOTAL           0.00"]


def test_every_line_is_20_wide():
    lines = format_receipt([("Tea", 1), ("Sandwich", 10.5)])
    assert all(len(line) == 20 for line in lines)


def test_two_decimals():
    assert format_receipt([("X", 2.5)])[0] == "X" + " " * 15 + "2.50"
    assert format_receipt([("Y", 1.999)])[0] == "Y" + " " * 15 + "2.00"


def test_total_sums_prices():
    assert format_receipt([("A", 1.1), ("B", 2.2), ("C", 3.3)])[-1] == "TOTAL           6.60"
