"""Lectura no destructiva de fuentes EPH y preservación de códigos."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

import pandas as pd


def _read_txt(stream: BytesIO | str) -> pd.DataFrame:
    return pd.read_csv(stream, sep=";", dtype=str, low_memory=False)


def read_individual(path: str | Path) -> pd.DataFrame:
    """Lee una base individual XLS/XLSX/TXT o un ZIP oficial sin alterar la fuente."""
    source = Path(path)
    suffix = source.suffix.lower()
    if suffix == ".zip":
        with ZipFile(source) as archive:
            members = [
                name for name in archive.namelist()
                if "usu_individual" in name.lower()
                and Path(name).suffix.lower() in {".txt", ".xls", ".xlsx"}
            ]
            if len(members) != 1:
                raise ValueError(f"No se identificó un único archivo individual en {source}")
            member = members[0]
            payload = BytesIO(archive.read(member))
            if Path(member).suffix.lower() == ".txt":
                return _read_txt(payload)
            return pd.read_excel(payload, dtype=str)
    if suffix == ".txt":
        return _read_txt(str(source))
    if suffix in {".xls", ".xlsx"}:
        return pd.read_excel(source, dtype=str)
    raise ValueError(f"Formato no soportado: {source}")
