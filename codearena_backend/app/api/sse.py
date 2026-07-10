import json


def format_sse(data: dict) -> str:
    """Serialize one event as an SSE frame."""
    return f"data: {json.dumps(data)}\n\n"
