"""Etapa 8: validacion, incertidumbre de Kitagawa y multinomial exploratorio.

Las salidas se escriben en reports/generated/stage8_inference (ignorado por Git).
El ajuste multinomial usa una log-verosimilitud ponderada explicita. No pretende
reemplazar un estimador de encuesta: los intervalos del bootstrap son por vivienda
y preservan las filas de los cuatro trimestres dentro de cada vivienda.
"""
from __future__ import annotations

import importlib.util
import json
import sys
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.optimize import minimize

ROOT = Path(__file__).resolve().parents[3]
INPUT = ROOT / "data" / "processed" / "eph_harmonized_2025T2_2026T1.csv"
REPORT = ROOT / "reports" / "generated" / "stage8_inference"
STAGE7 = ROOT / "projects" / "mas-alla-educacion" / "scripts" / "run_stage7_decomposition.py"
AUDIT = ROOT / "projects" / "mas-alla-educacion" / "scripts" / "run_joint_eph_audit.py"
SEED = 20261013
BOOT_REPS = 300

TECH = {"1": "No tecnológica", "2": "Operación de máquinas", "3": "Operación de sistemas informatizados"}


def load_frame() -> pd.DataFrame:
    d = pd.read_csv(INPUT, dtype={"source_quarter": "string", "cno_code": "string", "caes_code": "string", "sex": "string", "education": "string"}, low_memory=False)
    d["weight_person"] = pd.to_numeric(d["weight_person"], errors="coerce")
    d["age"] = pd.to_numeric(d["age"], errors="coerce")
    d["cno_code"] = d["cno_code"].astype("string").str.zfill(5)
    d["caes_code"] = d["caes_code"].astype("string").str.zfill(4)
    d["cno_digit"] = d["cno_code"].str[3]
    d["technology_category_clean"] = d["cno_digit"].map(TECH)
    d["occupied15"] = d["occupied"].astype(bool) & d["age"].gt(14)
    d["technology_valid_strict"] = d["technology_category_clean"].notna()
    d["wide_universe"] = d["occupied15"] & d["cno_valid"].astype(bool) & d["caes_valid"].astype(bool)
    d["final_analytic"] = d["wide_universe"] & d["technology_valid_strict"] & d["sector_provisional"].notna()
    d["weight_pooled"] = d["weight_person"] / 4.0
    d["macro_sector"] = d["caes_code"].str[:2].map(macro_sector)
    return d


def macro_sector(prefix: str | float) -> str | None:
    if not isinstance(prefix, str) or not prefix.isdigit():
        return None
    n = int(prefix)
    if 1 <= n <= 9: return "Primario y minería"
    if 10 <= n <= 33: return "Industria manufacturera"
    if 35 <= n <= 40: return "Energía, agua y construcción"
    if n in {45, 48}: return "Comercio"
    if 49 <= n <= 53: return "Transporte y almacenamiento"
    if 55 <= n <= 56: return "Hotelería y comidas"
    if 58 <= n <= 75: return "Información, finanzas y profesionales"
    if 77 <= n <= 82: return "Administración y apoyo"
    if 84 <= n <= 85: return "Sector público y educación"
    if 86 <= n <= 88: return "Salud y servicios sociales"
    if 90 <= n <= 99: return "Otros servicios y hogares"
    return None


def save(x: pd.DataFrame | dict, name: str) -> None:
    REPORT.mkdir(parents=True, exist_ok=True)
    if isinstance(x, pd.DataFrame): x.to_csv(REPORT / name, index=False)
    else: (REPORT / name).write_text(json.dumps(x, ensure_ascii=False, indent=2), encoding="utf-8")


def raw_reproduction() -> dict:
    """Read the four original ZIP members and reproduce the strict count/Kitagawa."""
    spec = importlib.util.spec_from_file_location("audit_module", AUDIT)
    mod = importlib.util.module_from_spec(spec); sys.modules[spec.name] = mod; spec.loader.exec_module(mod)
    raw_frames = []
    for q, path in mod.SOURCES.items():
        with zipfile.ZipFile(path) as z:
            name = mod.member_name(z, "usu_individual")
            raw_frames.append(mod.harmonize(mod.read_member(z, name, mod.INDIVIDUAL_REQUIRED), q))
    raw = pd.concat(raw_frames, ignore_index=True)
    raw["cno_code"] = raw["cno_code"].astype("string").str.zfill(5)
    raw["caes_code"] = raw["caes_code"].astype("string").str.zfill(4)
    raw["cno_digit"] = raw["cno_code"].str[3]
    raw["technology_valid_strict"] = raw["cno_digit"].isin(TECH)
    raw["occupied15"] = raw["occupied"].astype(bool) & raw["age"].gt(14)
    raw["wide_universe"] = raw["occupied15"] & raw["cno_valid"].fillna(False).astype(bool) & raw["caes_valid"].fillna(False).astype(bool)
    raw["final_analytic"] = raw["wide_universe"] & raw["technology_valid_strict"] & raw["sector_provisional"].notna()
    result = {"raw_rows": int(len(raw)), "raw_wide_rows": int(raw["wide_universe"].sum()), "raw_strict_rows": int(raw["final_analytic"].sum())}
    result["processed_strict_rows"] = int(load_frame()["final_analytic"].sum())
    result["strict_count_difference"] = result["raw_strict_rows"] - result["processed_strict_rows"]
    save(result, "raw_reproduction.json")
    return result


def universe_reconciliation(d: pd.DataFrame) -> pd.DataFrame:
    # The historical 74,221 count was the former sector-prefix universe:
    # corrected analytic rows plus 358 records with PP04B_COD=9999.
    masks = {
        "old_strict_74221": d["final_analytic"] | (d["occupied15"] & d["cno_valid"].astype(bool) & d["caes_code"].eq("9999") & d["technology_valid_strict"]),
        "technology_strict_74017": d["wide_universe"] & d["technology_valid_strict"],
        "sectorial_corrected_73863": d["final_analytic"],
    }
    rows = []
    for name, mask in masks.items(): rows.append({"set": name, "records": int(mask.sum())})
    old = masks["old_strict_74221"]
    corrected = masks["sectorial_corrected_73863"]
    excluded = d.loc[old & ~corrected].copy()
    rows += [{"set": "old_strict_minus_corrected", "records": int(len(excluded)), "all_caes_invalid_9999": bool((excluded["caes_code"] == "9999").all()), "all_technology_valid": bool(excluded["technology_valid_strict"].all())}]
    save(pd.DataFrame(rows), "universe_reconciliation.csv")
    save(excluded.groupby(["caes_code", "source_quarter"], dropna=False).size().rename("records").reset_index(), "universe_excluded_358_detail.csv")
    return pd.DataFrame(rows)


def repetitions(d: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for sample, x in [("full_eph", d), ("strict_analytic", d[d.final_analytic])]:
        for unit in ["household_id", "person_candidate_id"]:
            g = x.groupby(unit, dropna=False).agg(quarters=("source_quarter", "nunique"), records=("source_quarter", "size")).reset_index()
            dist = g.groupby("quarters", as_index=False).agg(unique_identifiers=(unit, "size"), records=("records", "sum"))
            dist.insert(0, "sample", sample); dist.insert(1, "unit", unit); rows.append(dist)
    result = pd.concat(rows, ignore_index=True); save(result, "repetition_distribution_full_and_analytic.csv"); return result


def kitagawa(x: pd.DataFrame, sector="sector_provisional") -> dict:
    x = x[x.final_analytic & x[sector].notna() & x.sex.isin(["1", "2"])].copy()
    x["_w"] = x.weight_pooled
    totals = x.groupby("sex")['_w'].sum()
    st = x.groupby([sector, "sex"])["_w"].sum().unstack(fill_value=0)
    valid = [s for s in st.index if all(k in st.columns and st.loc[s, k] > 0 for k in ["1", "2"])]
    st = st.loc[valid]
    rows = []
    for outcome, digit in [("systems", "3"), ("machines", "2")]:
        ot = x[x.cno_digit.eq(digit)].groupby([sector, "sex"])["_w"].sum().unstack(fill_value=0).reindex(valid, fill_value=0)
        qm, qf = st["1"] / totals["1"], st["2"] / totals["2"]
        pm, pf = ot["1"] / st["1"], ot["2"] / st["2"]
        gap = float((qf * pf).sum() - (qm * pm).sum())
        inter = float((0.5 * (pf + pm) * (qf - qm)).sum())
        # Symmetric within-sector term: sector distribution average times rate gap.
        intra = float((0.5 * (qf + qm) * (pf - pm)).sum())
        rows.append({"outcome": outcome, "gap_pp": 100 * gap, "intersectorial_pp": 100 * inter, "intrasectorial_pp": 100 * intra, "identity_error_pp": 100 * (gap - inter - intra), "sectors": len(valid)})
    return {"rows": rows, "valid_sectors": len(valid)}


def bootstrap(d: pd.DataFrame, reps=BOOT_REPS) -> pd.DataFrame:
    x = d[d.final_analytic & d.sector_provisional.notna() & d.sex.isin(["1", "2"])].copy()
    clusters = x.household_id.drop_duplicates().to_numpy(); rng = np.random.default_rng(SEED); outputs = []
    # Resampling households preserves all observed quarter rows within a household.
    for b in range(reps):
        sampled = rng.choice(clusters, size=len(clusters), replace=True)
        multiplicity = pd.Series(sampled).value_counts()
        boot = x.copy()
        boot["weight_pooled"] = boot["weight_pooled"] * boot["household_id"].map(multiplicity).fillna(0.0)
        boot = boot[boot["weight_pooled"] > 0]
        try:
            r = kitagawa(boot)
            for row in r["rows"]: outputs.append({"replicate": b, **row})
        except (KeyError, ZeroDivisionError, FloatingPointError):
            continue
    out = pd.DataFrame(outputs); save(out, "kitagawa_bootstrap_replicates.csv")
    rows = []
    for outcome, g in out.groupby("outcome"):
        for col in ["gap_pp", "intersectorial_pp", "intrasectorial_pp"]:
            a = g[col].dropna(); rows.append({"outcome": outcome, "statistic": col, "estimate": float(a.mean()), "ci95_low": float(a.quantile(.025)), "ci95_high": float(a.quantile(.975)), "replications": int(a.size), "failed_replications": reps - int(a.size)})
    result = pd.DataFrame(rows); save(result, "kitagawa_bootstrap_ci.csv"); return result


def estimands(d: pd.DataFrame) -> pd.DataFrame:
    x = d[d.final_analytic & d.sex.isin(["1", "2"])].copy(); x["technology_systems"] = x.cno_digit.eq("3"); x["technology_machines"] = x.cno_digit.eq("2")
    rows = []
    for sex, g in x.groupby("sex"):
        for outcome in ["systems", "machines"]:
            y = g["technology_" + outcome]; w = g.weight_person
            q = g.groupby("source_quarter").apply(lambda z: np.average(z["technology_" + outcome], weights=z.weight_person), include_groups=False)
            rows.append({"sex": sex, "outcome": outcome, "avg_quarterly_numerator": float((w*y).sum()/4), "avg_quarterly_denominator": float(w.sum()/4), "ratio_of_averages": float((w*y).sum()/w.sum()), "average_of_quarterly_percentages": float(q.mean()), "difference_pp": float(100*((w*y).sum()/w.sum()-q.mean()))})
    result = pd.DataFrame(rows); save(result, "estimand_sensitivity.csv"); return result


def design(d: pd.DataFrame, with_sector=False, interactions=False, category_spec=None):
    x = d[d.final_analytic & d.sex.isin(["1", "2"]) & d.education.notna() & d.macro_sector.notna()].copy()
    x["y"] = x.cno_digit.map({"1": 0, "2": 1, "3": 2}).astype(int); x["female"] = x.sex.eq("2").astype(int); x["age_c"] = (x.age - 40) / 10; x["age2"] = x.age_c**2
    cols = ["female", "age_c", "age2"]
    if category_spec is None:
        category_spec = {"education": sorted(x["education"].dropna().unique().tolist()), "quarter": sorted(x["source_quarter"].dropna().unique().tolist()), "sector": sorted(x["macro_sector"].dropna().unique().tolist())}
    edu = pd.Categorical(x["education"], categories=category_spec["education"])
    quarter = pd.Categorical(x["source_quarter"], categories=category_spec["quarter"])
    edu_dummies = pd.get_dummies(edu, prefix="edu", drop_first=True, dtype=float); edu_dummies.index = x.index
    quarter_dummies = pd.get_dummies(quarter, prefix="q", drop_first=True, dtype=float); quarter_dummies.index = x.index
    z = pd.concat([edu_dummies, quarter_dummies], axis=1)
    if with_sector:
        sector = pd.Categorical(x["macro_sector"], categories=category_spec["sector"])
        sector_dummies = pd.get_dummies(sector, prefix="sector", drop_first=True, dtype=float); sector_dummies.index = x.index
        z = pd.concat([z, sector_dummies], axis=1)
    if interactions and with_sector:
        for c in [c for c in z if c.startswith("sector_")]: z["female_x_" + c] = z[c] * x["female"].to_numpy()
    z = pd.concat([pd.Series(1.0, index=x.index, name="const"), x[cols], z], axis=1)
    z = z.loc[:, ~z.columns.duplicated()].astype(float); return x, z


def fit_multinomial(x: pd.DataFrame, X: pd.DataFrame, model: str, start: np.ndarray | None = None) -> tuple[pd.DataFrame, dict]:
    a, b, k = X.to_numpy(), x.y.to_numpy(), 3; w_raw = x.weight_pooled.to_numpy(dtype=float); w = w_raw / w_raw.mean(); p = a.shape[1]; y_one = np.eye(k)[b]
    def unpack(theta): return theta.reshape(k-1, p)
    def objective(theta, grad=False):
        B = unpack(theta); eta = a @ B.T; eta = np.column_stack([np.zeros(len(a)), eta]); eta -= eta.max(1, keepdims=True); pr = np.exp(eta); pr /= pr.sum(1, keepdims=True)
        val = -np.sum(w * np.sum(y_one * np.log(np.clip(pr, 1e-12, 1)), axis=1))
        if not grad: return val
        return -((w[:, None] * (y_one[:, 1:] - pr[:, 1:])).T @ a).ravel()
    initial = np.zeros((k-1)*p) if start is None else np.asarray(start, dtype=float)
    res = minimize(objective, initial, jac=lambda t: objective(t, True), method="L-BFGS-B", options={"maxiter": 1000, "ftol": 1e-13, "gtol": 1e-8, "maxls": 50})
    B = unpack(res.x); eta = np.column_stack([np.zeros(len(a)), a @ B.T]); eta -= eta.max(1, keepdims=True); pr = np.exp(eta); pr /= pr.sum(1, keepdims=True)
    pred = x[["sex", "education", "source_quarter"]].copy(); pred["model"] = model; pred["p0"] = pr[:, 0]; pred["p1"] = pr[:, 1]; pred["p2"] = pr[:, 2]
    coef = pd.DataFrame(B.T, index=X.columns, columns=["machine_vs_ref", "systems_vs_ref"]).reset_index(names="term"); coef["model"] = model
    diag = {"model": model, "converged": bool(res.success), "message": str(res.message), "iterations": int(res.nit), "n": int(len(x)), "clusters_household": int(x.household_id.nunique()), "weighted_n": float(w_raw.sum()), "max_probability_sum_error": float(np.abs(pr.sum(1)-1).max())}
    return coef, pred, diag


def models(d: pd.DataFrame) -> dict:
    all_coef, all_pred, diagnostics = [], [], []
    for name, sector, inter in [("M1", False, False), ("M2", True, False), ("M3", True, True)]:
        x, X = design(d, sector, inter); coef, pred, diag = fit_multinomial(x, X, name); all_coef.append(coef); all_pred.append(pred); diagnostics.append(diag)
        for sex in ["1", "2"]:
            g = pred[pred.sex.eq(sex)]; diagnostics.append({"model": name, "sex": sex, "standardized_p0": float(g.p0.mean()), "standardized_p1": float(g.p1.mean()), "standardized_p2": float(g.p2.mean()), "n": len(g)})
    save(pd.concat(all_coef, ignore_index=True), "multinomial_coefficients.csv"); save(pd.concat(all_pred, ignore_index=True), "multinomial_individual_predictions.csv"); save(pd.DataFrame(diagnostics), "multinomial_diagnostics_and_standardized_predictions.csv"); return {"diagnostics": diagnostics}


def plots() -> list[str]:
    ci = pd.read_csv(REPORT / "kitagawa_bootstrap_ci.csv")
    fig, ax = plt.subplots(figsize=(8, 4.8), facecolor="white")
    labels = {"gap_pp": "Brecha agregada", "intersectorial_pp": "Intersectorial", "intrasectorial_pp": "Intrasectorial"}
    y = np.arange(len(ci))
    ax.errorbar(ci.estimate, y, xerr=[ci.estimate-ci.ci95_low, ci.ci95_high-ci.estimate], fmt="o", color="#0b3c5d", ecolor="#4f9bc7", capsize=3)
    ax.axvline(0, color="#555", lw=.8); ax.set_yticks(y, [f"{r.outcome} — {labels[r.statistic]}" for _, r in ci.iterrows()]); ax.set_xlabel("Puntos porcentuales"); ax.set_title("Descomposición tecnológica: IC bootstrap por vivienda"); fig.tight_layout(); fig.savefig(REPORT / "figura_1_kitagawa_ic.png", dpi=220, facecolor="white"); plt.close(fig)
    d = pd.read_csv(REPORT / "multinomial_diagnostics_and_standardized_predictions.csv"); d = d[d.sex.notna()].copy(); d["sexo"] = d.sex.map({1: "Varones", 2: "Mujeres"})
    fig, axes = plt.subplots(1, 3, figsize=(11, 4), sharey=True, facecolor="white")
    for ax, model in zip(axes, ["M1", "M2", "M3"]):
        z = d[d.model.eq(model)].set_index("sexo")[["standardized_p0", "standardized_p1", "standardized_p2"]]; z.columns = ["No tecnológica", "Máquinas", "Sistemas"]
        z.plot.bar(ax=ax, color=["#d9e7f2", "#4f9bc7", "#0b3c5d"], legend=False); ax.set_title(model); ax.set_ylim(0, .7); ax.set_ylabel("Probabilidad marginal" if model == "M1" else ""); ax.tick_params(axis="x", rotation=0)
    axes[-1].legend(frameon=False, loc="upper right"); fig.suptitle("Probabilidades predichas estandarizadas por sexo", y=1.02); fig.tight_layout(); fig.savefig(REPORT / "figura_2_probabilidades_marginales.png", dpi=220, facecolor="white"); plt.close(fig)
    return ["figura_1_kitagawa_ic.png", "figura_2_probabilidades_marginales.png"]


def main() -> None:
    REPORT.mkdir(parents=True, exist_ok=True); d = load_frame()
    reconciliation = universe_reconciliation(d); reps = repetitions(d); raw = raw_reproduction()
    base = kitagawa(d); boot = bootstrap(d); est = estimands(d); mod = models(d); figures = plots()
    save(pd.DataFrame(base["rows"]), "kitagawa_point_estimates.csv")
    save({"seed": SEED, "bootstrap_replicates_requested": BOOT_REPS, "raw_reproduction": raw, "strict_rows": int(d.final_analytic.sum()), "old_strict_rows": int((d.final_analytic | (d.occupied15 & d.cno_valid.astype(bool) & d.caes_code.eq("9999") & d.technology_valid_strict)).sum()), "analytic_households": int(d.loc[d.final_analytic, "household_id"].nunique()), "caes_00xx": sorted(d.loc[d.final_analytic & d.caes_code.str.startswith("00"), "caes_code"].unique().tolist()), "caes_9999_excluded": int((d.caes_code.eq("9999") & d.occupied15).sum()), "figures": figures, "models_note": "Pondered likelihood and marginal predictions are exploratory; no survey-design SEs are claimed."}, "summary.json")
    print(json.dumps({"strict_rows": int(d.final_analytic.sum()), "raw": raw, "bootstrap_rows": len(boot), "models": mod["diagnostics"][-6:]}, ensure_ascii=False, indent=2))


if __name__ == "__main__": main()
