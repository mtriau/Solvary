def sort_people(people: list[dict]) -> list[dict]:
    return sorted(people, key=lambda person: (person["age"], person["name"]))
