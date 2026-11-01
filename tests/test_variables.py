import pandas as pd

from eph_genero_tecnologia.variables import binary_informatized, classify_technology, normalize_code


def test_normalize_code_preserves_leading_zeroes():
    result = normalize_code(pd.Series(["101", "0003", None]), 5)
    assert result.iloc[0] == "00101"
    assert result.iloc[1] == "00003"
    assert pd.isna(result.iloc[2])


def test_classify_technology_uses_fourth_digit():
    result = classify_technology(pd.Series(["01211", "01221", "01231", "09999"]))
    assert result.iloc[0] == "No tecnológica"
    assert result.iloc[1] == "Operación de máquinas"
    assert result.iloc[2] == "Operación de sistemas informatizados"
    assert pd.isna(result.iloc[3])


def test_binary_indicator():
    assert binary_informatized(pd.Series(["01231", "01211"])).tolist() == [1, 0]


def test_classification_rejects_unknown_fourth_digit_and_missing():
    result = classify_technology(pd.Series(["01241", None, "0123"]))
    assert pd.isna(result.iloc[0])
    assert pd.isna(result.iloc[1])
    assert pd.notna(result.iloc[2])
