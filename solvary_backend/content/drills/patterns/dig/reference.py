def dig(data, *path, default=None):
    try:
        for step in path:
            data = data[step]
    except (KeyError, IndexError, TypeError):
        return default
    return data
