"""
Sistema de scoring inteligente para propiedades inmobiliarias.

Puntua cada inmueble de 0 a 5 estrellas en base a:
  1. Precio relativo    (40%) — mas barato vs la media del dataset = mejor
  2. Precio por m2      (25%) — eficiencia del precio por superficie
  3. Completitud        (15%) — datos completos = anuncio mas fiable
  4. Superficie         (10%) — mas m2 por el precio = mejor
  5. Ubicacion centrica (10%) — bonus por zonas premium de Madrid

La logica es relativa al dataset actual: compara cada propiedad contra
el resto del batch, no contra valores absolutos. Asi funciona con
cualquier ciudad y rango de precios.
"""

import logging
import math
from models.property import Property

logger = logging.getLogger(__name__)

# Zonas premium de Madrid (barrios centricos / alta demanda)
# Bonus de ubicacion para propiedades en estas zonas
PREMIUM_ZONES = [
    "chamberi", "salamanca", "retiro", "centro", "malasana",
    "chueca", "lavapies", "arguelles", "moncloa", "chamartin",
    "castellana", "arapiles", "trafalgar", "justicia", "cortes",
    "sol", "opera", "latina", "embajadores", "universidad",
    "alonso martinez", "olavide", "rios rosas", "nuevos ministerios",
    "barrio de salamanca", "guindalera", "goya", "principe de vergara",
    "lista", "velazquez", "recoletos",
]


class ScoringService:
    """
    Puntua y filtra propiedades segun su valor relativo.

    Flujo:
        properties = scoring.score_all(properties)
        top = scoring.filter_top(properties, min_score=3.5, max_results=10)
    """

    def __init__(self, min_score: float = 3.5, max_results: int = 10):
        self.min_score = min_score
        self.max_results = max_results

    def score_all(self, properties: list[Property]) -> list[Property]:
        """Asigna score a todas las propiedades del batch."""
        if not properties:
            return properties

        # Calcular estadisticas del dataset para scoring relativo
        stats = self._compute_stats(properties)
        logger.info(
            f"Stats del batch: {stats['count']} props, "
            f"precio medio {stats['avg_price']:,.0f}, "
            f"EUR/m2 medio {stats['avg_ppm2']:,.0f}"
        )

        for prop in properties:
            prop.score = self._calculate_score(prop, stats)
            prop.score_stars = self._to_stars(prop.score)
            prop.score_label = self._to_label(prop.score)

        scored_count = len([p for p in properties if p.score >= self.min_score])
        logger.info(
            f"Scoring completado: {scored_count}/{len(properties)} "
            f"superan umbral {self.min_score}"
        )
        return properties

    def filter_top(
        self,
        properties: list[Property],
        min_score: float = None,
        max_results: int = None,
    ) -> list[Property]:
        """Filtra y ordena: solo las mejores oportunidades."""
        threshold = min_score if min_score is not None else self.min_score
        limit = max_results if max_results is not None else self.max_results

        filtered = [p for p in properties if p.score >= threshold]
        filtered.sort(key=lambda p: p.score, reverse=True)
        top = filtered[:limit]

        logger.info(
            f"Filtrado: {len(top)} oportunidades "
            f"(de {len(properties)} totales, umbral >= {threshold})"
        )
        return top

    # ─── Scoring interno ────────────────────────────────────────────────

    def _calculate_score(self, prop: Property, stats: dict) -> float:
        """
        Score compuesto de 0.0 a 5.0.

        Pesos:
          - Precio relativo:    40%
          - Precio por m2:      25%
          - Completitud:        15%
          - Superficie:         10%
          - Ubicacion premium:  10%
        """
        s_price = self._score_price(prop, stats)
        s_ppm2 = self._score_price_per_m2(prop, stats)
        s_complete = self._score_completeness(prop)
        s_size = self._score_size(prop, stats)
        s_location = self._score_location(prop)

        raw = (
            s_price * 0.40
            + s_ppm2 * 0.25
            + s_complete * 0.15
            + s_size * 0.10
            + s_location * 0.10
        )

        # Clamp a [0, 5]
        return max(0.0, min(5.0, round(raw, 2)))

    def _score_price(self, prop: Property, stats: dict) -> float:
        """Cuanto mas barato vs la media, mejor score (0-5)."""
        if not prop.price or not stats["avg_price"]:
            return 2.5
        ratio = prop.price / stats["avg_price"]
        # ratio < 0.5 -> 5.0, ratio = 1.0 -> 2.5, ratio > 1.5 -> 0.0
        return max(0.0, min(5.0, 5.0 - (ratio * 2.5)))

    def _score_price_per_m2(self, prop: Property, stats: dict) -> float:
        """Cuanto menor precio/m2 vs la media, mejor (0-5)."""
        if not prop.price_per_m2 or not stats["avg_ppm2"]:
            return 2.0
        ratio = prop.price_per_m2 / stats["avg_ppm2"]
        return max(0.0, min(5.0, 5.0 - (ratio * 2.5)))

    def _score_completeness(self, prop: Property) -> float:
        """Mas datos = anuncio mas fiable = mejor score (0-5)."""
        points = 0.0
        if prop.price:
            points += 1.5
        if prop.rooms:
            points += 1.0
        if prop.size_m2:
            points += 1.0
        if prop.description:
            points += 0.75
        if prop.title and len(prop.title) > 15:
            points += 0.75
        return min(5.0, points)

    def _score_size(self, prop: Property, stats: dict) -> float:
        """Mas m2 = mejor (0-5), relativo al dataset."""
        if not prop.size_m2 or not stats["avg_size"]:
            return 2.0
        ratio = prop.size_m2 / stats["avg_size"]
        # ratio 0.5 -> 1.5, ratio 1.0 -> 3.0, ratio 2.0 -> 5.0
        return max(0.0, min(5.0, ratio * 3.0))

    def _score_location(self, prop: Property) -> float:
        """Bonus si la propiedad esta en zona premium (0 o 5)."""
        loc_lower = prop.location.lower()
        for zone in PREMIUM_ZONES:
            if zone in loc_lower:
                return 5.0
        return 2.0

    # ─── Stats del dataset ──────────────────────────────────────────────

    def _compute_stats(self, properties: list[Property]) -> dict:
        prices = [p.price for p in properties if p.price]
        ppm2s = [p.price_per_m2 for p in properties if p.price_per_m2]
        sizes = [p.size_m2 for p in properties if p.size_m2]

        return {
            "count": len(properties),
            "avg_price": (sum(prices) / len(prices)) if prices else 0,
            "median_price": sorted(prices)[len(prices) // 2] if prices else 0,
            "avg_ppm2": (sum(ppm2s) / len(ppm2s)) if ppm2s else 0,
            "avg_size": (sum(sizes) / len(sizes)) if sizes else 0,
        }

    # ─── Conversion visual ──────────────────────────────────────────────

    @staticmethod
    def _to_stars(score: float) -> int:
        """Convierte score 0-5 a entero 0-5 estrellas."""
        return max(0, min(5, round(score)))

    @staticmethod
    def _to_label(score: float) -> str:
        """Etiqueta descriptiva segun el score."""
        if score >= 4.5:
            return "Oportunidad excepcional"
        if score >= 4.0:
            return "Gran oportunidad"
        if score >= 3.5:
            return "Buena oportunidad"
        if score >= 3.0:
            return "Interesante"
        if score >= 2.0:
            return "Normal"
        return "Por debajo de la media"
