import re
import unicodedata


def normalize_whitespace(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def clean_resource_text(value: str) -> str:
    lines = [normalize_whitespace(line) for line in value.splitlines()]
    return "\n".join(line for line in lines if line)


def slugify(value: str, max_length: int = 90) -> str:
    normalized = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    lowered = normalized.lower()
    slug = re.sub(r"[^a-z0-9]+", "-", lowered).strip("-")
    return (slug[:max_length].strip("-") or "untitled")

