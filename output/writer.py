"""
Módulo de exportación de datos a JSON.
"""

import json
import os
import logging
from datetime import datetime

from models.property import Property

logger = logging.getLogger(__name__)


class JsonWriter:
    """Escribe la lista de propiedades a un archivo JSON limpio."""

    def __init__(self, output_dir: str = "data"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def write(self, properties: list[Property], filename: str = None) -> str:
        """
        Exporta las propiedades a JSON.
        Devuelve la ruta del archivo generado.
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"properties_{timestamp}.json"

        filepath = os.path.join(self.output_dir, filename)

        data = {
            "metadata": {
                "total": len(properties),
                "generated_at": datetime.now().isoformat(),
                "sources": list(set(p.source for p in properties)),
            },
            "properties": [p.to_dict() for p in properties],
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        logger.info(f"JSON exportado: {filepath} ({len(properties)} inmuebles)")
        return filepath
