import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "projects/mas-alla-educacion" / "scripts" / "run_stage9_validation.py"
spec = importlib.util.spec_from_file_location("stage9", SCRIPT)
stage9 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(stage9)


def test_fixed_category_spec_preserves_training_columns_after_education_filter():
    d = stage9.stage8.load_frame()
    spec = {"education": sorted(d.loc[d.final_analytic & d.education.notna(), "education"].unique()), "quarter": sorted(d.loc[d.final_analytic, "source_quarter"].unique()), "sector": sorted(d.loc[d.final_analytic & d.macro_sector.notna(), "macro_sector"].unique())}
    _, X = stage9.stage8.design(d, True, True, category_spec=spec)
    h = d[d.final_analytic & d.education.eq(spec["education"][0])].copy(); _, HX = stage9.stage8.design(h, True, True, category_spec=spec)
    assert list(HX.columns) == list(X.columns)
    assert HX.shape[1] == X.shape[1]


def test_marginal_standardization_uses_same_reference_rows_and_weights():
    d = stage9.stage8.load_frame(); x, X, coef, _, _, cat = stage9.prediction_table(d, "M2", True, False)
    ref = d[d.final_analytic & d.education.notna() & d.macro_sector.notna()].copy()
    p_m, n_m, w_m = stage9.standardized_probabilities(d, coef, cat, True, False, "1", ref)
    p_f, n_f, w_f = stage9.standardized_probabilities(d, coef, cat, True, False, "2", ref)
    assert n_m == n_f == len(ref)
    assert np.isclose(w_m, w_f)
    assert np.isclose(p_m.sum(), 1) and np.isclose(p_f.sum(), 1)


def test_fixed_kitagawa_does_not_impute_missing_sector_support():
    d = stage9.stage8.load_frame(); x = d[d.final_analytic].copy(); support = sorted(x.sector_provisional.dropna().unique())
    one = x[x.sector_provisional.ne(support[0])].copy()
    assert stage9.fixed_kitagawa(one, "sector_provisional", support) is None


def test_six_corrected_marginal_gaps_match_published_targets():
    table = pd.read_csv(ROOT / "reports/generated/stage9_validation/multinomial_standardized_predictions.csv")
    table["sex"] = table["sex"].astype(int)
    wide = table.pivot(index="model", columns="sex", values=["standardized_p1", "standardized_p2"])
    expected = {"M1": (-12.3519, 2.1394), "M2": (-7.4277, 3.3692), "M3": (-7.3597, 6.3286)}
    for model, (machines, systems) in expected.items():
        assert np.isclose(100 * (wide.loc[model, ("standardized_p1", 2)] - wide.loc[model, ("standardized_p1", 1)]), machines, atol=1e-4)
        assert np.isclose(100 * (wide.loc[model, ("standardized_p2", 2)] - wide.loc[model, ("standardized_p2", 1)]), systems, atol=1e-4)


def test_final_tables_and_figures_are_corresponding_and_kitagawa_is_separated():
    report = ROOT / "reports/generated/stage9_validation"
    ci = pd.read_csv(report / "kitagawa_bootstrap_fixed_support_ci.csv")
    points = pd.read_csv(report / "kitagawa_point_estimates.csv")
    assert set(ci.scheme) == {"detailed_19", "macro_11"}
    assert set(ci.replicates) == {835, 1000}
    assert set(points.columns) >= {"gap_point_estimate_pp", "intersectorial_point_estimate_pp", "intrasectorial_point_estimate_pp"}
    assert np.isclose(points.loc[(points.scheme == "detailed_19") & (points.outcome == "systems"), "gap_point_estimate_pp"].iloc[0], 10.0086, atol=1e-4)
    assert np.isclose(points.loc[(points.scheme == "detailed_19") & (points.outcome == "machines"), "gap_point_estimate_pp"].iloc[0], -13.8079, atol=1e-4)
    for name in ["figura_1_kitagawa_ic.png", "figura_2_probabilidades_marginales.png"]:
        assert (report / name).exists() and (report / name).stat().st_size > 1000
    assert not (report / "multinomial_diagnostics_and_standardized_predictions.csv").exists()
