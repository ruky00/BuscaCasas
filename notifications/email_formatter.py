"""
Generador de emails HTML con scoring visual.
Estilo SaaS profesional (mismo que la landing de BuscaCasas).
Todo inline CSS para compatibilidad con Gmail, Outlook, Apple Mail.
"""

import logging
from datetime import datetime
from typing import Optional

from models.property import Property

logger = logging.getLogger(__name__)

# ─── Paleta de colores ───────────────────────────────────────────────────────
C_BG = "#f8f9fb"
C_WHITE = "#ffffff"
C_TEXT = "#1a1a2e"
C_TEXT_SEC = "#5a5a72"
C_TEXT_LIGHT = "#8888a0"
C_PRIMARY = "#4f46e5"
C_PRIMARY_LIGHT = "#eef2ff"
C_GREEN = "#10b981"
C_GREEN_BG = "#ecfdf5"
C_RED = "#ef4444"
C_RED_BG = "#fef2f2"
C_YELLOW = "#f59e0b"
C_YELLOW_BG = "#fef3c7"
C_BORDER = "#e5e7eb"

# ─── Estrellas y colores por score ───────────────────────────────────────────
STAR_FILLED = "&#9733;"   # ★
STAR_EMPTY = "&#9734;"    # ☆


def _format_price(price: Optional[int]) -> str:
    if not price:
        return "Consultar"
    return f"{price:,.0f} &euro;".replace(",", ".")


def _format_ppm2(ppm2: Optional[int]) -> str:
    if not ppm2:
        return ""
    return f"{ppm2:,.0f} &euro;/m&sup2;".replace(",", ".")


def _stars_html(stars: int) -> str:
    """Genera estrellas con colores: doradas para filled, grises para empty."""
    filled = (
        f'<span style="color:{C_YELLOW};font-size:16px;letter-spacing:1px;">'
        + (STAR_FILLED * stars)
        + "</span>"
    )
    empty = ""
    if stars < 5:
        empty = (
            f'<span style="color:#d1d5db;font-size:16px;letter-spacing:1px;">'
            + (STAR_EMPTY * (5 - stars))
            + "</span>"
        )
    return filled + empty


def _score_badge(prop: Property) -> str:
    """Badge de oportunidad con color segun nivel de score."""
    if prop.score >= 4.5:
        bg, color, border = "#fef2f2", "#dc2626", "#fecaca"
        icon = "&#128293;"  # 🔥
    elif prop.score >= 4.0:
        bg, color, border = C_YELLOW_BG, "#b45309", "#fde68a"
        icon = "&#11088;"   # ⭐
    elif prop.score >= 3.5:
        bg, color, border = C_GREEN_BG, "#059669", "#a7f3d0"
        icon = "&#9989;"    # ✅
    else:
        bg, color, border = C_PRIMARY_LIGHT, C_PRIMARY, "#c7d2fe"
        icon = "&#128270;"  # 🔎

    return (
        f'<span style="display:inline-block;padding:4px 12px;border-radius:6px;'
        f'font-size:12px;font-weight:700;background:{bg};color:{color};'
        f'border:1px solid {border};">'
        f'{icon} {prop.score_label}</span>'
    )


def _source_badge(source: str) -> str:
    colors = {
        "FOTOCASA": (C_PRIMARY_LIGHT, C_PRIMARY),
        "PISOS.COM": (C_GREEN_BG, "#059669"),
        "REDPISO": (C_RED_BG, "#dc2626"),
    }
    bg, color = colors.get(source, ("#f3f4f6", "#374151"))
    return (
        f'<span style="display:inline-block;padding:3px 10px;border-radius:4px;'
        f'font-size:11px;font-weight:600;background:{bg};color:{color};">'
        f'{source}</span>'
    )


def _property_card(prop: Property, index: int) -> str:
    """Card HTML de un inmueble con scoring visual."""
    price_str = _format_price(prop.price)
    ppm2_str = _format_ppm2(prop.price_per_m2)
    rooms_str = f"{prop.rooms} hab" if prop.rooms else ""
    size_str = f"{prop.size_m2} m&sup2;" if prop.size_m2 else ""
    details_parts = [x for x in [rooms_str, size_str] if x]
    details = " &middot; ".join(details_parts)

    # Borde izquierdo segun score
    if prop.score >= 4.5:
        left_border = f"border-left:4px solid {C_RED};"
    elif prop.score >= 4.0:
        left_border = f"border-left:4px solid {C_YELLOW};"
    elif prop.score >= 3.5:
        left_border = f"border-left:4px solid {C_GREEN};"
    else:
        left_border = f"border-left:4px solid {C_BORDER};"

    desc_html = ""
    if prop.description:
        short_desc = prop.description[:140]
        if len(prop.description) > 140:
            short_desc += "..."
        desc_html = (
            f'<p style="margin:8px 0 0;font-size:13px;color:{C_TEXT_LIGHT};'
            f'line-height:1.5;">{short_desc}</p>'
        )

    # Numero de ranking
    if index == 0:
        rank_bg, rank_color = C_YELLOW_BG, "#b45309"
    elif index < 3:
        rank_bg, rank_color = C_PRIMARY_LIGHT, C_PRIMARY
    else:
        rank_bg, rank_color = C_BG, C_TEXT_LIGHT

    return f'''
    <tr>
        <td style="padding:0 0 14px 0;">
            <table cellpadding="0" cellspacing="0" border="0" width="100%"
                   style="background:{C_WHITE};border:1px solid {C_BORDER};
                          {left_border}border-radius:12px;overflow:hidden;">
                <tr>
                    <td style="padding:22px 24px;">

                        <!-- Row 1: Badge oportunidad + Estrellas -->
                        <table cellpadding="0" cellspacing="0" border="0" width="100%">
                            <tr>
                                <td style="vertical-align:middle;">
                                    {_score_badge(prop)}
                                </td>
                                <td style="vertical-align:middle;text-align:right;">
                                    {_stars_html(prop.score_stars)}
                                    <span style="font-size:13px;font-weight:700;
                                        color:{C_TEXT_SEC};margin-left:4px;">
                                        {prop.score}/5</span>
                                </td>
                            </tr>
                        </table>

                        <!-- Row 2: Content -->
                        <table cellpadding="0" cellspacing="0" border="0" width="100%"
                               style="margin-top:14px;">
                            <tr>
                                <!-- Rank number -->
                                <td style="vertical-align:top;padding:0 16px 0 0;width:40px;">
                                    <div style="width:36px;height:36px;border-radius:50%;
                                        background:{rank_bg};color:{rank_color};
                                        font-size:14px;font-weight:700;text-align:center;
                                        line-height:36px;">{index + 1}</div>
                                </td>
                                <td style="vertical-align:top;">
                                    <!-- Source -->
                                    {_source_badge(prop.source)}

                                    <!-- Title -->
                                    <h3 style="margin:8px 0 6px;font-size:16px;font-weight:700;
                                        color:{C_TEXT};line-height:1.3;">
                                        <a href="{prop.url}" style="color:{C_TEXT};
                                           text-decoration:none;" target="_blank">
                                            {prop.title}
                                        </a>
                                    </h3>

                                    <!-- Price row -->
                                    <table cellpadding="0" cellspacing="0" border="0">
                                        <tr>
                                            <td style="padding:0 12px 0 0;">
                                                <span style="font-size:22px;font-weight:800;
                                                    color:{C_GREEN};">{price_str}</span>
                                            </td>
                                            <td style="vertical-align:middle;">
                                                <span style="font-size:12px;font-weight:600;
                                                    color:{C_TEXT_LIGHT};">{ppm2_str}</span>
                                            </td>
                                        </tr>
                                    </table>

                                    <!-- Location + details -->
                                    <p style="margin:4px 0 0;font-size:13px;color:{C_TEXT_SEC};">
                                        {prop.location}
                                        {f" &middot; {details}" if details else ""}
                                    </p>

                                    {desc_html}
                                </td>
                            </tr>
                        </table>

                        <!-- CTA -->
                        <table cellpadding="0" cellspacing="0" border="0"
                               style="margin-top:16px;">
                            <tr>
                                <td style="background:{C_PRIMARY};border-radius:6px;">
                                    <a href="{prop.url}" target="_blank"
                                       style="display:inline-block;padding:10px 22px;
                                              font-size:13px;font-weight:600;
                                              color:#ffffff;text-decoration:none;
                                              font-family:Arial,sans-serif;">
                                        Ver propiedad &rarr;
                                    </a>
                                </td>
                            </tr>
                        </table>
                    </td>
                </tr>
            </table>
        </td>
    </tr>'''


def _date_es() -> str:
    """Fecha en espanol."""
    months = {
        1: "enero", 2: "febrero", 3: "marzo", 4: "abril",
        5: "mayo", 6: "junio", 7: "julio", 8: "agosto",
        9: "septiembre", 10: "octubre", 11: "noviembre", 12: "diciembre",
    }
    now = datetime.now()
    return f"{now.day} de {months[now.month]} de {now.year}"


class EmailFormatter:
    """
    Genera HTML para emails con scoring de oportunidades.
    Solo incluye las propiedades ya filtradas (top oportunidades).
    """

    def format(
        self,
        properties: list[Property],
        location: str = "Madrid",
        total_analyzed: int = 0,
    ) -> str:
        """
        Genera email HTML con:
        - Header con copy de urgencia
        - Resumen: analizados vs seleccionados
        - Cards con estrellas, badges, precio/m2
        - Footer
        """
        date_str = _date_es()
        now = datetime.now()

        if not properties:
            return self._empty_report(date_str, location, total_analyzed)

        total_shown = len(properties)
        if total_analyzed == 0:
            total_analyzed = total_shown

        prices = [p.price for p in properties if p.price]
        min_price = min(prices) if prices else 0
        avg_score = sum(p.score for p in properties) / len(properties)

        sources = {}
        for p in properties:
            sources[p.source] = sources.get(p.source, 0) + 1

        # Cards (ya vienen ordenadas por score)
        cards_html = ""
        for i, prop in enumerate(properties):
            cards_html += _property_card(prop, i)

        # Source badges
        sources_html = ""
        for src, count in sorted(sources.items()):
            sources_html += f'<td style="padding:0 4px;">{_source_badge(src)}</td>'

        # Copy dinamico del header
        if total_shown == 1:
            headline = "Hemos detectado 1 oportunidad destacada hoy"
        elif total_shown <= 3:
            headline = f"Hemos detectado {total_shown} oportunidades destacadas hoy"
        else:
            headline = f"{total_shown} oportunidades detectadas para ti"

        return f'''<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>BuscaCasas - Oportunidades del dia</title>
</head>
<body style="margin:0;padding:0;background:{C_BG};font-family:Arial,'Helvetica Neue',Helvetica,sans-serif;color:{C_TEXT};-webkit-font-smoothing:antialiased;">

    <table cellpadding="0" cellspacing="0" border="0" width="100%"
           style="background:{C_BG};">
        <tr>
            <td align="center" style="padding:32px 16px;">
                <table cellpadding="0" cellspacing="0" border="0"
                       width="640" style="max-width:640px;width:100%;">

                    <!-- ═══ HEADER ═══ -->
                    <tr>
                        <td style="padding:0 0 24px;">
                            <table cellpadding="0" cellspacing="0" border="0" width="100%"
                                   style="background:linear-gradient(135deg,{C_PRIMARY} 0%,#7c3aed 100%);
                                          border-radius:16px;overflow:hidden;">
                                <tr>
                                    <td style="padding:40px 32px;text-align:center;">
                                        <p style="margin:0 0 6px;font-size:13px;font-weight:600;
                                           color:rgba(255,255,255,0.6);letter-spacing:1.5px;
                                           text-transform:uppercase;">&#9678; BuscaCasas</p>

                                        <h1 style="margin:0 0 10px;font-size:26px;font-weight:800;
                                            color:#ffffff;line-height:1.3;">
                                            {headline}
                                        </h1>

                                        <p style="margin:0;font-size:15px;color:rgba(255,255,255,0.75);">
                                            {date_str} &middot; {location} &middot;
                                            {total_analyzed} inmuebles analizados
                                        </p>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>

                    <!-- ═══ RESUMEN ═══ -->
                    <tr>
                        <td style="padding:0 0 20px;">
                            <table cellpadding="0" cellspacing="0" border="0" width="100%"
                                   style="background:{C_WHITE};border:1px solid {C_BORDER};
                                          border-radius:12px;overflow:hidden;">
                                <tr>
                                    <td style="padding:24px 28px;">
                                        <p style="margin:0 0 16px;font-size:11px;font-weight:600;
                                           text-transform:uppercase;letter-spacing:1.5px;
                                           color:{C_PRIMARY};">Resumen del analisis</p>

                                        <table cellpadding="0" cellspacing="0" border="0"
                                               width="100%"
                                               style="background:{C_BG};border-radius:8px;">
                                            <tr>
                                                <td style="padding:18px;text-align:center;width:25%;">
                                                    <p style="margin:0;font-size:28px;font-weight:800;
                                                       color:{C_PRIMARY};line-height:1;">
                                                       {total_analyzed}</p>
                                                    <p style="margin:4px 0 0;font-size:11px;
                                                       color:{C_TEXT_SEC};">Analizados</p>
                                                </td>
                                                <td style="padding:18px;text-align:center;width:25%;">
                                                    <p style="margin:0;font-size:28px;font-weight:800;
                                                       color:{C_GREEN};line-height:1;">
                                                       {total_shown}</p>
                                                    <p style="margin:4px 0 0;font-size:11px;
                                                       color:{C_TEXT_SEC};">Seleccionados</p>
                                                </td>
                                                <td style="padding:18px;text-align:center;width:25%;">
                                                    <p style="margin:0;font-size:28px;font-weight:800;
                                                       color:{C_YELLOW};line-height:1;">
                                                       {_stars_html(round(avg_score))}</p>
                                                    <p style="margin:4px 0 0;font-size:11px;
                                                       color:{C_TEXT_SEC};">Score medio</p>
                                                </td>
                                                <td style="padding:18px;text-align:center;width:25%;">
                                                    <p style="margin:0;font-size:28px;font-weight:800;
                                                       color:{C_GREEN};line-height:1;">
                                                       {_format_price(min_price)}</p>
                                                    <p style="margin:4px 0 0;font-size:11px;
                                                       color:{C_TEXT_SEC};">Desde</p>
                                                </td>
                                            </tr>
                                        </table>

                                        <table cellpadding="0" cellspacing="0" border="0"
                                               style="margin-top:16px;">
                                            <tr>
                                                <td style="padding:0 6px 0 0;font-size:13px;
                                                    color:{C_TEXT_SEC};font-weight:500;">
                                                    Fuentes:</td>
                                                {sources_html}
                                            </tr>
                                        </table>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>

                    <!-- ═══ LISTINGS ═══ -->
                    <tr>
                        <td style="padding:0 0 10px;">
                            <p style="margin:0 0 4px;font-size:11px;font-weight:600;
                               text-transform:uppercase;letter-spacing:1.5px;
                               color:{C_PRIMARY};">
                                Top oportunidades &mdash; ordenadas por scoring</p>
                            <p style="margin:0 0 14px;font-size:13px;color:{C_TEXT_LIGHT};">
                                Solo inmuebles con puntuaci&oacute;n destacada.
                                Act&uacute;a r&aacute;pido, las mejores oportunidades no duran.</p>
                        </td>
                    </tr>
                    <tr>
                        <td>
                            <table cellpadding="0" cellspacing="0" border="0" width="100%">
                                {cards_html}
                            </table>
                        </td>
                    </tr>

                    <!-- ═══ FOOTER ═══ -->
                    <tr>
                        <td style="padding:32px 0 0;">
                            <table cellpadding="0" cellspacing="0" border="0" width="100%"
                                   style="border-top:1px solid {C_BORDER};">
                                <tr>
                                    <td style="padding:24px 0;text-align:center;">
                                        <p style="margin:0 0 8px;font-size:14px;font-weight:700;
                                           color:{C_TEXT};">&#9678; BuscaCasas</p>
                                        <p style="margin:0 0 4px;font-size:12px;color:{C_TEXT_LIGHT};">
                                            Informe generado el {date_str}</p>
                                        <p style="margin:0;font-size:12px;color:{C_TEXT_LIGHT};">
                                            {total_analyzed} inmuebles analizados de
                                            {", ".join(sorted(sources.keys()))}</p>
                                        <p style="margin:12px 0 0;font-size:11px;color:{C_TEXT_LIGHT};">
                                            &copy; {now.year} BuscaCasas &middot;
                                            Oportunidades inmobiliarias con IA</p>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>

                </table>
            </td>
        </tr>
    </table>

</body>
</html>'''

    def format_plain_text(
        self,
        properties: list[Property],
        location: str = "Madrid",
        total_analyzed: int = 0,
    ) -> str:
        """Version texto plano con scoring."""
        if not properties:
            return f"BuscaCasas - No se encontraron oportunidades destacadas en {location} hoy."

        if total_analyzed == 0:
            total_analyzed = len(properties)

        lines = [
            "BUSCACASAS - OPORTUNIDADES DESTACADAS",
            f"Fecha: {datetime.now().strftime('%d/%m/%Y')}",
            f"Ubicacion: {location}",
            f"Analizados: {total_analyzed} | Seleccionados: {len(properties)}",
            "",
            "=" * 60,
        ]

        for i, p in enumerate(properties, 1):
            price_str = f"{p.price:,.0f} EUR".replace(",", ".") if p.price else "Consultar"
            stars = "*" * p.score_stars + "." * (5 - p.score_stars)
            details = []
            if p.rooms:
                details.append(f"{p.rooms} hab")
            if p.size_m2:
                details.append(f"{p.size_m2} m2")
            if p.price_per_m2:
                details.append(f"{p.price_per_m2:,} EUR/m2".replace(",", "."))

            lines.append("")
            lines.append(f"  {i}. [{stars}] {p.score}/5 - {p.score_label}")
            lines.append(f"     [{p.source}] {p.title}")
            lines.append(f"     {price_str} - {p.location}")
            if details:
                lines.append(f"     {' | '.join(details)}")
            lines.append(f"     {p.url}")

        lines.append("")
        lines.append("=" * 60)
        lines.append("Generado automaticamente por BuscaCasas")
        return "\n".join(lines)

    def _empty_report(self, date_str: str, location: str, total_analyzed: int) -> str:
        analyzed_text = (
            f"Hemos analizado {total_analyzed} inmuebles pero ninguno super&oacute; "
            f"el umbral de calidad."
            if total_analyzed > 0
            else f"No hemos encontrado inmuebles en {location}."
        )
        return f'''<!DOCTYPE html>
<html lang="es">
<head><meta charset="UTF-8"></head>
<body style="margin:0;padding:0;background:{C_BG};font-family:Arial,sans-serif;color:{C_TEXT};">
    <table cellpadding="0" cellspacing="0" border="0" width="100%" style="background:{C_BG};">
        <tr><td align="center" style="padding:32px 16px;">
            <table cellpadding="0" cellspacing="0" border="0" width="640"
                   style="max-width:640px;width:100%;">
                <tr><td style="background:linear-gradient(135deg,{C_PRIMARY} 0%,#7c3aed 100%);
                        border-radius:16px;padding:40px 32px;text-align:center;">
                    <p style="margin:0 0 4px;font-size:14px;font-weight:600;
                       color:rgba(255,255,255,0.7);letter-spacing:1px;
                       text-transform:uppercase;">&#9678; BuscaCasas</p>
                    <h1 style="margin:0 0 12px;font-size:24px;font-weight:800;
                        color:#ffffff;">Sin oportunidades destacadas hoy</h1>
                    <p style="margin:0;font-size:15px;color:rgba(255,255,255,0.8);">
                        {analyzed_text}<br>Seguiremos buscando.</p>
                </td></tr>
                <tr><td style="padding:24px 0;text-align:center;">
                    <p style="font-size:12px;color:{C_TEXT_LIGHT};">
                        {date_str} &middot; &copy; {datetime.now().year} BuscaCasas</p>
                </td></tr>
            </table>
        </td></tr>
    </table>
</body></html>'''
