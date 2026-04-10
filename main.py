"""
BuscaCasas — Punto de entrada principal.
Ejecuta el scraping de portales inmobiliarios, exporta a JSON
y opcionalmente envía los resultados por email.

Uso:
    python main.py                              # Scraping + JSON
    python main.py --email                      # Scraping + JSON + email
    python main.py --location barcelona --pages 5
    python main.py --scrapers fotocasa,redpiso
"""

import argparse
import logging
import sys
from datetime import datetime

import config
from scrapers import FotocasaScraper, PisosScraper, RedpisoScraper
from services.scraper_service import ScraperService
from services.scoring_service import ScoringService
from output.writer import JsonWriter
from notifications.email_formatter import EmailFormatter
from notifications.email_sender import EmailSender

# Registro de scrapers disponibles (añadir nuevos aquí)
SCRAPER_REGISTRY = {
    "fotocasa": FotocasaScraper,
    "pisos": PisosScraper,
    "redpiso": RedpisoScraper,
}


def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("buscacasas.log", encoding="utf-8"),
        ],
    )


def parse_args():
    parser = argparse.ArgumentParser(
        description="BuscaCasas - Scraping inmobiliario multi-portal"
    )
    parser.add_argument(
        "--location", "-l",
        default=config.SEARCH_LOCATION,
        help="Ciudad o zona de busqueda (default: madrid)",
    )
    parser.add_argument(
        "--pages", "-p",
        type=int,
        default=config.MAX_PAGES,
        help="Paginas maximas por portal (default: 3)",
    )
    parser.add_argument(
        "--scrapers", "-s",
        default=config.ACTIVE_SCRAPERS,
        help="Scrapers a ejecutar, separados por coma (default: todos)",
    )
    parser.add_argument(
        "--email",
        action="store_true",
        help="Enviar resultados por email",
    )
    parser.add_argument(
        "--output-dir", "-o",
        default=config.OUTPUT_DIR,
        help="Directorio de salida JSON (default: data)",
    )
    return parser.parse_args()


def resolve_scrapers(scraper_names: str) -> list:
    names = [n.strip().lower() for n in scraper_names.split(",")]
    classes = []
    for name in names:
        if name in SCRAPER_REGISTRY:
            classes.append(SCRAPER_REGISTRY[name])
        else:
            logging.warning(
                f"Scraper desconocido: '{name}'. "
                f"Disponibles: {list(SCRAPER_REGISTRY.keys())}"
            )
    return classes


def send_email_report(top_properties, location: str, total_analyzed: int):
    """Genera HTML profesional con scoring y envía por email."""
    logger = logging.getLogger("EmailReport")

    if not config.SENDER_EMAIL or not config.RECIPIENT_EMAIL:
        logger.error("Configura SENDER_EMAIL y RECIPIENT_EMAIL en .env")
        return

    # Generar HTML y texto plano con info de scoring
    formatter = EmailFormatter()
    html_body = formatter.format(
        top_properties, location=location, total_analyzed=total_analyzed
    )
    plain_body = formatter.format_plain_text(
        top_properties, location=location, total_analyzed=total_analyzed
    )

    # Enviar
    sender = EmailSender(
        smtp_server=config.SMTP_SERVER,
        smtp_port=config.SMTP_PORT,
        sender_email=config.SENDER_EMAIL,
        sender_password=config.SENDER_PASSWORD,
    )

    today = datetime.now().strftime("%d/%m/%Y")
    n = len(top_properties)
    subject = (
        f"BuscaCasas - {n} oportunidades destacadas en {location} ({today})"
        if n > 0
        else f"BuscaCasas - Sin oportunidades hoy en {location} ({today})"
    )

    success = sender.send(
        to_email=config.RECIPIENT_EMAIL,
        subject=subject,
        html_body=html_body,
        plain_body=plain_body,
    )

    if success:
        logger.info(f"Email enviado a {config.RECIPIENT_EMAIL}")
    else:
        logger.error("No se pudo enviar el email")


def main():
    setup_logging()
    args = parse_args()
    logger = logging.getLogger("Main")

    logger.info("=" * 60)
    logger.info("  BuscaCasas — Scraping Inmobiliario")
    logger.info(f"  Ubicacion: {args.location}")
    logger.info(f"  Paginas por portal: {args.pages}")
    logger.info(f"  Scrapers: {args.scrapers}")
    logger.info("=" * 60)

    scraper_classes = resolve_scrapers(args.scrapers)
    if not scraper_classes:
        logger.error("No hay scrapers validos para ejecutar.")
        sys.exit(1)

    # 1. Scraping
    service = ScraperService(location=args.location, max_pages=args.pages)
    service.register_all(scraper_classes)
    all_properties = service.run_all()

    if not all_properties:
        logger.warning("No se encontraron inmuebles.")
    else:
        logger.info(f"Total: {len(all_properties)} inmuebles encontrados")

    # 2. Scoring — puntua todas las propiedades
    scoring = ScoringService(
        min_score=config.MIN_SCORE,
        max_results=config.MAX_EMAIL_RESULTS,
    )
    all_properties = scoring.score_all(all_properties)

    # 3. Filtrado — solo las mejores oportunidades
    top_properties = scoring.filter_top(all_properties)

    # 4. Exportar JSON (todas las propiedades, con score)
    writer = JsonWriter(output_dir=args.output_dir)
    filepath = writer.write(all_properties)
    logger.info(f"Resultados guardados en: {filepath}")

    # 5. Email (solo top oportunidades)
    if args.email:
        send_email_report(
            top_properties,
            location=args.location,
            total_analyzed=len(all_properties),
        )

    logger.info("Proceso finalizado.")


if __name__ == "__main__":
    main()
