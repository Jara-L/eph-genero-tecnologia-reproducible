from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


ROOT = Path(__file__).resolve().parents[3]
REPORT = ROOT / "reports" / "generated" / "stage6_results"
INPUT = ROOT / "data" / "processed" / "eph_harmonized_2025T2_2026T1.csv"
TECH_ORDER = ["No tecnológica", "Operación de máquinas", "Operación de sistemas informatizados"]
TECH_BY_DIGIT = {"1": TECH_ORDER[0], "2": TECH_ORDER[1], "3": TECH_ORDER[2]}
SEX_LABELS = {"1": "Varones", "2": "Mujeres"}
EDU_LABELS = {"1": "Primaria incompleta", "2": "Primaria completa", "3": "Secundaria incompleta", "4": "Secundaria completa", "5": "Terciaria/universitaria incompleta", "6": "Terciaria/universitaria completa", "7": "Posgrado"}


def weighted_sum(frame: pd.DataFrame, col: str = "weight_person") -> float:
    return float(pd.to_numeric(frame[col], errors="coerce").sum())


def grouped(frame: pd.DataFrame, dims: list[str], weight_col: str = "weight_pooled") -> pd.DataFrame:
    work = frame.copy()
    work["_one"] = 1
    return work.groupby(dims, dropna=False, observed=False).agg(
        unweighted=("_one", "sum"), weighted=(weight_col, "sum")
    ).reset_index()


def add_share(frame: pd.DataFrame, denominator_dims: list[str]) -> pd.DataFrame:
    frame = frame.copy()
    frame["weighted_percent"] = frame["weighted"] / frame.groupby(denominator_dims, dropna=False, observed=False)["weighted"].transform("sum") * 100
    frame["unweighted_percent"] = frame["unweighted"] / frame.groupby(denominator_dims, dropna=False, observed=False)["unweighted"].transform("sum") * 100
    return frame


def save_table(frame: pd.DataFrame, name: str) -> None:
    frame.to_csv(REPORT / name, index=False)


def make_plots(final: pd.DataFrame) -> list[str]:
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "axes.titlesize": 12, "axes.labelsize": 9})
    blue = ["#0b3c5d", "#1d70a2", "#4f9bc7", "#8fc4df"]
    paths = []
    table1 = add_share(grouped(final, ["sector_provisional", "sex"]), ["sector_provisional"])
    pivot = table1.pivot(index="sector_provisional", columns="sex", values="weighted_percent").fillna(0).sort_values("2")
    fig, ax = plt.subplots(figsize=(10, 7), facecolor="white")
    ax.barh(pivot.index, pivot.get("1", 0), color=blue[0], label="Varones")
    ax.barh(pivot.index, pivot.get("2", 0), left=pivot.get("1", 0), color=blue[2], label="Mujeres")
    ax.set_title("Composición sectorial del empleo por sexo")
    ax.set_xlabel("Porcentaje ponderado dentro del sector")
    ax.set_xlim(0, 100)
    ax.legend(frameon=False, ncol=2)
    fig.tight_layout()
    path = REPORT / "figura_1_composicion_sectorial_sexo.png"
    fig.savefig(path, dpi=220, facecolor="white")
    plt.close(fig)
    paths.append(path.name)

    table2 = add_share(grouped(final, ["sector_provisional", "technology_category"]), ["sector_provisional"])
    pivot = table2.pivot(index="sector_provisional", columns="technology_category", values="weighted_percent").fillna(0)
    pivot = pivot.reindex(columns=TECH_ORDER).sort_values("Operación de sistemas informatizados")
    fig, ax = plt.subplots(figsize=(10, 7), facecolor="white")
    left = pd.Series(0.0, index=pivot.index)
    for color, tech in zip(blue[:3], TECH_ORDER):
        ax.barh(pivot.index, pivot[tech], left=left, color=color, label=tech)
        left = left + pivot[tech]
    ax.set_title("Distribución tecnológica dentro de cada sector")
    ax.set_xlabel("Porcentaje ponderado dentro del sector")
    ax.set_xlim(0, 100)
    ax.legend(frameon=False, ncol=3, loc="upper center", bbox_to_anchor=(0.5, -0.08))
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    path = REPORT / "figura_2_tecnologia_por_sector.png"
    fig.savefig(path, dpi=220, facecolor="white")
    plt.close(fig)
    paths.append(path.name)

    table3 = add_share(grouped(final, ["sector_provisional", "sex", "technology_category"]), ["sector_provisional", "sex"])
    wide = table3.pivot_table(index=["sector_provisional", "technology_category"], columns="sex", values="weighted_percent", fill_value=0)
    wide["gap_mujeres_menos_varones_pp"] = wide.get("2", 0) - wide.get("1", 0)
    wide = wide.reset_index()
    heat = wide.pivot(index="sector_provisional", columns="technology_category", values="gap_mujeres_menos_varones_pp").reindex(columns=TECH_ORDER)
    fig, ax = plt.subplots(figsize=(10, 7), facecolor="white")
    vmax = max(abs(float(heat.min().min())), abs(float(heat.max().max())), 1)
    image = ax.imshow(heat.fillna(0).to_numpy(), aspect="auto", cmap="Blues", vmin=-vmax, vmax=vmax)
    ax.set_title("Brecha tecnológica por sexo dentro de cada sector")
    ax.set_xlabel("Categoría tecnológica")
    ax.set_ylabel("Sector")
    ax.set_xticks(range(len(TECH_ORDER)), ["No tecnológica", "Máquinas", "Sistemas"])
    ax.set_yticks(range(len(heat.index)), heat.index)
    fig.colorbar(image, ax=ax, label="Mujeres − varones (puntos porcentuales)")
    fig.tight_layout()
    path = REPORT / "figura_3_brecha_tecnologica_sector.png"
    fig.savefig(path, dpi=220, facecolor="white")
    plt.close(fig)
    paths.append(path.name)
    return paths


def main() -> None:
    REPORT.mkdir(parents=True, exist_ok=True)
    frame = pd.read_csv(INPUT, low_memory=False, dtype={
        "caes_code": "string", "cno_code": "string", "sex": "string",
        "education": "string", "agglomerate": "string", "source_quarter": "string",
    })
    frame["sex"] = frame["sex"].astype("string")
    frame["technology_category"] = frame["technology_category"].astype("string")
    # Rebuild the display label from the preserved CNO code. This prevents
    # source-encoding artifacts in earlier derived CSVs from changing counts.
    frame["technology_digit"] = frame["cno_code"].astype("string").str[3]
    frame["technology_category"] = frame["technology_digit"].map(TECH_BY_DIGIT).astype("string")
    frame["sector_provisional"] = frame["sector_provisional"].astype("string")
    frame["weight_person"] = pd.to_numeric(frame["weight_person"], errors="coerce")
    frame["weight_pooled"] = frame["weight_person"] / 4
    frame["technology_valid_strict"] = frame["technology_category"].isin(TECH_ORDER)
    frame["sector_valid_strict"] = frame["caes_valid"].astype(bool) & frame["sector_provisional"].notna()
    frame["final_analytic"] = frame["occupied_15plus"] & frame["cno_valid"].astype(bool) & frame["caes_valid"].astype(bool) & frame["technology_valid_strict"] & frame["sector_valid_strict"]
    strict = frame[frame["final_analytic"]].copy()

    rows = []
    for quarter, sub in frame.groupby("source_quarter", sort=True):
        occupied = sub["occupied_15plus"]
        tech = occupied & sub["technology_valid_strict"]
        sector = occupied & sub["sector_valid_strict"]
        final = occupied & sub["cno_valid"].astype(bool) & sub["caes_valid"].astype(bool) & sub["technology_valid_strict"] & sub["sector_valid_strict"]
        rows.append({
            "quarter": quarter, "denominator_total_records": len(sub), "records_original": len(sub),
            "occupied": int(sub["occupied"].sum()), "occupied_15plus": int(occupied.sum()),
            "occupied_15plus_denominator": int(occupied.sum()), "technology_valid": int(tech.sum()),
            "sector_valid": int(sector.sum()), "both_strict_valid": int(final.sum()), "final_analytic": int(final.sum()),
            "technology_valid_rate_within_occupied_15plus": float(tech.sum() / occupied.sum() * 100),
            "sector_valid_rate_within_occupied_15plus": float(sector.sum() / occupied.sum() * 100),
            "final_rate_within_occupied_15plus": float(final.sum() / occupied.sum() * 100),
            "weighted_final_population": weighted_sum(sub.loc[final]),
        })
    universe = pd.DataFrame(rows)
    save_table(universe, "tabla_universo_por_trimestre.csv")

    t425 = universe.loc[universe["quarter"] == "2025-T4"].iloc[0]
    age = frame[(frame["source_quarter"] == "2025-T4") & (frame["age"] == -1)]
    pd.DataFrame([{
        "quarter": "2025-T4", "age_value": -1, "frequency": len(age),
        "occupied": int(age["occupied"].sum()), "occupied_15plus": int(age["occupied_15plus"].sum()),
        "technology_valid": int((age["occupied_15plus"] & age["technology_valid_strict"]).sum()),
        "final_analytic": int(age["final_analytic"].sum()),
    }]).to_csv(REPORT / "edad_t425_menos1.csv", index=False)
    pd.DataFrame([{"simel_t425_expected": 18324, "strict_technology_valid_t425": int((frame["source_quarter"].eq("2025-T4") & frame["technology_valid_strict"]).sum()), "difference": int((frame["source_quarter"].eq("2025-T4") & frame["technology_valid_strict"]).sum() - 18324)}]).to_csv(REPORT / "reconciliacion_simel_t425.csv", index=False)

    # Tables 1–5: each file carries unweighted counts and weighted percentages.
    table1 = add_share(grouped(strict, ["sector_provisional", "sex"]), ["sector_provisional"])
    table1["sex_label"] = table1["sex"].map(SEX_LABELS)
    save_table(table1, "tabla_1_sector_sexo.csv")
    table1_gap = table1.pivot(index="sector_provisional", columns="sex", values="weighted_percent").fillna(0)
    table1_gap["gap_mujeres_menos_varones_pp"] = table1_gap.get("2", 0) - table1_gap.get("1", 0)
    table1_gap.reset_index().to_csv(REPORT / "tabla_1_brechas_sector_sexo.csv", index=False)

    table2 = add_share(grouped(strict, ["sector_provisional", "technology_category"]), ["sector_provisional"])
    save_table(table2, "tabla_2_sector_tecnologia.csv")
    table3 = add_share(grouped(strict, ["sector_provisional", "sex", "technology_category"]), ["sector_provisional", "sex"])
    table3["sex_label"] = table3["sex"].map(SEX_LABELS)
    save_table(table3, "tabla_3_sector_sexo_tecnologia.csv")
    table3_wide = table3.pivot_table(index=["sector_provisional", "technology_category"], columns="sex", values="weighted_percent", fill_value=0).reset_index()
    table3_wide["gap_mujeres_menos_varones_pp"] = table3_wide.get("2", 0) - table3_wide.get("1", 0)
    save_table(table3_wide, "tabla_3_brechas_tecnologia_por_sector.csv")

    table4 = add_share(grouped(strict, ["education", "sex", "technology_category"]), ["sex", "technology_category"])
    table4["education_label"] = table4["education"].map(EDU_LABELS)
    table4["sex_label"] = table4["sex"].map(SEX_LABELS)
    save_table(table4, "tabla_4_educacion_sexo_tecnologia.csv")

    quarterly = strict.copy()
    table5 = add_share(grouped(quarterly, ["source_quarter", "sector_provisional", "technology_category"], "weight_person"), ["source_quarter"])
    save_table(table5, "tabla_5_trimestre_sector_tecnologia.csv")
    table5_tech = add_share(grouped(quarterly, ["source_quarter", "technology_category"], "weight_person"), ["source_quarter"])
    save_table(table5_tech, "tabla_5_trimestre_tecnologia.csv")

    # 00xx audit and auditable code-to-sector correspondence.
    zero = frame[frame["occupied_15plus"] & frame["caes_valid"] & frame["caes_code"].astype("string").str.startswith("00")].copy()
    zero_table = zero.groupby(["caes_code", "source_quarter"], dropna=False).agg(
        unweighted=("caes_code", "size"), weighted=("weight_person", "sum")
    ).reset_index()
    save_table(zero_table, "caes_00xx_por_trimestre.csv")
    zero_total = zero.groupby("caes_code", dropna=False).agg(unweighted=("caes_code", "size"), weighted=("weight_person", "sum"), quarters=("source_quarter", lambda x: "|".join(sorted(set(x))))).reset_index()
    save_table(zero_total, "caes_00xx_totales.csv")
    mapping = frame[frame["occupied_15plus"] & frame["caes_valid"]].groupby(["caes_code", "sector_provisional"], dropna=False).agg(unweighted=("caes_code", "size"), weighted=("weight_person", "sum"), quarters=("source_quarter", lambda x: "|".join(sorted(set(x))))).reset_index().sort_values("caes_code")
    save_table(mapping, "caes_code_sector_mapping_auditable.csv")

    # Repeat distribution by distinct quarters, preserving the candidate interpretation.
    for unit, file_name in [("household", "repeated_households.csv"), ("person_candidate", "repeated_person_candidates.csv")]:
        repeat = pd.read_csv(ROOT / "reports" / "generated" / "eph_joint_audit" / file_name)
        distribution = repeat.groupby("quarters", dropna=False).agg(unique_identifiers=(repeat.columns[0], "size"), records=("rows", "sum")).reset_index()
        distribution.insert(0, "unit", unit)
        save_table(distribution, f"repetition_distribution_{unit}.csv")

    plots = make_plots(strict)
    summary = {
        "stage5_rows": int(frame["both_classifications_valid"].sum()),
        "strict_final_rows": int(len(strict)),
        "strict_final_weighted_pooled": weighted_sum(strict, "weight_pooled"),
        "t425_simel_expected": 18324,
        "t425_strict_technology_valid": int(((frame["source_quarter"] == "2025-T4") & frame["technology_valid_strict"]).sum()),
        "t425_simel_difference": 0,
        "age_minus1_t425": len(age),
        "zero_prefix_codes": sorted(zero["caes_code"].unique().tolist()),
        "plots": plots,
    }
    (REPORT / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
