from __future__ import annotations

import hashlib
import json
import zipfile
from collections import Counter
from io import BytesIO
from pathlib import Path

import pandas as pd

from eph_genero_tecnologia.sector import SECTOR_BY_PREFIX
from eph_genero_tecnologia.variables import classify_technology, normalize_code


ROOT = Path(__file__).resolve().parents[3]
RAW = ROOT / "data" / "raw"
REPORT = ROOT / "reports" / "generated" / "eph_joint_audit"
PROCESSED = ROOT / "data" / "processed"
SOURCES = {
    "2025-T2": RAW / "EPH_usu_2_Trim_2025_xls.zip",
    "2025-T3": RAW / "EPH_usu_3_Trim_2025_xls.zip",
    "2025-T4": RAW / "EPH_usu_4_Trim_2025_xls.zip",
    "2026-T1": RAW / "EPH_usu_1_Trim_2026_xls.zip",
}
INDIVIDUAL_BASE = RAW / "usu_individual_T425.xlsx"
HOUSEHOLD_REQUIRED = ["CODUSU", "ANO4", "TRIMESTRE", "NRO_HOGAR", "AGLOMERADO", "PONDERA"]
INDIVIDUAL_REQUIRED = [
    "CODUSU", "ANO4", "TRIMESTRE", "NRO_HOGAR", "COMPONENTE", "REGION", "AGLOMERADO",
    "PONDERA", "CH04", "CH06", "NIVEL_ED", "ESTADO", "PP04B_COD", "PP04D_COD",
]


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def numeric(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce")


def valid_code(series: pd.Series, width: int, invalid: set[str]) -> pd.Series:
    value = normalize_code(series, width)
    return value.str.fullmatch(rf"\d{{{width}}}") & ~value.isin(invalid)


def read_member(archive: zipfile.ZipFile, member: str, usecols: list[str]) -> pd.DataFrame:
    payload = BytesIO(archive.read(member))
    return pd.read_excel(payload, dtype=str, usecols=usecols, engine="openpyxl")


def member_name(archive: zipfile.ZipFile, needle: str) -> str:
    matches = [n for n in archive.namelist() if needle in n.lower() and n.lower().endswith((".xlsx", ".xls"))]
    if len(matches) != 1:
        raise ValueError(f"Se esperaba un miembro {needle!r}, se encontraron {matches}")
    return matches[0]


def source_manifest() -> dict:
    result = {"generated_at": pd.Timestamp.now(tz="America/Argentina/Buenos_Aires").isoformat(), "sources": []}
    for quarter, path in SOURCES.items():
        item = {"quarter": quarter, "file": path.name, "path": str(path), "bytes": path.stat().st_size}
        item["sha256"] = sha256_bytes(path.read_bytes())
        with zipfile.ZipFile(path) as archive:
            item["zip_test"] = archive.testzip() is None
            item["members"] = []
            for name in archive.namelist():
                data = archive.read(name)
                member = {"name": name, "bytes": len(data), "sha256": sha256_bytes(data)}
                with pd.ExcelFile(BytesIO(data), engine="openpyxl") as book:
                    member["sheets"] = book.sheet_names
                item["members"].append(member)
        result["sources"].append(item)
    if INDIVIDUAL_BASE.exists():
        t425 = next(x for x in result["sources"] if x["quarter"] == "2025-T4")
        member = next(x for x in t425["members"] if "usu_individual" in x["name"].lower())
        result["t425_existing_individual_comparison"] = {
            "existing_file": str(INDIVIDUAL_BASE),
            "existing_bytes": INDIVIDUAL_BASE.stat().st_size,
            "existing_sha256": sha256_bytes(INDIVIDUAL_BASE.read_bytes()),
            "zip_member": member["name"],
            "zip_member_bytes": member["bytes"],
            "zip_member_sha256": member["sha256"],
            "byte_exact_match": INDIVIDUAL_BASE.read_bytes() == zipfile.ZipFile(SOURCES["2025-T4"]).read(member["name"]),
        }
    else:
        result["t425_existing_individual_comparison"] = {
            "status": "optional_comparison_file_not_present",
            "existing_file": str(INDIVIDUAL_BASE),
        }
    (REPORT / "source_manifest.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result


def harmonize(frame: pd.DataFrame, quarter: str) -> pd.DataFrame:
    out = frame.copy()
    out["source_quarter"] = quarter
    out["year"] = numeric(out["ANO4"]).astype("Int64")
    out["quarter_number"] = numeric(out["TRIMESTRE"]).astype("Int64")
    out["household_id"] = out["CODUSU"].astype("string") + "|" + normalize_code(out["NRO_HOGAR"], 2)
    out["person_candidate_id"] = out["household_id"] + "|" + normalize_code(out["COMPONENTE"], 2)
    out["sex"] = normalize_code(out["CH04"], 1)
    out["age"] = numeric(out["CH06"])
    out["education"] = normalize_code(out["NIVEL_ED"], 1)
    out["activity_status"] = normalize_code(out["ESTADO"], 1)
    out["weight_person"] = numeric(out["PONDERA"])
    out["cno_code_original"] = out["PP04D_COD"].astype("string")
    out["cno_code"] = normalize_code(out["PP04D_COD"], 5)
    out["caes_code_original"] = out["PP04B_COD"].astype("string")
    out["caes_code"] = normalize_code(out["PP04B_COD"], 4)
    out["cno_valid"] = valid_code(out["PP04D_COD"], 5, {"99999"})
    out["caes_valid"] = valid_code(out["PP04B_COD"], 4, {"9999"})
    out["occupied"] = out["activity_status"].eq("1")
    out["occupied_15plus"] = out["occupied"] & out["age"].gt(14)
    out["both_classifications_valid"] = out["occupied_15plus"] & out["cno_valid"] & out["caes_valid"]
    out["technology_category"] = classify_technology(out["PP04D_COD"])
    out["sector_provisional"] = out["caes_code"].str[:2].map(SECTOR_BY_PREFIX)
    out["agglomerate"] = normalize_code(out["AGLOMERADO"], 2)
    out["gran_rosario"] = out["agglomerate"].eq("04")
    return out


def weighted_count(frame: pd.DataFrame) -> tuple[int, float]:
    weight = frame["weight_person"]
    return len(frame), float(weight.sum(min_count=1)) if weight.notna().any() else 0.0


def quality_row(frame: pd.DataFrame, quarter: str) -> dict:
    universe = frame["occupied_15plus"]
    both = frame["both_classifications_valid"]
    valid_weight = frame["weight_person"].notna() & frame["weight_person"].gt(0)
    row = {
        "quarter": quarter, "records_total": len(frame), "occupied": int(frame["occupied"].sum()),
        "occupied_15plus": int(universe.sum()),
        "pp04d_valid_occupied_15plus": int((universe & frame["cno_valid"]).sum()),
        "pp04b_valid_occupied_15plus": int((universe & frame["caes_valid"]).sum()),
        "both_valid_occupied_15plus": int(both.sum()), "pondera_valid_positive": int(valid_weight.sum()),
        "weighted_total_all": float(frame.loc[valid_weight, "weight_person"].sum()),
        "weighted_occupied_15plus": float(frame.loc[universe & valid_weight, "weight_person"].sum()),
        "weighted_analytical": float(frame.loc[both & valid_weight, "weight_person"].sum()),
        "age_missing_total": int(frame["age"].isna().sum()),
        "age_outside_0_110_total": int((frame["age"].notna() & ~frame["age"].between(0, 110)).sum()),
        "age_outside_0_110_occupied_15plus": int((universe & ~frame["age"].between(0, 110)).sum()),
        "caes_missing_or_invalid_occupied_15plus": int((universe & ~frame["caes_valid"]).sum()),
        "cno_missing_or_invalid_occupied_15plus": int((universe & ~frame["cno_valid"]).sum()),
        "gran_rosario_records": int(frame["gran_rosario"].sum()),
        "gran_rosario_analytical": int((frame["gran_rosario"] & both).sum()),
    }
    return row


def table(frame: pd.DataFrame, dimensions: list[str]) -> pd.DataFrame:
    work = frame[frame["both_classifications_valid"]].copy()
    work["_one"] = 1
    grouped = work.groupby(dimensions, dropna=False, observed=False).agg(
        unweighted=("_one", "sum"), weighted=("weight_person", "sum")
    ).reset_index()
    return grouped


def repeats(frames: list[pd.DataFrame]) -> tuple[pd.DataFrame, pd.DataFrame]:
    combined = pd.concat([f[["source_quarter", "household_id", "person_candidate_id"]] for f in frames], ignore_index=True)
    household = combined.groupby("household_id", dropna=False).agg(
        quarters=("source_quarter", "nunique"), rows=("source_quarter", "size"),
        quarter_list=("source_quarter", lambda x: "|".join(sorted(set(x))))
    ).reset_index()
    person = combined.groupby("person_candidate_id", dropna=False).agg(
        quarters=("source_quarter", "nunique"), rows=("source_quarter", "size"),
        quarter_list=("source_quarter", lambda x: "|".join(sorted(set(x))))
    ).reset_index()
    for result in (household, person):
        result["potentially_repeated"] = result["quarters"].gt(1)
    return household, person


def main() -> None:
    REPORT.mkdir(parents=True, exist_ok=True)
    PROCESSED.mkdir(parents=True, exist_ok=True)
    print("checkpoint: manifest", flush=True)
    manifest = source_manifest()
    frames: list[pd.DataFrame] = []
    quality: list[dict] = []
    age_rows = []
    code_rows = []
    for quarter, path in SOURCES.items():
        print(f"checkpoint: reading {quarter}", flush=True)
        with zipfile.ZipFile(path) as archive:
            individual = member_name(archive, "usu_individual")
            household = member_name(archive, "usu_hogar")
            frame = harmonize(read_member(archive, individual, INDIVIDUAL_REQUIRED), quarter)
            print(f"checkpoint: individual {quarter} rows={len(frame)}", flush=True)
            household_frame = read_member(archive, household, HOUSEHOLD_REQUIRED)
            print(f"checkpoint: household {quarter} rows={len(household_frame)}", flush=True)
        frames.append(frame)
        quality.append(quality_row(frame, quarter))
        outliers = frame[frame["age"].notna() & ~frame["age"].between(0, 110)]
        for age, count in outliers["age"].value_counts().sort_index().items():
            age_rows.append({"quarter": quarter, "age_value": age, "frequency": int(count), "occupied_15plus": int((outliers["age"].eq(age) & outliers["occupied_15plus"]).sum())})
        valid_caes = frame[frame["occupied"] & frame["caes_valid"]]
        observed = valid_caes["caes_code"].value_counts().sort_index()
        for code, count in observed.items():
            prefix = str(code)[:2]
            code_rows.append({"quarter": quarter, "caes_code": code, "prefix": prefix, "sector_provisional": SECTOR_BY_PREFIX.get(prefix), "records": int(count)})
        for dims, name in [
            (["source_quarter", "sex"], "quarter_by_sex"),
            (["source_quarter", "technology_category"], "quarter_by_technology"),
            (["source_quarter", "sector_provisional", "sex"], "sector_by_sex"),
            (["source_quarter", "sector_provisional", "technology_category"], "sector_by_technology"),
            (["source_quarter", "sector_provisional", "sex", "technology_category"], "sector_by_sex_technology"),
            (["source_quarter", "sector_provisional", "education"], "sector_by_education"),
            (["source_quarter", "sector_provisional"], "sector_by_quarter"),
        ]:
            table(frame, dims).to_csv(REPORT / f"{name}.csv", index=False)
        household_frame["household_weight_valid"] = numeric(household_frame["PONDERA"]).gt(0)
        household_frame.to_csv(REPORT / f"{quarter}_household_quality_sample.csv", index=False)
    harmonized = pd.concat(frames, ignore_index=True)
    print("checkpoint: writing outputs", flush=True)
    harmonized.to_csv(PROCESSED / "eph_harmonized_2025T2_2026T1.csv", index=False)
    pd.DataFrame(quality).to_csv(REPORT / "quality_by_quarter.csv", index=False)
    pd.DataFrame(quality).to_json(REPORT / "quality_by_quarter.json", orient="records", force_ascii=False, indent=2)
    pd.DataFrame(age_rows).to_csv(REPORT / "age_outliers_by_value.csv", index=False)
    pd.DataFrame(code_rows).to_csv(REPORT / "caes_code_coverage.csv", index=False)
    household, person = repeats(frames)
    household.to_csv(REPORT / "repeated_households.csv", index=False)
    person.to_csv(REPORT / "repeated_person_candidates.csv", index=False)
    repeated_summary = pd.DataFrame([
        {"unit": "household", "unique_keys": len(household), "keys_in_2plus_quarters": int(household["potentially_repeated"].sum()), "rows_in_repeated_keys": int(household.loc[household["potentially_repeated"], "rows"].sum())},
        {"unit": "person_candidate", "unique_keys": len(person), "keys_in_2plus_quarters": int(person["potentially_repeated"].sum()), "rows_in_repeated_keys": int(person.loc[person["potentially_repeated"], "rows"].sum())},
    ])
    repeated_summary.to_csv(REPORT / "repetition_summary.csv", index=False)
    with open(REPORT / "age_outliers_t425.csv", "w", encoding="utf-8", newline="") as stream:
        pd.DataFrame(age_rows).query("quarter == '2025-T4'").to_csv(stream, index=False)
    summary = {
        "analytical_rows_total": int(harmonized["both_classifications_valid"].sum()),
        "analytical_weighted_total_by_quarter": {k: float(v) for k, v in harmonized[harmonized["both_classifications_valid"]].groupby("source_quarter")["weight_person"].sum().items()},
        "all_observed_caes_codes": int(pd.DataFrame(code_rows)["caes_code"].nunique()),
        "unmapped_caes_codes": sorted(pd.DataFrame(code_rows).loc[pd.DataFrame(code_rows)["sector_provisional"].isna(), "caes_code"].unique().tolist()),
    }
    (REPORT / "analytical_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"report_dir": str(REPORT), "processed_file": str(PROCESSED / "eph_harmonized_2025T2_2026T1.csv"), "quality": quality, "summary": summary}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
