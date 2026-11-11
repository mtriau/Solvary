def topo_order(deps: dict[str, set[str]]) -> list[str]:
    """Tasks ordered after their dependencies; ValueError on a cycle."""
    raise NotImplementedError
