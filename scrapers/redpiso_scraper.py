"""
Scraper para Redpiso.es
Selectores verificados abril 2026. Redpiso usa Vue + Tailwind.
Estructura: div.group.relative.flex con:
  - a[href*="/inmueble/"] (link + aria-label con ubicación)
  - p.font-bold.text-lg.text-red-500 (precio)
  - h3.text-gray-600 (ubicación)
  - div con spans para hab, baños, m²
"""

from playwright.sync_api import Page

from scrapers.base_scraper import BaseScraper
from models.property import Property
from utils.parser import parse_price, clean_text, parse_size, parse_rooms_from_number, extract_title_from_url


class RedpisoScraper(BaseScraper):

    SOURCE_NAME = "REDPISO"
    BASE_URL = "https://www.redpiso.es"

    def build_search_url(self, page_num: int) -> str:
        loc = self.location.lower().replace(" ", "-")
        base = f"{self.BASE_URL}/venta-viviendas/{loc}"
        if page_num == 1:
            return base
        return f"{base}?pagina={page_num}"

    def get_cookie_selectors(self) -> list[str]:
        return [
            "#onetrust-accept-btn-handler",
            "button:has-text('Aceptar cookies')",
            "button:has-text('Aceptar')",
        ]

    def get_wait_selector(self) -> str:
        return "a[href*='/inmueble/']"

    def get_page_load_strategy(self) -> str:
        return "networkidle"

    def extract_listings(self, page: Page) -> list[Property]:
        properties = []
        cards = page.query_selector_all("div.group.relative.flex")
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
        # Link al inmueble
        link = card.query_selector("a[href*='/inmueble/']")
        if not link:
            return None
        href = link.get_attribute("href") or ""
        if not href:
            return None
        url = href if href.startswith("http") else f"{self.BASE_URL}{href}"

        # Título — extraer del href (Redpiso no muestra un título explícito en la card)
        title = extract_title_from_url(href)

        # Precio — p rojo en negrita
        price = None
        price_el = card.query_selector("p.font-bold.text-lg.text-red-500")
        if price_el:
            price = parse_price(price_el.inner_text())

        # Ubicación — h3 gris
        location = self.location
        loc_el = card.query_selector("h3")
        if loc_el:
            loc_text = clean_text(loc_el.inner_text())
            if loc_text:
                location = loc_text

        # Aria-label como fallback de ubicación
        if location == self.location:
            aria = link.get_attribute("aria-label") or ""
            if "inmueble" in aria.lower():
                # "Visitar el inmueble San Andrés, Madrid"
                parts = aria.split("inmueble")
                if len(parts) > 1:
                    location = clean_text(parts[1])

        # Características — spans dentro del div de features
        rooms = None
        size_m2 = None
        feature_div = card.query_selector("div.flex.items-center.justify-between.text-sm")
        if feature_div:
            spans = feature_div.query_selector_all("span")
            # Patrón típico: span "3" (hab), span "1" (baños), span "86 m²"
            for span in spans:
                text = span.inner_text().strip()
                if "m²" in text or "m2" in text.lower():
                    size_m2 = parse_size(text)
                elif not rooms and text.isdigit():
                    rooms = int(text)

        if not price and not title:
            return None

        return Property(
            source=self.SOURCE_NAME,
            title=title,
            price=price,
            location=location,
            url=url,
            rooms=rooms,
            size_m2=size_m2,
        )
