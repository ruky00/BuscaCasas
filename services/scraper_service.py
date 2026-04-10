"""
Orquestador principal de scrapers.
Coordina la ejecución de todos los scrapers registrados,
consolida resultados y elimina duplicados.
"""

import logging
from typing import Type

from scrapers.base_scraper import BaseScraper
from models.property import Property

logger = logging.getLogger(__name__)


class ScraperService:
    """
    Servicio central que gestiona el registro y ejecución de scrapers.
    Permite añadir scrapers dinámicamente y ejecutarlos todos en secuencia.
    """

    def __init__(self, location: str = "madrid", max_pages: int = 3):
        self.location = location
        self.max_pages = max_pages
        self._scraper_classes: list[Type[BaseScraper]] = []

    def register(self, scraper_class: Type[BaseScraper]):
        """Registra una clase de scraper para ejecución posterior."""
        self._scraper_classes.append(scraper_class)
        logger.info(f"Scraper registrado: {scraper_class.SOURCE_NAME}")

    def register_all(self, scraper_classes: list[Type[BaseScraper]]):
        """Registra múltiples scrapers de una vez."""
        for cls in scraper_classes:
            self.register(cls)

    def run_all(self) -> list[Property]:
        """
        Ejecuta todos los scrapers registrados secuencialmente.
        Devuelve la lista consolidada y deduplicada de propiedades.
        """
        all_properties: list[Property] = []

        for scraper_class in self._scraper_classes:
            scraper = scraper_class(
                location=self.location,
                max_pages=self.max_pages,
            )
            try:
                results = scraper.run()
                all_properties.extend(results)
            except Exception as e:
                logger.error(
                    f"Error ejecutando {scraper_class.SOURCE_NAME}: {e}"
                )
                continue

        # Deduplicar por hash
        before = len(all_properties)
        all_properties = self._deduplicate(all_properties)
        after = len(all_properties)

        if before != after:
            logger.info(f"Deduplicación: {before} -> {after} inmuebles únicos")

        logger.info(f"Total inmuebles recopilados: {len(all_properties)}")
        return all_properties

    def _deduplicate(self, properties: list[Property]) -> list[Property]:
        """Elimina duplicados basándose en el hash único de cada propiedad."""
        seen: set[str] = set()
        unique: list[Property] = []
        for prop in properties:
            if prop.hash not in seen:
                seen.add(prop.hash)
                unique.append(prop)
        return unique
