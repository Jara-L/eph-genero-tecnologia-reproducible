"""Construcción conservadora de variables EPH."""

from __future__ import annotations

import pandas as pd


def normalize_code(values: pd.Series, width: int) -> pd.Series:
    """Conserva códigos como texto y repone ceros iniciales."""
    result = values.astype("string").str.strip().str.replace(r"\.0$", "", regex=True)
    result = result.mask(result.isin({"", "nan", "None", "<NA>"}))
    return result.str.zfill(width)


def classify_technology(cno: pd.Series) -> pd.Series:
    """Clasifica el cuarto dígito de PP04D_COD según IATA/SIMEL."""
    code = normalize_code(cno, 5)
    digit = code.str[3]
    return digit.map({
        "1": "No tecnológica",
        "2": "Operación de máquinas",
        "3": "Operación de sistemas informatizados",
    }).rename("TECNOLOGIA")


def binary_informatized(cno: pd.Series) -> pd.Series:
    return (normalize_code(cno, 5).str[3] == "3").astype("Int64").rename(
        "OCUP_INFORMATIZADA"
    )
