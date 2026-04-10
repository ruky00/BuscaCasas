"""
Scraper para Pisos.com
Selectores verificados abril 2026.
Estructura: div.ad-preview con:
  - a.ad-preview__title (título + link)
  - span.ad-preview__price (precio)
  - p.ad-preview__subtitle (ubicación)
  - p.ad-preview__char (características: habs, baños, m², planta)
  - p.ad-preview__description (descripción)
"""

from playwright.sync_api import Page

from scrapers.base_scraper import BaseScraper
from models.property import Property
from utils.parser import parse_price, clean_text, parse_rooms, parse_size


class PisosScraper(BaseScraper):

    SOURCE_NAME = "PISOS.COM"
    BASE_URL = "https://www.pisos.com"

    def build_search_url(self, page_num: int) -> str:
        loc = self.location.lower().replace(" ", "-")
        if page_num == 1:
            return f"{self.BASE_URL}/venta/pisos-{loc}/"
        return f"{self.BASE_URL}/venta/pisos-{loc}/{page_num}/"

    def get_cookie_selectors(self) -> list[str]:
        return [
            "#didomi-notice-agree-button",
            "button:has-text('Aceptar')",
        ]

    def get_wait_selector(self) -> str:
        return "div.ad-preview"

    def get_page_load_strategy(self) -> str:
        return "networkidle"

    def extract_listings(self, page: Page) -> list[Property]:
        properties = []
        cards = page.query_selector_all("div.ad-preview")
        self.logger.debug(f"[{self.SOURCE_NAME}] Cards encontradas: {len(cards)}")

        for card in cards:
            try:
                prop = self._parse_card(card)
                if prop:
                    properties.append(prop)
            except Exception as e:
                self.logger.debug(f"[{self.SOURCE_NAME}] Error parseando card: {e}")
                continue

        return properties

    def _parse_card(self, card) -> Property | None:
        # Título y URL
        title_el = card.query_selector("a.ad-preview__title")
        if not title_el:
            return None
        title = clean_text(title_el.inner_text())
        href = title_el.get_attribute("href") or ""
        if not href:
            return None
        url = href if href.startswith("http") else f"{self.BASE_URL}{href}"

        # Precio
        price_el = card.query_selector("span.ad-preview__price")
        price = parse_price(price_el.inner_text()) if price_el else None

        # Ubicación
        subtitle_el = card.query_selector("p.ad-preview__subtitle")
        location = clean_text(subtitle_el.inner_text()) if subtitle_el else self.location

        # Características
        rooms = None
        size_m2 = None
        chars = card.query_selector_all("p.ad-preview__char")
        for char_el in chars:
            text = char_el.inner_text().strip()
            if "hab" in text.lower():
                rooms = parse_rooms(text)
            elif "m²" in text or "m2" in text.lower():
                size_m2 = parse_size(text)

        # Descripción
        desc_el = card.query_selector("p.ad-preview__description")
        description = clean_text(desc_el.inner_text()) if desc_el else None

        return Property(
            source=self.SOURCE_NAME,
            title=title,
            price=price,
            location=location,
            url=url,
            description=description,
            rooms=rooms,
            size_m2=size_m2,
        )
