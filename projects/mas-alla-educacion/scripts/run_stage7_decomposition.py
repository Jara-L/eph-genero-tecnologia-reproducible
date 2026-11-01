from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


ROOT = Path(__file__).resolve().parents[3]
INPUT = ROOT / "data" / "processed" / "eph_harmonized_2025T2_2026T1.csv"
REPORT = ROOT / "reports" / "generated" / "stage7_decomposition"
TECH = {"2": "Operación de máquinas", "3": "Operación de sistemas informatizados"}


def load_data() -> pd.DataFrame:
    dtype = {"source_quarter": "string", "cno_code": "string", "caes_code": "string", "sex": "string", "education": "string"}
    frame = pd.read_csv(INPUT, dtype=dtype, low_memory=False)
    frame["weight_person"] = pd.to_numeric(frame["weight_person"], errors="coerce")
    frame["age"] = pd.to_numeric(frame["age"], errors="coerce")
    frame["cno_digit"] = frame["cno_code"].str[3]
    frame["technology_category_clean"] = frame["cno_digit"].map({"1": "No tecnológica", **TECH})
    frame["technology_valid_strict"] = frame["technology_category_clean"].notna()
    frame["sector_assigned"] = frame["sector_provisional"].notna()
    frame["occupied15"] = frame["occupied"].astype(bool) & frame["age"].gt(14)
    frame["wide_universe"] = frame["occupied15"] & frame["cno_valid"].astype(bool) & frame["caes_valid"].astype(bool)
    frame["final_analytic"] = frame["wide_universe"] & frame["technology_valid_strict"] & frame["sector_assigned"]
    frame["weight_pooled"] = frame["weight_person"] / 4
    frame["macro_sector"] = frame["caes_code"].str[:2].map(macro_sector)
    return frame


def macro_sector(prefix: str) -> str | None:
    if not isinstance(prefix, str):
        return None
    n = int(prefix) if prefix.isdigit() else -1
    if 1 <= n <= 9:
        return "Primario y minería"
    if 10 <= n <= 33:
        return "Industria manufacturera"
    if 35 <= n <= 40:
        return "Energía, agua y construcción"
    if n in {45, 48}:
        return "Comercio"
    if 49 <= n <= 53:
        return "Transporte y almacenamiento"
    if 55 <= n <= 56:
        return "Hotelería y comidas"
    if 58 <= n <= 75:
        return "Información, finanzas y profesionales"
    if 77 <= n <= 82:
        return "Administración y apoyo"
    if 84 <= n <= 85:
        return "Sector público y educación"
    if 86 <= n <= 88:
        return "Salud y servicios sociales"
    if 90 <= n <= 99:
        return "Otros servicios y hogares"
    return None


def save(frame: pd.DataFrame, name: str) -> None:
    frame.to_csv(REPORT / name, index=False)


def universe_audit(frame: pd.DataFrame) -> dict:
    masks = [
        ("Registros originales", pd.Series(True, index=frame.index)),
        ("Personas ocupadas", frame["occupied"].astype(bool)),
        ("Ocupadas de 15 años y más", frame["occupied15"]),
        ("CNO válido", frame["occupied15"] & frame["cno_valid"].astype(bool)),
        ("CAES válido; universo amplio", frame["wide_universe"]),
        ("Tecnología estricta válida", frame["wide_universe"] & frame["technology_valid_strict"]),
        ("Sector asignado; universo estricto", frame["final_analytic"]),
    ]
    rows = []
    previous = len(frame)
    for label, mask in masks:
        current = int(mask.sum())
        rows.append({"step": label, "records": current, "excluded_from_previous_step": previous - current, "denominator_previous_step": previous, "percent_retained_previous_step": current / previous * 100 if previous else None})
        previous = current
    result = pd.DataFrame(rows)
    save(result, "universe_filter_sequence.csv")
    return {"wide_rows": int(frame["wide_universe"].sum()), "strict_rows": int(frame["final_analytic"].sum()), "sequence": rows}


def validate_table_denominators() -> pd.DataFrame:
    checks = []
    specifications = [
        ("tabla_1_sector_sexo.csv", ["sector_provisional"]),
        ("tabla_2_sector_tecnologia.csv", ["sector_provisional"]),
        ("tabla_3_sector_sexo_tecnologia.csv", ["sector_provisional", "sex"]),
        ("tabla_4_educacion_sexo_tecnologia.csv", ["sex", "technology_category"]),
        ("tabla_5_trimestre_sector_tecnologia.csv", ["source_quarter"]),
        ("tabla_5_trimestre_tecnologia.csv", ["source_quarter"]),
    ]
    for filename, denominators in specifications:
        table = pd.read_csv(ROOT / "reports" / "generated" / "stage6_results" / filename)
        sums = table.groupby(denominators, dropna=False)["weighted_percent"].sum()
        checks.append({"table": filename, "denominator": " × ".join(denominators), "groups": len(sums), "max_abs_deviation_from_100_pp": float((sums - 100).abs().max()), "all_groups_close": bool((sums - 100).abs().max() < 1e-8)})
    result = pd.DataFrame(checks)
    save(result, "denominator_checks.csv")
    return result


def repeated_analytical(frame: pd.DataFrame) -> pd.DataFrame:
    analytic = frame[frame["final_analytic"]].copy()
    results = []
    for unit in ["household_id", "person_candidate_id"]:
        grouped = analytic.groupby(unit).agg(quarters=("source_quarter", "nunique"), records=("source_quarter", "size")).reset_index()
        dist = grouped.groupby("quarters").agg(unique_identifiers=(unit, "size"), records=("records", "sum")).reset_index()
        dist.insert(0, "unit", unit)
        results.append(dist)
    result = pd.concat(results, ignore_index=True)
    save(result, "repetition_distribution_analytical.csv")
    return result


def decomposition(data: pd.DataFrame, sector_col: str, period_label: str) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    work = data[data["final_analytic"] & data[sector_col].notna()].copy()
    work["_w"] = work["weight_pooled"]
    # Keep only positive-support female/male sector cells. No rate is imputed.
    support = work.groupby([sector_col, "sex"], dropna=False).agg(unweighted=("sex", "size"), weighted=("_w", "sum")).reset_index()
    support["small_unweighted_lt30"] = support["unweighted"] < 30
    save(support.assign(period=period_label), f"support_{period_label}_{sector_col}.csv")
    sectors = sorted(set(support.loc[support["sex"].isin(["1", "2"]), sector_col].dropna()))
    valid_sectors = [s for s in sectors if set(support.loc[support[sector_col].eq(s), "sex"]) >= {"1", "2"}]
    rows = []
    outcomes = {"systems": "3", "machines": "2"}
    aggregate = []
    for outcome, digit in outcomes.items():
        tab = work[work[sector_col].isin(valid_sectors)].copy()
        totals = tab.groupby("sex")["_w"].sum()
        sector_totals = tab.groupby([sector_col, "sex"])["_w"].sum().unstack(fill_value=0)
        sector_outcomes = tab[tab["cno_digit"].eq(digit)].groupby([sector_col, "sex"])["_w"].sum().unstack(fill_value=0)
        q_m = sector_totals.get("1", pd.Series(dtype=float)) / totals.get("1", 1)
        q_f = sector_totals.get("2", pd.Series(dtype=float)) / totals.get("2", 1)
        p_m = sector_outcomes.get("1", pd.Series(dtype=float)) / sector_totals.get("1", 1)
        p_f = sector_outcomes.get("2", pd.Series(dtype=float)) / sector_totals.get("2", 1)
        component = pd.DataFrame({"sector": valid_sectors})
        component["q_men"] = component["sector"].map(q_m).fillna(0)
        component["q_women"] = component["sector"].map(q_f).fillna(0)
        component["p_men"] = component["sector"].map(p_m).fillna(0)
        component["p_women"] = component["sector"].map(p_f).fillna(0)
        component["intersectorial_pp"] = 0.5 * (component["q_women"] - component["q_men"]) * (component["p_women"] + component["p_men"]) * 100
        component["intrasectorial_pp"] = 0.5 * (component["p_women"] - component["p_men"]) * (component["q_women"] + component["q_men"]) * 100
        component["outcome"] = outcome
        component["period"] = period_label
        rows.append(component)
        p_women = float((component["q_women"] * component["p_women"]).sum())
        p_men = float((component["q_men"] * component["p_men"]).sum())
        inter = float(component["intersectorial_pp"].sum())
        intra = float(component["intrasectorial_pp"].sum())
        aggregate.append({"period": period_label, "outcome": outcome, "women_rate": p_women * 100, "men_rate": p_men * 100, "aggregate_gap_pp": (p_women - p_men) * 100, "intersectorial_pp": inter, "intrasectorial_pp": intra, "reconstructed_gap_pp": inter + intra, "identity_error_pp": (p_women - p_men) * 100 - inter - intra, "sectors_used": len(valid_sectors), "sectors_excluded_no_both_sexes": len(sectors) - len(valid_sectors)})
    contributions = pd.concat(rows, ignore_index=True)
    save(contributions, f"sector_contributions_{period_label}_{sector_col}.csv")
    return contributions, pd.DataFrame(aggregate), {"valid_sectors": valid_sectors, "support": support}


def make_plots(aggregate: pd.DataFrame, contributions: pd.DataFrame) -> list[str]:
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "axes.titlesize": 12})
    paths = []
    pooled = aggregate[aggregate["period"].eq("pooled_4q")]
    fig, ax = plt.subplots(figsize=(7, 5), facecolor="white")
    x = range(len(pooled))
    ax.bar([i - 0.18 for i in x], pooled["intersectorial_pp"], width=0.36, color="#0b3c5d", label="Intersectorial")
    ax.bar([i + 0.18 for i in x], pooled["intrasectorial_pp"], width=0.36, color="#4f9bc7", label="Intrasectorial")
    ax.axhline(0, color="#444444", linewidth=0.8)
    ax.set_xticks(list(x), ["Sistemas", "Máquinas"])
    ax.set_ylabel("Puntos porcentuales")
    ax.set_title("Descomposición simétrica de la brecha tecnológica")
    ax.legend(frameon=False)
    fig.tight_layout()
    path = REPORT / "figura_1_componentes_kitagawa.png"
    fig.savefig(path, dpi=220, facecolor="white")
    plt.close(fig)
    paths.append(path.name)

    systems = contributions[(contributions["period"] == "pooled_4q") & (contributions["outcome"] == "systems")].sort_values("intersectorial_pp")
    machines = contributions[(contributions["period"] == "pooled_4q") & (contributions["outcome"] == "machines")].sort_values("intersectorial_pp")
    fig, axes = plt.subplots(1, 2, figsize=(12, 7), sharey=True, facecolor="white")
    for ax, sub, title in [(axes[0], systems, "Sistemas informatizados"), (axes[1], machines, "Operación de máquinas")]:
        ax.barh(sub["sector"], sub["intersectorial_pp"], color="#0b3c5d", alpha=0.9, label="Intersectorial")
        ax.barh(sub["sector"], sub["intrasectorial_pp"], color="#4f9bc7", alpha=0.75, label="Intrasectorial")
        ax.axvline(0, color="#444444", linewidth=0.8)
        ax.set_title(title)
        ax.set_xlabel("Puntos porcentuales")
    axes[0].set_ylabel("Sector")
    axes[0].legend(frameon=False, loc="lower right")
    fig.suptitle("Contribuciones sectoriales a la brecha", y=1.01)
    fig.tight_layout()
    path = REPORT / "figura_2_contribuciones_sectoriales.png"
    fig.savefig(path, dpi=220, facecolor="white", bbox_inches="tight")
    plt.close(fig)
    paths.append(path.name)
    return paths


def main() -> None:
    REPORT.mkdir(parents=True, exist_ok=True)
    frame = load_data()
    audit = universe_audit(frame)
    checks = validate_table_denominators()
    repeats = repeated_analytical(frame)
    all_contrib, all_aggregate, _ = decomposition(frame, "sector_provisional", "pooled_4q")
    t1 = frame[frame["source_quarter"].eq("2026-T1")].copy()
    _, t1_aggregate, _ = decomposition(t1, "sector_provisional", "2026_T1")
    _, macro_aggregate, _ = decomposition(frame, "macro_sector", "pooled_4q_macro")
    aggregate = pd.concat([all_aggregate, t1_aggregate, macro_aggregate], ignore_index=True)
    save(aggregate, "decomposition_summary.csv")
    zero = frame[frame["occupied15"] & frame["caes_valid"].astype(bool) & frame["caes_code"].str.startswith("00")]
    zero_report = zero.groupby(["caes_code", "source_quarter"]).agg(unweighted=("caes_code", "size"), weighted=("weight_person", "sum")).reset_index()
    save(zero_report, "caes_00xx_incidence_stage7.csv")
    plots = make_plots(aggregate, all_contrib)
    summary = {"universe": audit, "denominator_checks_all_pass": bool(checks["all_groups_close"].all()), "analytical_repetition_rows": int(repeats.loc[repeats["unit"].eq("person_candidate_id"), "records"].sum()), "zero_codes": sorted(zero["caes_code"].dropna().unique().tolist()), "plots": plots}
    (REPORT / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    report = f"""# Etapa 7 — descomposición de brechas tecnológicas\n\nLa auditoría reproduce {audit['wide_rows']:,} registros del universo amplio y {audit['strict_rows']:,} del universo estricto. La secuencia completa está en `universe_filter_sequence.csv`.\n\nLa descomposición simétrica usa `PONDERA/4` en la ventana agrupada y calcula, para cada resultado, la brecha mujeres − varones como suma exacta de componentes intersectorial e intrasectorial. La identidad se valida en `decomposition_summary.csv`; el error máximo debe ser numérico.\n\nLos 64.030 identificadores candidatos repetidos y 128.060 registros de Etapa 6 corresponden a la EPH completa. Para la muestra analítica estricta, la distribución está en `repetition_distribution_analytical.csv`.\n\nLos 13 códigos `00xx` se auditan en `caes_00xx_incidence_stage7.csv`, sin imputar sectores.\n\n## Sensibilidad\n\nSe estimaron descriptivamente las versiones agrupadas 2025-T2–2026-T1, sólo 2026-T1 y agrupada con macrosectores. No se estimaron intervalos ingenuos: la inferencia recomendada requiere errores agrupados por vivienda, controles por trimestre y sensibilidad a la rotación.\n\n## Interpretación\n\nEl componente intersectorial resume cuánto cambiaría la brecha si mujeres y varones conservaran sus tasas sectoriales pero compartieran distribuciones sectoriales; el componente intrasectorial resume diferencias tecnológicas dentro de sectores bajo la distribución sectorial simétrica. No son efectos causales.\n\n## Modelos pendientes\n\nSe preparan modelos multinomiales base, con sector e interacciones sexo × sector. La comparación principal deberá usar probabilidades marginales estandarizadas y brechas predichas, no comparar mecánicamente coeficientes entre modelos por no colapsabilidad. No se ejecutaron estimaciones definitivas.\n\nPruebas específicas de identidad, denominadores, orden sectorial y ponderación acompañan el código en `tests/`.\n"""
    (REPORT / "informe_etapa7.md").write_text(report, encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
