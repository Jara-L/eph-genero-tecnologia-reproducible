"""Etapa 9: auditoría final, bootstrap ampliado y tablas para revisión académica."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[3]
STAGE8_PATH = ROOT / "projects" / "mas-alla-educacion" / "scripts" / "run_stage8_inference.py"
REPORT = ROOT / "reports" / "generated" / "stage9_validation"
SEED = 20261013
MODEL_BOOT_REPS = 60

EDUCATION_LABELS = {
    "1": "Primario incompleto",
    "2": "Primario completo",
    "3": "Secundario incompleto",
    "4": "Secundario completo",
    "5": "Superior universitario incompleto",
    "6": "Superior universitario completo",
    "7": "Sin instrucción",
}

spec = importlib.util.spec_from_file_location("stage8", STAGE8_PATH)
stage8 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(stage8)
stage8.REPORT = REPORT
stage8.SEED = SEED
stage8.BOOT_REPS = 1000


def save(value, name):
    REPORT.mkdir(parents=True, exist_ok=True)
    if isinstance(value, pd.DataFrame): value.to_csv(REPORT / name, index=False)
    else: (REPORT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def numerical_gradient_check(x, X, coef):
    a, y = X.to_numpy(), x.y.to_numpy(); w = x.weight_pooled.to_numpy(dtype=float); w = w / w.mean(); y_one = np.eye(3)[y]; beta = coef.set_index("term")[["machine_vs_ref", "systems_vs_ref"]].reindex(X.columns).to_numpy().T
    eta = np.column_stack([np.zeros(len(a)), a @ beta.T]); eta -= eta.max(1, keepdims=True); p = np.exp(eta); p /= p.sum(1, keepdims=True)
    analytic = -((w[:, None] * (y_one[:, 1:] - p[:, 1:])).T @ a).ravel()
    # Independent centered finite differences on a compact deterministic subset.
    ix = np.linspace(0, len(a)-1, min(3000, len(a)), dtype=int); aa, yy, ww = a[ix], y_one[ix], w[ix]
    def objective(t):
        b = t.reshape(2, a.shape[1]); e = np.column_stack([np.zeros(len(aa)), aa @ b.T]); e -= e.max(1, keepdims=True); q = np.exp(e); q /= q.sum(1, keepdims=True); return -np.sum(ww * np.sum(yy * np.log(np.clip(q, 1e-12, 1)), axis=1))
    # Normalize comparison to the same subset.
    subgrad = -((ww[:, None] * (yy[:, 1:] - p[ix, 1:])).T @ aa).ravel(); numeric = np.zeros_like(subgrad); eps = 1e-5
    t = beta.ravel()
    for j in range(len(t)):
        u = t.copy(); v = t.copy(); u[j] += eps; v[j] -= eps; numeric[j] = (objective(u)-objective(v))/(2*eps)
    return {"max_abs_gradient_full": float(np.abs(analytic).max()), "max_abs_gradient_subset": float(np.abs(subgrad).max()), "max_abs_numeric_gradient_difference_subset": float(np.abs(numeric-subgrad).max()), "subset_n": int(len(ix))}


def prediction_table(d, model_name, with_sector, interactions):
    spec = {"education": sorted(d.loc[d.final_analytic & d.education.notna(), "education"].dropna().unique().tolist()), "quarter": sorted(d.loc[d.final_analytic, "source_quarter"].dropna().unique().tolist()), "sector": sorted(d.loc[d.final_analytic & d.macro_sector.notna(), "macro_sector"].dropna().unique().tolist())}
    x, X = stage8.design(d, with_sector, interactions, category_spec=spec); coef, pred, diag = stage8.fit_multinomial(x, X, model_name)
    B = coef.set_index("term")[["machine_vs_ref", "systems_vs_ref"]].reindex(X.columns).to_numpy().T; a = X.to_numpy(); eta = np.column_stack([np.zeros(len(a)), a @ B.T]); eta -= eta.max(1, keepdims=True); pr = np.exp(eta); pr /= pr.sum(1, keepdims=True)
    out = x[["sex", "education", "macro_sector", "household_id"]].copy(); out["model"] = model_name; out["p0"], out["p1"], out["p2"] = pr[:,0], pr[:,1], pr[:,2]
    return x, X, coef, out, diag, spec


def probabilities_from_fit(x, X, coef):
    B = coef.set_index("term")[["machine_vs_ref", "systems_vs_ref"]].reindex(X.columns).to_numpy().T; a = X.to_numpy(); eta = np.column_stack([np.zeros(len(a)), a @ B.T]); eta -= eta.max(1, keepdims=True); pr = np.exp(eta); return pr / pr.sum(1, keepdims=True)


def standardized_probabilities(d, coef, category_spec, with_sector, interactions, sex, reference):
    h = reference.copy(); h["sex"] = sex; hx, hX = stage8.design(h, with_sector, interactions, category_spec=category_spec); pr = probabilities_from_fit(hx, hX, coef); w = hx.weight_pooled.to_numpy(dtype=float); w = w / w.sum(); return np.average(pr, axis=0, weights=w), len(hx), float(hx.weight_pooled.sum())


def education_results(d):
    rows, diagnostics, fits = [], [], {}
    for model, sector, inter in [("M1", False, False), ("M2", True, False), ("M3", True, True)]:
        x, X, coef, pred, diag, category_spec = prediction_table(d, model, sector, inter); fits[model] = (x, X, coef, pred, category_spec); diagnostics.append(diag)
        alt_start = np.random.default_rng(SEED + len(model)).normal(0, 0.01, size=2 * X.shape[1]); alt_coef, _, alt_diag = stage8.fit_multinomial(x, X, model, start=alt_start)
        aligned = coef.set_index("term").loc[X.columns, ["machine_vs_ref", "systems_vs_ref"]].to_numpy(); aligned_alt = alt_coef.set_index("term").loc[X.columns, ["machine_vs_ref", "systems_vs_ref"]].to_numpy()
        diagnostics.append({"model": model, "alternate_start_converged": alt_diag["converged"], "alternate_start_max_abs_coefficient_difference": float(np.abs(aligned-aligned_alt).max())})
        diagnostics.append({"model": model, **numerical_gradient_check(x, X, coef)})
        # Common standardization population within each education level: the same
        # rows are evaluated twice, once with female=0 and once with female=1.
        ref = d[d.final_analytic & d.education.notna() & d.macro_sector.notna()].copy()
        for edu, g in ref.groupby("education", dropna=False):
            for sex in ["1", "2"]:
                hp, n_ref, w_ref = standardized_probabilities(d, coef, category_spec, sector, inter, sex, g[g.education.eq(edu)].copy())
                rows.append({"model": model, "education": edu, "sex": sex, "n": n_ref, "households": g[g.education.eq(edu)].household_id.nunique(), "reference_weight": w_ref, "machines_probability": hp[1], "systems_probability": hp[2]})
    table = pd.DataFrame(rows); table["education_label"] = table.education.map(EDUCATION_LABELS); table["sex_label"] = table.sex.map({"1":"Varones", "2":"Mujeres"}); save(table, "probabilidades_por_educacion_sexo_modelo.csv")
    wide = table.pivot_table(index=["model","education"], columns="sex", values=["machines_probability","systems_probability"], aggfunc="first").reset_index()
    wide.columns = ["_".join([str(a),str(b)]).strip("_") for a,b in wide.columns]; wide["education_label"] = wide.education.map(EDUCATION_LABELS); wide["machines_gap_female_minus_male_pp"] = 100*(wide["machines_probability_2"]-wide["machines_probability_1"]); wide["systems_gap_female_minus_male_pp"] = 100*(wide["systems_probability_2"]-wide["systems_probability_1"]); save(wide, "brechas_ajustadas_por_educacion.csv")
    ref_all = d[d.final_analytic & d.education.notna() & d.macro_sector.notna()].copy()
    aggregate = []
    for model, sector, inter in [("M1", False, False), ("M2", True, False), ("M3", True, True)]:
        coef = fits[model][2]; category_spec = fits[model][4]
        for sex, label in [("1", "Varones"), ("2", "Mujeres")]:
            p, n_ref, w_ref = standardized_probabilities(d, coef, category_spec, sector, inter, sex, ref_all)
            aggregate.append({"model": model, "sex": sex, "sex_label": label, "reference_rows": n_ref, "reference_households": ref_all.household_id.nunique(), "reference_weight": w_ref, "standardized_p0": p[0], "standardized_p1": p[1], "standardized_p2": p[2], "estimate_type": "point_estimate"})
    save(pd.DataFrame(aggregate), "multinomial_standardized_predictions.csv")
    # M3 sector predictions only for cells with at least 100 records by sex.
    m3 = fits["M3"][3]; support = m3.groupby(["macro_sector","sex"]).size().unstack(fill_value=0); keep = support.index[(support.get("1",0) >= 100) & (support.get("2",0) >= 100)]
    sec_rows = []; ref_sector = d[d.final_analytic & d.macro_sector.isin(keep) & d.education.notna()].copy()
    for sec_name, g in ref_sector.groupby("macro_sector"):
        for sex in ["1", "2"]:
            pr, n_ref, w_ref = standardized_probabilities(d, fits["M3"][2], fits["M3"][4], True, True, sex, g)
            sec_rows.append({"macro_sector": sec_name, "sex": sex, "n_reference": n_ref, "reference_weight": w_ref, "machines_probability": pr[1], "systems_probability": pr[2]})
    save(pd.DataFrame(sec_rows), "predicciones_m3_sector_estable.csv")
    save(pd.DataFrame(diagnostics), "diagnosticos_modelos_etapa9.csv"); return fits, pd.DataFrame(diagnostics)


def education_plot():
    table = pd.read_csv(REPORT / "brechas_ajustadas_por_educacion.csv")
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.2), facecolor="white")
    for ax, col, title in [(axes[0], "machines_gap_female_minus_male_pp", "Máquinas"), (axes[1], "systems_gap_female_minus_male_pp", "Sistemas informatizados")]:
        for model, color in [("M1", "#0b3c5d"), ("M2", "#4f9bc7"), ("M3", "#91b9d4")]:
            z = table[table.model.eq(model)].sort_values("education"); ax.plot(z.education, z[col], marker="o", lw=1.8, label=model, color=color)
        ax.axhline(0, color="#555", lw=.8); ax.set_title(title); ax.set_xlabel("Nivel educativo EPH"); ax.set_ylabel("Brecha mujeres−varones (pp)"); ax.grid(axis="y", alpha=.2)
    axes[1].legend(frameon=False); fig.suptitle("Brechas ajustadas por nivel educativo", y=1.02); fig.tight_layout(); fig.savefig(REPORT / "figura_3_brechas_educacion.png", dpi=220, facecolor="white"); plt.close(fig)


def fixed_kitagawa(x, sector, fixed_sectors):
    x = x[x.final_analytic & x[sector].isin(fixed_sectors) & x.sex.isin(["1", "2"])].copy(); st = x.groupby([sector, "sex"]).weight_pooled.sum().unstack(fill_value=0).reindex(fixed_sectors)
    if st.isna().any().any() or (st <= 0).any().any(): return None
    totals = x.groupby("sex").weight_pooled.sum()
    rows = []
    for outcome, digit in [("systems", "3"), ("machines", "2")]:
        ot = x[x.cno_digit.eq(digit)].groupby([sector, "sex"]).weight_pooled.sum().unstack(fill_value=0).reindex(fixed_sectors, fill_value=0)
        qm, qf = st["1"] / totals["1"], st["2"] / totals["2"]; pm, pf = ot["1"] / st["1"], ot["2"] / st["2"]
        gap = (qf*pf).sum()-(qm*pm).sum(); inter = (0.5*(pf+pm)*(qf-qm)).sum(); intra = (0.5*(qf+qm)*(pf-pm)).sum()
        rows.append({"outcome":outcome,"gap_pp":100*gap,"intersectorial_pp":100*inter,"intrasectorial_pp":100*intra,"identity_error_pp":100*(gap-inter-intra),"sectors":len(fixed_sectors)})
    return rows


def bootstrap_kitagawa_fixed(d):
    x = d[d.final_analytic & d.sector_provisional.notna() & d.sex.isin(["1","2"])].copy(); clusters=x.household_id.drop_duplicates().to_numpy(); rng=np.random.default_rng(SEED); schemes=[]
    detailed = sorted(x.sector_provisional.unique().tolist()); macro = sorted(x.macro_sector.dropna().unique().tolist()); schemes.extend([("detailed_19", "sector_provisional", detailed), ("macro_11", "macro_sector", macro)])
    rows=[]
    for scheme, col, support in schemes:
        for b in range(1000):
            mult=pd.Series(rng.choice(clusters,size=len(clusters),replace=True)).value_counts(); boot=x.copy(); boot["weight_pooled"]*=boot.household_id.map(mult).fillna(0); boot=boot[boot.weight_pooled.gt(0)]; result=fixed_kitagawa(boot,col,support)
            if result is None:
                rows.append({"scheme":scheme,"replicate":b,"valid":False,"failure":"missing_sex_sector_support"}); continue
            for r in result: rows.append({"scheme":scheme,"replicate":b,"valid":True,**r})
    out=pd.DataFrame(rows); save(out,"kitagawa_bootstrap_fixed_support_replicates.csv"); valid=out[out.valid.eq(True)]
    summary=valid.groupby(["scheme","outcome"]).agg(replicates=("replicate","nunique"),gap_bootstrap_mean_pp=("gap_pp","mean"),gap_ci_low=("gap_pp",lambda s:s.quantile(.025)),gap_ci_high=("gap_pp",lambda s:s.quantile(.975)),intersectorial_bootstrap_mean_pp=("intersectorial_pp","mean"),inter_ci_low=("intersectorial_pp",lambda s:s.quantile(.025)),inter_ci_high=("intersectorial_pp",lambda s:s.quantile(.975)),intrasectorial_bootstrap_mean_pp=("intrasectorial_pp","mean"),intra_ci_low=("intrasectorial_pp",lambda s:s.quantile(.025)),intra_ci_high=("intrasectorial_pp",lambda s:s.quantile(.975))).reset_index(); summary["failed_replicates"]=1000-summary.replicates
    points = []
    for scheme, col, support in [("detailed_19", "sector_provisional", detailed), ("macro_11", "macro_sector", macro)]:
        for row in fixed_kitagawa(d, col, support): points.append({"scheme": scheme, "outcome": row["outcome"], "gap_point_estimate_pp": row["gap_pp"], "intersectorial_point_estimate_pp": row["intersectorial_pp"], "intrasectorial_point_estimate_pp": row["intrasectorial_pp"], "identity_error_pp": row["identity_error_pp"], "sectors": row["sectors"]})
    point = pd.DataFrame(points); save(point, "kitagawa_point_estimates.csv")
    summary = summary.merge(point[["scheme", "outcome", "gap_point_estimate_pp", "intersectorial_point_estimate_pp", "intrasectorial_point_estimate_pp"]], on=["scheme", "outcome"], how="left")
    save(summary,"kitagawa_bootstrap_fixed_support_ci.csv"); save(out.groupby(["scheme","valid","failure"],dropna=False).size().rename("rows").reset_index(),"kitagawa_bootstrap_support_diagnostics.csv"); return summary


def fixed_kitagawa_plot():
    summary = pd.read_csv(REPORT / "kitagawa_bootstrap_fixed_support_ci.csv")
    fig, axes = plt.subplots(1, 2, figsize=(11, 5), sharey=True, facecolor="white")
    labels = {"systems": "Sistemas", "machines": "Máquinas"}
    for ax, outcome in zip(axes, ["systems", "machines"]):
        z = summary[summary.outcome.eq(outcome)].copy(); y = np.arange(len(z))
        ax.errorbar(z.gap_point_estimate_pp, y, xerr=[z.gap_point_estimate_pp-z.gap_ci_low, z.gap_ci_high-z.gap_point_estimate_pp], fmt="o", color="#0b3c5d", capsize=3)
        ax.set_yticks(y, [f"{s} ({int(n)} válidas)" for s, n in zip(z.scheme, z.replicates)]); ax.axvline(0, color="#555", lw=.8); ax.set_title(labels[outcome]); ax.set_xlabel("Brecha agregada (pp)"); ax.grid(axis="x", alpha=.2)
    axes[0].set_ylabel("Esquema de soporte fijo"); fig.suptitle("Kitagawa: estimación puntual e IC bootstrap por soporte fijo", y=1.02); fig.tight_layout(); fig.savefig(REPORT / "figura_1_kitagawa_ic.png", dpi=220, facecolor="white"); plt.close(fig)


def standardized_predictions_plot():
    d = pd.read_csv(REPORT / "multinomial_standardized_predictions.csv")
    fig, axes = plt.subplots(1, 3, figsize=(11, 4), sharey=True, facecolor="white")
    for ax, model in zip(axes, ["M1", "M2", "M3"]):
        z = d[d.model.eq(model)].set_index("sex_label")[["standardized_p0", "standardized_p1", "standardized_p2"]]; z.columns = ["No tecnológica", "Máquinas", "Sistemas"]
        z.plot.bar(ax=ax, color=["#d9e7f2", "#4f9bc7", "#0b3c5d"], legend=False); ax.set_title(model); ax.set_ylim(0, .7); ax.set_ylabel("Probabilidad marginal" if model == "M1" else ""); ax.tick_params(axis="x", rotation=0)
    axes[-1].legend(frameon=False, loc="upper right"); fig.suptitle("Probabilidades contrafactuales estandarizadas por sexo", y=1.02); fig.tight_layout(); fig.savefig(REPORT / "figura_2_probabilidades_marginales.png", dpi=220, facecolor="white"); plt.close(fig)


def model_bootstrap(d, fits):
    # A deliberately modest clustered bootstrap for adjusted gaps; it is not a survey-design variance.
    rng = np.random.default_rng(SEED); x0 = d[d.final_analytic & d.sex.isin(["1","2"]) & d.education.notna() & d.macro_sector.notna()].copy(); clusters = x0.household_id.drop_duplicates().to_numpy(); rows=[]
    for b in range(MODEL_BOOT_REPS):
        mult = pd.Series(rng.choice(clusters, size=len(clusters), replace=True)).value_counts(); x = x0[x0.household_id.map(mult).fillna(0).gt(0)].copy(); x["weight_pooled"] *= x.household_id.map(mult).fillna(0)
        for model, sector, inter in [("M1",False,False),("M2",True,False),("M3",True,True)]:
            try:
                category_spec = fits[model][4]; z, X = stage8.design(x, sector, inter, category_spec=category_spec); coef, pred, diag = stage8.fit_multinomial(z, X, model)
                reference = x0
                p_m, _, _ = standardized_probabilities(d, coef, category_spec, sector, inter, "1", reference); p_f, _, _ = standardized_probabilities(d, coef, category_spec, sector, inter, "2", reference)
                rows.append({"replicate":b,"model":model,"machines_gap_pp":100*(p_f[1]-p_m[1]),"systems_gap_pp":100*(p_f[2]-p_m[2]),"converged":diag["converged"]})
            except Exception as exc:
                rows.append({"replicate":b,"model":model,"converged":False,"error":type(exc).__name__})
    out=pd.DataFrame(rows); save(out,"bootstrap_model_gaps.csv"); ok=out[out.converged.eq(True)]; summary=ok.groupby("model").agg(replicates=("replicate","nunique"), machines_gap_mean=("machines_gap_pp","mean"), machines_ci_low=("machines_gap_pp",lambda s:s.quantile(.025)), machines_ci_high=("machines_gap_pp",lambda s:s.quantile(.975)), systems_gap_mean=("systems_gap_pp","mean"), systems_ci_low=("systems_gap_pp",lambda s:s.quantile(.025)), systems_ci_high=("systems_gap_pp",lambda s:s.quantile(.975))).reset_index(); summary["failed_replicates"] = MODEL_BOOT_REPS-summary.replicates; save(summary,"bootstrap_model_gaps_ci.csv"); return summary


def main():
    d = stage8.load_frame(); kitagawa_ci = bootstrap_kitagawa_fixed(d); fits, diagnostics = education_results(d); education_plot(); fixed_kitagawa_plot(); standardized_predictions_plot(); model_ci = model_bootstrap(d, fits)
    save({"kitagawa_replicates":1000,"model_bootstrap_replicates":MODEL_BOOT_REPS,"seed":SEED,"strict_rows":int(d.final_analytic.sum()),"analytical_households":int(d.loc[d.final_analytic,"household_id"].nunique()),"model_ci_is_exploratory":True,"models_note":"Weighted pseudo-maximum likelihood; marginal predictions use the same weighted reference rows for both sexes; clustered bootstrap sensitivity, not full EPH survey variance."},"summary.json")
    print(json.dumps({"strict_rows":int(d.final_analytic.sum()),"kitagawa":kitagawa_ci.to_dict(orient="records"),"model_bootstrap":model_ci.to_dict(orient="records")},ensure_ascii=False,indent=2))


if __name__ == "__main__": main()
