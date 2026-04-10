"""
Configuración de Playwright con medidas anti-detección.
Verificado contra Fotocasa, Pisos.com y Redpiso (abril 2026).
"""

import random
import time
import logging
from playwright.sync_api import Browser, BrowserContext, Page

logger = logging.getLogger(__name__)

# User agents reales de Chrome 124-145 en Windows/Mac
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
]

# Script stealth: elimina huellas de automatización
STEALTH_SCRIPT = """
Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
Object.defineProperty(navigator, 'languages', {get: () => ['es-ES', 'es', 'en']});
Object.defineProperty(navigator, 'plugins', {
    get: () => [1, 2, 3, 4, 5]
});
window.chrome = {runtime: {}, loadTimes: function(){}, csi: function(){}};
Object.defineProperty(navigator, 'maxTouchPoints', {get: () => 0});
Object.defineProperty(navigator, 'platform', {get: () => 'Win32'});
// Eliminar la propiedad que delata Playwright
delete window.__playwright;
delete window.__pw_manual;
"""


def create_stealth_context(playwright) -> tuple[Browser, BrowserContext]:
    """
    Crea browser + context con anti-detección.
    El llamante debe cerrarlos al terminar.
    """
    user_agent = random.choice(USER_AGENTS)
    logger.debug(f"User-Agent: {user_agent}")

    browser = playwright.chromium.launch(
        headless=True,
        args=[
            "--disable-blink-features=AutomationControlled",
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--disable-infobars",
            "--window-size=1920,1080",
        ],
    )

    context = browser.new_context(
        user_agent=user_agent,
        viewport={"width": 1920, "height": 1080},
        locale="es-ES",
        timezone_id="Europe/Madrid",
        geolocation={"latitude": 40.4168, "longitude": -3.7038},
        permissions=["geolocation"],
    )

    context.add_init_script(STEALTH_SCRIPT)
    return browser, context


def human_delay(min_sec: float = 1.0, max_sec: float = 3.0):
    """Pausa aleatoria para simular comportamiento humano."""
    time.sleep(random.uniform(min_sec, max_sec))


def human_scroll(page: Page, steps: int = 3):
    """Simula scroll humano gradual hacia abajo."""
    for _ in range(steps):
        page.mouse.wheel(0, random.randint(300, 700))
        human_delay(0.5, 1.5)


def safe_click(page: Page, selector: str, timeout: int = 5000) -> bool:
    """Click seguro: intenta y devuelve True/False."""
    try:
        el = page.wait_for_selector(selector, timeout=timeout)
        if el:
            el.click()
            human_delay(0.5, 1.0)
            return True
    except Exception:
        pass
    return False
