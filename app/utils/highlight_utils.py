import re


def highlight_text(text: str, query: str):
    if not query or not text:
        return [{"text": text, "highlight": False}]
    try:
        escaped = re.escape(query)
        pattern = re.compile(f"({escaped})", re.IGNORECASE)
        parts = pattern.split(text)
        result = []
        for part in parts:
            if pattern.match(part):
                result.append({"text": part, "highlight": True})
            elif part:
                result.append({"text": part, "highlight": False})
        return result if result else [{"text": text, "highlight": False}]
    except re.error:
        return [{"text": text, "highlight": False}]
