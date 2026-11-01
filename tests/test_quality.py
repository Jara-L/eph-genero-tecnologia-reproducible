import pandas as pd

from eph_genero_tecnologia.quality import audit_repeated_observations, weighted_crosstab


def test_repeats_require_two_external_quarters():
    frame = pd.DataFrame({
        "CODUSU": ["a"], "NRO_HOGAR": ["1"], "COMPONENTE": ["1"],
        "TRIMESTRE": [4], "ANO4": [2025], "_quarter": ["2025-T4"],
    })
    result = audit_repeated_observations([frame])
    assert result.iloc[0]["status"] == "insufficient_quarters"
    assert result.iloc[0]["n_quarters"] == 1


def test_repeats_are_counted_across_external_quarters():
    frames = []
    for quarter in ["2025-T3", "2025-T4"]:
        frames.append(pd.DataFrame({
            "CODUSU": ["a"], "NRO_HOGAR": ["1"], "COMPONENTE": ["1"],
            "TRIMESTRE": [4], "ANO4": [2025], "_quarter": [quarter],
        }))
    result = audit_repeated_observations(frames)
    assert result.iloc[0]["periods"] == 2
    assert bool(result.iloc[0]["potentially_repeated"])


def test_weighted_crosstab_uses_row_denominator():
    frame = pd.DataFrame({
        "sector": ["A", "A", "B"], "sex": [1, 2, 1],
        "weight": [2, 1, 4],
    })
    result = weighted_crosstab(frame, "sector", "sex", "weight")
    a = result[result["sector"] == "A"].set_index("sex")
    assert a.loc[1, "row_percent"] == 2 / 3 * 100
    assert a.loc[2, "row_percent"] == 1 / 3 * 100
