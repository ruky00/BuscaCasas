"""
Scraper para Fotocasa.es
Selectores verificados abril 2026 — Fotocasa usa Tailwind CSS.
Las cards se cargan por lazy loading: hay que hacer scroll individual
a cada article para que se renderice su contenido.
"""

import random
import time
from playwright.sync_api import Page

from scrapers.base_scraper import BaseScraper
from models.property import Property
from utils.parser import parse_price, clean_text, parse_size, parse_rooms


class FotocasaScraper(BaseScraper):

    SOURCE_NAME = "FOTOCASA"
    BASE_URL = "https://www.fotocasa.es"

    def build_search_url(self, page_num: int) -> str:
        loc = self.location.lower().replace(" ", "-")
        base = f"{self.BASE_URL}/es/comprar/viviendas/{loc}/todas-las-zonas/l"
        if page_num == 1:
            return base
        return f"{base}/{page_num}"

    def get_cookie_selectors(self) -> list[str]:
        return [
            "button[data-testid='TcfAccept']",
            "#onetrust-accept-btn-handler",
            "button:has-text('Aceptar y cerrar')",
            "button:has-text('Aceptar')",
        ]

    def get_wait_selector(self) -> str:
        return "article"

    def extract_listings(self, page: Page) -> list[Property]:
        # Fotocasa usa lazy loading agresivo: scrollear cada article al viewport
        self._trigger_lazy_load(page)

        properties = []
        articles = page.query_selector_all("article")
        self.logger.debug(f"[{self.SOURCE_NAME}] Articles encontrados: {len(articles)}")

        for article in articles:
            try:
                prop = self._parse_article(article)
                if prop:
                    properties.append(prop)
            except Exception as e:
                self.logger.debug(f"[{self.SOURCE_NAME}] Error parseando article: {e}")
                continue

        return properties

    def _trigger_lazy_load(self, page: Page):
        """Hace scroll individual a cada article para forzar la carga lazy."""
        count = page.evaluate('document.querySelectorAll("article").length')
        for i in range(count):
            try:
                page.evaluate(f'''() => {{
                    const arts = document.querySelectorAll("article");
                    if (arts[{i}]) arts[{i}].scrollIntoView({{behavior:"smooth",block:"center"}});
                }}''')
                time.sleep(0.3 + random.random() * 0.4)
            except Exception:
                pass
        time.sleep(1.5)

    def _parse_article(self, article) -> Property | None:
        # URL del inmueble
        link = article.query_selector("a[href*='/comprar/vivienda']")
        if not link:
            link = article.query_selector("a[href*='/comprar/']")
        if not link:
            return None
        href = link.get_attribute("href") or ""
        if not href or "/comprar/" not in href:
            return None
        url = href if href.startswith("http") else f"{self.BASE_URL}{href}"

        # Título
        title_el = article.query_selector("h3")
        title = clean_text(title_el.inner_text()) if title_el else ""

        # Precio — span con '€'
        price = None
        spans = article.query_selector_all("span")
        for span in spans:
            text = span.inner_text().strip()
            if "€" in text and len(text) < 30:
                price = parse_price(text)
                if price:
                    break

        # Ubicación
        location = self.location
        loc_el = article.query_selector("p.text-body-1, p[class*='opacity']")
        if loc_el:
            loc_text = clean_text(loc_el.inner_text())
            if loc_text:
                location = loc_text

        # Habitaciones y m²
        rooms = None
        size_m2 = None
        full_text = article.inner_text()
        rooms = parse_rooms(full_text)
        size_m2 = parse_size(full_text)

        if not title and not price:
            return None

        return Property(
            source=self.SOURCE_NAME,
            title=title or "Sin título",
            price=price,
            location=location,
            url=url,
            rooms=rooms,
            size_m2=size_m2,
        )
