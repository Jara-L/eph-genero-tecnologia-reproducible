"""Auditorías descriptivas y de integridad para bases EPH."""

from __future__ import annotations

from typing import Iterable

import pandas as pd

from .variables import classify_technology, normalize_code


def _count(series: pd.Series) -> dict[str, int]:
    return {str(k): int(v) for k, v in series.value_counts(dropna=False).items()}


def audit_individual(df: pd.DataFrame, quarter: str) -> dict:
    required = ["ESTADO", "PP04D_COD", "PP04B_COD", "CH04", "CH06", "NIVEL_ED", "PONDERA"]
    missing = [column for column in required if column not in df.columns]
    work = df.copy()
    estado = normalize_code(work["ESTADO"], 1) if "ESTADO" in work else pd.Series(dtype="string")
    occupied = estado.eq("1")
    tech = classify_technology(work["PP04D_COD"]) if "PP04D_COD" in work else pd.Series(dtype="string")
    weights = pd.to_numeric(work["PONDERA"], errors="coerce") if "PONDERA" in work else pd.Series(dtype=float)
    ages = pd.to_numeric(work["CH06"], errors="coerce") if "CH06" in work else pd.Series(dtype=float)
    return {
        "quarter": quarter,
        "records_total": int(len(work)),
        "records_occupied": int(occupied.sum()),
        "pp04d_nonmissing": int(work["PP04D_COD"].notna().sum()) if "PP04D_COD" in work else None,
        "pp04b_nonmissing": int(work["PP04B_COD"].notna().sum()) if "PP04B_COD" in work else None,
        "technology_valid": int(tech.notna().sum()),
        "pondera_nonmissing": int(weights.notna().sum()),
        "pondera_sum": float(weights.sum()) if weights.notna().any() else None,
        "age_nonmissing": int(ages.notna().sum()),
        "age_outside_0_110": int((~ages.between(0, 110) & ages.notna()).sum()),
        "missing_required_columns": missing,
        "sex_counts": _count(work["CH04"]) if "CH04" in work else {},
        "education_counts": _count(work["NIVEL_ED"]) if "NIVEL_ED" in work else {},
        "agglomerate_counts": _count(work["AGLOMERADO"]) if "AGLOMERADO" in work else {},
        "technology_counts": _count(tech),
        "sector_counts": _count(normalize_code(work["PP04B_COD"], 4)) if "PP04B_COD" in work else {},
    }


def weighted_crosstab(
    df: pd.DataFrame, rows: str, columns: str, weight: str = "PONDERA"
) -> pd.DataFrame:
    """Devuelve conteos, suma de ponderadores y porcentajes dentro de cada fila."""
    work = df[[rows, columns, weight]].copy()
    work["_weight"] = pd.to_numeric(work[weight], errors="coerce")
    grouped = work.groupby([rows, columns], dropna=False, observed=False)["_weight"].agg(
        weighted="sum", unweighted="size"
    ).reset_index()
    grouped["row_percent"] = grouped["weighted"] / grouped.groupby(rows)["weighted"].transform("sum") * 100
    return grouped


def audit_repeated_observations(frames: Iterable[pd.DataFrame]) -> pd.DataFrame:
    """Resume repeticiones potenciales sin eliminar registros."""
    combined = pd.concat(frames, ignore_index=True)
    identity = ["CODUSU", "NRO_HOGAR", "COMPONENTE"]
    missing = sorted(set(identity) - set(combined.columns))
    if missing:
        return pd.DataFrame({"status": ["missing_identity_columns"], "missing": [str(missing)]})

    # The external quarter label is authoritative when supplied by the audit
    # runner. TRIMESTRE is retained as a source field and must not be used as
    # a cross-file period identifier.
    if "_quarter" in combined.columns:
        period = combined["_quarter"].astype("string")
    elif {"ANO4", "TRIMESTRE"}.issubset(combined.columns):
        period = combined["ANO4"].astype("string") + "-T" + combined["TRIMESTRE"].astype("string")
    else:
        return pd.DataFrame({"status": ["missing_period_columns"], "missing": ["['_quarter'] or ['ANO4', 'TRIMESTRE']"]})

    available = sorted(period.dropna().unique().tolist())
    if len(available) < 2:
        return pd.DataFrame({
            "status": ["insufficient_quarters"],
            "quarters_available": ["|".join(available)],
            "n_quarters": [len(available)],
        })

    person = combined.assign(
        _person_key=(
            combined["CODUSU"].astype("string") + "|" +
            combined["NRO_HOGAR"].astype("string") + "|" +
            combined["COMPONENTE"].astype("string")
        ),
        _period=period,
    )
    return (
        person.dropna(subset=["_person_key", "_period"])
        .groupby("_person_key", dropna=False)
        .agg(periods=("_period", "nunique"), rows=("_period", "size"), quarters=("_period", lambda x: "|".join(sorted(x.unique()))))
        .assign(potentially_repeated=lambda x: x["periods"] > 1)
        .reset_index()
    )
