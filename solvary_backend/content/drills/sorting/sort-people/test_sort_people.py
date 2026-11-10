from sort_people import sort_people


def test_example():
    people = [{"name": "Bo", "age": 30}, {"name": "Al", "age": 25}, {"name": "Ab", "age": 30}]
    assert sort_people(people) == [
        {"name": "Al", "age": 25},
        {"name": "Ab", "age": 30},
        {"name": "Bo", "age": 30},
    ]


def test_input_is_not_mutated():
    people = [{"name": "B", "age": 2}, {"name": "A", "age": 1}]
    sort_people(people)
    assert [p["name"] for p in people] == ["B", "A"]


def test_empty():
    assert sort_people([]) == []


def test_same_age_sorted_by_name():
    people = [{"name": "Zed", "age": 40}, {"name": "Amy", "age": 40}]
    assert [p["name"] for p in sort_people(people)] == ["Amy", "Zed"]
