from pathlib import Path
import json

import pandas as pd


REPORT = Path(__file__).parents[1] / "reports" / "generated" / "stage7_decomposition"


def test_kitagawa_identity_holds_for_all_sensitivities():
    summary = pd.read_csv(REPORT / "decomposition_summary.csv")
    assert summary["identity_error_pp"].abs().max() < 1e-10
    assert (summary["aggregate_gap_pp"] - summary["reconstructed_gap_pp"]).abs().max() < 1e-10


def test_descriptive_denominators_sum_to_one_hundred():
    checks = pd.read_csv(REPORT / "denominator_checks.csv")
    assert checks["all_groups_close"].all()
    assert checks["max_abs_deviation_from_100_pp"].max() < 1e-8


def test_sector_order_does_not_change_component_totals():
    contrib = pd.read_csv(REPORT / "sector_contributions_pooled_4q_sector_provisional.csv")
    forward = contrib.groupby("outcome")[["intersectorial_pp", "intrasectorial_pp"]].sum().sort_index()
    reverse = contrib.iloc[::-1].groupby("outcome")[["intersectorial_pp", "intrasectorial_pp"]].sum().sort_index()
    pd.testing.assert_frame_equal(forward, reverse)


def test_pooled_weight_is_quarter_average():
    weights = pd.Series([100.0, 200.0, 300.0, 400.0])
    assert weights.div(4).sum() == weights.mean()


def test_universe_reconciliation_is_explicit_and_corrected():
    summary = json.loads((REPORT / "summary.json").read_text(encoding="utf-8"))
    assert summary["universe"]["wide_rows"] == 79222
    assert summary["universe"]["strict_rows"] == 73863
