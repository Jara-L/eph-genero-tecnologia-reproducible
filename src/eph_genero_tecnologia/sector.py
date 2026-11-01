"""Clasificación sectorial provisional basada en CAES-Mercosur 1.0."""

from __future__ import annotations

import pandas as pd

SECTOR_BY_PREFIX = {
    **{f"{i:02d}": "Agropecuario, silvicultura y pesca" for i in range(1, 4)},
    **{f"{i:02d}": "Minería y canteras" for i in range(5, 10)},
    **{f"{i:02d}": "Industria manufacturera" for i in range(10, 34)},
    **{f"{i:02d}": "Energía, agua y residuos" for i in range(35, 40)},
    "40": "Construcción",
    "45": "Comercio",
    "48": "Comercio",
    **{f"{i:02d}": "Transporte y almacenamiento" for i in range(49, 54)},
    "55": "Hotelería y restaurantes",
    "56": "Hotelería y restaurantes",
    **{f"{i:02d}": "Información y comunicaciones" for i in range(58, 64)},
    **{f"{i:02d}": "Finanzas y seguros" for i in range(64, 67)},
    "68": "Actividades inmobiliarias",
    **{f"{i:02d}": "Servicios profesionales, científicos y técnicos" for i in range(69, 76)},
    **{f"{i:02d}": "Servicios administrativos y de apoyo" for i in range(77, 83)},
    "84": "Administración pública",
    "85": "Educación",
    **{f"{i:02d}": "Salud y servicios sociales" for i in range(86, 89)},
    **{f"{i:02d}": "Artes, recreación y otros servicios" for i in range(90, 97)},
    "97": "Hogares empleadores",
    "98": "Hogares empleadores",
    "99": "Organismos extraterritoriales",
}


def caes4(code: pd.Series) -> pd.Series:
    return code.astype("string").str.strip().str.replace(r"\.0$", "", regex=True).str.zfill(4)


def provisional_sector(code: pd.Series) -> pd.Series:
    return caes4(code).str[:2].map(SECTOR_BY_PREFIX).fillna("No clasificado")
