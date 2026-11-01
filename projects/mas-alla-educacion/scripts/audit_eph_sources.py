"""Auditoría reproducible de fuentes EPH; sólo lee entradas y escribe reportes."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from eph_genero_tecnologia.data_io import read_individual
from eph_genero_tecnologia.quality import audit_individual, audit_repeated_observations, weighted_crosstab
from eph_genero_tecnologia.sector import provisional_sector
from eph_genero_tecnologia.variables import classify_technology


def parse_source(value: str) -> tuple[str, Path]:
    quarter, path = value.split("=", 1)
    return quarter, Path(path)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", action="append", required=True, help="TRIMESTRE=RUTA")
    parser.add_argument("--out-dir", type=Path, default=Path("reports/generated/eph_audit"))
    args = parser.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)

    frames = []
    quality = []
    for value in args.source:
        quarter, path = parse_source(value)
        frame = read_individual(path)
        frame["_quarter"] = quarter
        frame["TECNOLOGIA"] = classify_technology(frame["PP04D_COD"])
        frame["SECTOR_PROVISIONAL"] = provisional_sector(frame["PP04B_COD"])
        frames.append(frame)
        quality.append(audit_individual(frame, quarter))

        analytical = frame[frame["TECNOLOGIA"].notna()].copy()
        sector_totals = analytical.assign(_weight=pd.to_numeric(analytical["PONDERA"], errors="coerce")).groupby("SECTOR_PROVISIONAL", dropna=False).agg(unweighted=("SECTOR_PROVISIONAL", "size"), weighted=("_weight", "sum")).reset_index()
        sector_totals.to_csv(args.out_dir / f"{quarter}_sector_totals.csv", index=False)

        for rows, filename in [
            (["TECNOLOGIA", "CH04"], "technology_by_sex"),
            (["SECTOR_PROVISIONAL", "TECNOLOGIA"], "sector_by_technology"),
            (["SECTOR_PROVISIONAL", "CH04"], "sector_by_sex"),
            (["SECTOR_PROVISIONAL", "NIVEL_ED"], "sector_by_education"),
        ]:
            if all(column in analytical.columns for column in rows):
                table = analytical.copy()
                if len(rows) == 2:
                    table["_group"] = table[rows[0]].astype("string") + "|" + table[rows[1]].astype("string")
                    table["_count"] = 1
                    table["_weight"] = pd.to_numeric(table["PONDERA"], errors="coerce")
                    table.groupby("_group", dropna=False).agg(
                        unweighted=("_count", "sum"), weighted=("_weight", "sum")
                    ).reset_index().to_csv(
                        args.out_dir / f"{quarter}_{filename}.csv", index=False
                    )

    (args.out_dir / "quality_by_quarter.json").write_text(
        json.dumps(quality, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    audit_repeated_observations(frames).to_csv(args.out_dir / "potential_repeats.csv", index=False)
    print(json.dumps(quality, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
