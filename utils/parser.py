"""
Utilidades de parsing y limpieza de texto para datos inmobiliarios.
"""

import re
from typing import Optional


def parse_price(raw: str) -> Optional[int]:
    """
    Extrae un precio entero de strings como '250.000 €', '1,200,000€', '834000'.
    Devuelve None si no se puede parsear.
    """
    if not raw:
        return None
    # Eliminar todo excepto dígitos
    cleaned = re.sub(r"[^\d]", "", raw)
    if not cleaned:
        return None
    price = int(cleaned)
    if price < 5000 or price > 50_000_000:
        return None
    return price


def clean_text(raw: str) -> str:
    """Elimina espacios extra, saltos de línea y caracteres invisibles."""
    if not raw:
        return ""
    text = re.sub(r"[\n\r\t]+", " ", raw)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def parse_rooms(raw: str) -> Optional[int]:
    """Extrae habitaciones de '3 habs.', '2 hab', '3 dormitorios'."""
    if not raw:
        return None
    match = re.search(r"(\d+)\s*(?:hab|dorm)", raw, re.IGNORECASE)
    return int(match.group(1)) if match else None


def parse_rooms_from_number(raw: str) -> Optional[int]:
    """Extrae habitaciones de un string que es solo un número."""
    if not raw:
        return None
    match = re.search(r"^(\d+)$", raw.strip())
    return int(match.group(1)) if match else None


def parse_size(raw: str) -> Optional[int]:
    """Extrae metros cuadrados de '85 m²', '120 m2', '68 m²'."""
    if not raw:
        return None
    match = re.search(r"(\d+)\s*m[²2\s]", raw, re.IGNORECASE)
    return int(match.group(1)) if match else None


def extract_title_from_url(url: str) -> str:
    """Extrae un título legible de la URL del inmueble como fallback."""
    if not url:
        return "Sin título"
    # /inmueble/piso-en-venta-en-calle-de-foo-RP472026151749 -> Piso en venta en calle de foo
    parts = url.rstrip("/").split("/")
    last = parts[-1] if parts else ""
    # Limpiar códigos Redpiso (RP + dígitos), IDs numéricos, y sufijos largos
    last = re.sub(r"-RP\d+$", "", last, flags=re.IGNORECASE)
    last = re.sub(r"-[A-Z0-9]{10,}$", "", last)
    last = re.sub(r"-\d+_\d+$", "", last)
    result = last.replace("-", " ").strip().capitalize()
    # Si queda algo muy corto o solo es un código, devolver genérico
    if not result or len(result) < 5 or result.replace(" ", "").isdigit():
        return "Sin título"
    return result
