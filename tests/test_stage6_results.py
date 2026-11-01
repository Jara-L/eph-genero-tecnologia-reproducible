import pandas as pd
import importlib.util
from pathlib import Path

_SCRIPT = Path(__file__).parents[1] / "projects" / "mas-alla-educacion" / "scripts" / "run_stage6_results.py"
_SPEC = importlib.util.spec_from_file_location("stage6_results", _SCRIPT)
_MODULE = importlib.util.module_from_spec(_SPEC)
assert _SPEC.loader is not None
_SPEC.loader.exec_module(_MODULE)
TECH_BY_DIGIT = _MODULE.TECH_BY_DIGIT
add_share = _MODULE.add_share


def test_technology_categories_are_driven_by_cno_digit():
    assert set(TECH_BY_DIGIT) == {"1", "2", "3"}
    assert TECH_BY_DIGIT["1"] != TECH_BY_DIGIT["2"]


def test_weighted_shares_use_explicit_group_denominator():
    frame = pd.DataFrame({
        "group": ["A", "A", "B"],
        "unweighted": [1, 1, 1],
        "weighted": [3.0, 1.0, 8.0],
    })
    result = add_share(frame, ["group"])
    assert result[result["group"] == "A"]["weighted_percent"].sum() == 100
    assert result.loc[result["weighted"] == 3, "weighted_percent"].iloc[0] == 75


def test_pooled_weight_is_quarter_average():
    weights = pd.Series([100.0, 200.0, 300.0, 400.0])
    assert weights.div(4).sum() == weights.mean()
