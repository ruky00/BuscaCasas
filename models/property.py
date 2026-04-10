"""
Modelo de datos para representar un inmueble extraido de cualquier portal.
"""

import hashlib
from dataclasses import dataclass, field, asdict
from datetime import date
from typing import Optional


@dataclass
class Property:
    source: str
    title: str
    price: Optional[int]
    location: str
    url: str
    description: Optional[str] = None
    rooms: Optional[int] = None
    size_m2: Optional[int] = None
    hash: str = field(default="", init=False)
    extracted_date: str = field(default="", init=False)

    # Scoring — asignados por ScoringService despues del scraping
    score: float = field(default=0.0, init=False)
    score_stars: int = field(default=0, init=False)
    score_label: str = field(default="", init=False)
    price_per_m2: Optional[int] = field(default=None, init=False)

    def __post_init__(self):
        self.extracted_date = date.today().isoformat()
        self.hash = self._generate_hash()
        if self.price and self.size_m2 and self.size_m2 > 0:
            self.price_per_m2 = int(self.price / self.size_m2)

    def _generate_hash(self) -> str:
        raw = f"{self.source}|{self.url}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]

    def to_dict(self) -> dict:
        return asdict(self)
