import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "projects" / "mas-alla-educacion" / "scripts" / "run_stage8_inference.py"
spec = importlib.util.spec_from_file_location("stage8", SCRIPT)
stage8 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(stage8)


def test_kitagawa_identity_on_processed_data():
    d = stage8.load_frame()
    result = stage8.kitagawa(d)
    assert len(result["rows"]) == 2
    assert max(abs(x["identity_error_pp"]) for x in result["rows"]) < 1e-8


def test_three_universes_have_unique_overlap_structure():
    d = stage8.load_frame()
    old = d.final_analytic | (d.occupied15 & d.cno_valid.astype(bool) & d.caes_code.eq("9999") & d.technology_valid_strict)
    technology = d.wide_universe & d.technology_valid_strict
    corrected = d.final_analytic
    assert int(old.sum()) == 74221
    assert int(technology.sum()) == 74017
    assert int(corrected.sum()) == 73863
    assert int((old & technology & corrected).sum()) == 73863
    assert int((old & ~technology).sum()) == 358
    assert int((technology & ~old).sum()) == 154


def test_pooled_weight_is_quarterly_average_scale():
    d = stage8.load_frame()
    x = d[d.final_analytic]
    assert np.isclose(x.weight_pooled.sum(), x.weight_person.sum() / 4)


def test_estimand_ratio_is_defined_for_both_sexes_and_outcomes():
    result = stage8.estimands(stage8.load_frame())
    assert set(zip(result.sex, result.outcome)) == {("1", "systems"), ("1", "machines"), ("2", "systems"), ("2", "machines")}
    assert result.ratio_of_averages.between(0, 1).all()


def test_bootstrap_reproducible_with_fixed_seed_on_small_replicates():
    d = stage8.load_frame()
    a = stage8.bootstrap(d, reps=4)
    b = stage8.bootstrap(d, reps=4)
    pd.testing.assert_frame_equal(a, b)
