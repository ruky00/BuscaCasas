"""
Clase base abstracta para todos los scrapers inmobiliarios.
Verificada con Playwright 1.58 en Windows (abril 2026).
"""

import random
import logging
from abc import ABC, abstractmethod
from typing import Optional
from playwright.sync_api import sync_playwright, Page

from models.property import Property
from utils.browser import create_stealth_context, human_delay, human_scroll, safe_click


class BaseScraper(ABC):
    """
    Cada portal hereda de aquí e implementa:
      - SOURCE_NAME y BASE_URL (constantes)
      - build_search_url(page_num) -> str
      - extract_listings(page) -> list[Property]

    Opcionalmente puede override:
      - get_cookie_selectors() -> list[str]
      - get_wait_selector() -> str | None
      - get_page_load_strategy() -> str
    """

    SOURCE_NAME: str = "UNKNOWN"
    BASE_URL: str = ""

    def __init__(self, location: str = "madrid", max_pages: int = 3):
        self.location = location
        self.max_pages = max_pages
        self.logger = logging.getLogger(self.__class__.__name__)
        self.properties: list[Property] = []

    def run(self) -> list[Property]:
        """Flujo principal: abrir browser -> paginar -> extraer -> cerrar."""
        self.logger.info(f"[{self.SOURCE_NAME}] Iniciando scraping para '{self.location}'...")
        self.properties = []

        pw = sync_playwright().start()
        try:
            browser, context = create_stealth_context(pw)
            page = context.new_page()

            for page_num in range(1, self.max_pages + 1):
                url = self.build_search_url(page_num)
                self.logger.info(f"[{self.SOURCE_NAME}] Pagina {page_num}: {url}")

                try:
                    strategy = self.get_page_load_strategy()
                    page.goto(url, wait_until=strategy, timeout=45000)
                    human_delay(3.0, 5.0)

                    # Cookies solo en la primera carga
                    if page_num == 1:
                        self._accept_cookies(page)

                    # Scroll para cargar contenido lazy
                    human_scroll(page, steps=random.randint(3, 5))
                    human_delay(1.0, 2.0)

                    # Esperar al selector principal si está definido
                    wait_sel = self.get_wait_selector()
                    if wait_sel:
                        try:
                            page.wait_for_selector(wait_sel, timeout=10000)
                        except Exception:
                            self.logger.warning(f"[{self.SOURCE_NAME}] Timeout esperando '{wait_sel}'")

                    # Extraer
                    new_props = self.extract_listings(page)
                    self.logger.info(
                        f"[{self.SOURCE_NAME}] Pagina {page_num}: {len(new_props)} inmuebles"
                    )
                    self.properties.extend(new_props)

                    if not new_props:
                        self.logger.info(f"[{self.SOURCE_NAME}] Sin resultados, parando paginacion.")
                        break

                    human_delay(2.0, 4.0)

                except Exception as e:
                    self.logger.error(f"[{self.SOURCE_NAME}] Error pagina {page_num}: {e}")
                    continue

            context.close()
            browser.close()
        except Exception as e:
            self.logger.error(f"[{self.SOURCE_NAME}] Error fatal: {e}")
        finally:
            pw.stop()

        self.logger.info(
            f"[{self.SOURCE_NAME}] Completado: {len(self.properties)} inmuebles totales"
        )
        return self.properties

    def _accept_cookies(self, page: Page):
        """Intenta aceptar cookies con los selectores del portal."""
        for selector in self.get_cookie_selectors():
            if safe_click(page, selector, timeout=3000):
                self.logger.debug(f"[{self.SOURCE_NAME}] Cookies aceptadas: {selector}")
                human_delay(1.0, 2.0)
                return
        self.logger.debug(f"[{self.SOURCE_NAME}] No se encontro banner de cookies")

    # --- Abstractos ---

    @abstractmethod
    def build_search_url(self, page_num: int) -> str:
        ...

    @abstractmethod
    def extract_listings(self, page: Page) -> list[Property]:
        ...

    # --- Con implementación por defecto ---

    def get_cookie_selectors(self) -> list[str]:
        return [
            "#onetrust-accept-btn-handler",
            "#didomi-notice-agree-button",
            "button[data-testid='TcfAccept']",
            "button:has-text('Aceptar')",
        ]

    def get_wait_selector(self) -> Optional[str]:
        """Selector a esperar tras cargar la página. None = no esperar."""
        return None

    def get_page_load_strategy(self) -> str:
        """'domcontentloaded' (rápido) o 'networkidle' (espera JS)."""
        return "domcontentloaded"
