from flask import jsonify, request


def error(message: str, status: int = 400, code: str = "bad_request", **extra):
    return jsonify(error=message, code=code, **extra), status


def body() -> dict:
    data = request.get_json(silent=True)
    return data if isinstance(data, dict) else {}


def text_field(data: dict, name: str, max_len: int, required: bool = True) -> tuple[str, str | None]:
    """Return (value, error message or None)."""
    value = data.get(name)
    value = value.strip() if isinstance(value, str) else ""
    if required and not value:
        return value, f"{name.replace('_', ' ').capitalize()} is required."
    if len(value) > max_len:
        return value, f"{name.replace('_', ' ').capitalize()} must be at most {max_len} characters."
    return value, None
