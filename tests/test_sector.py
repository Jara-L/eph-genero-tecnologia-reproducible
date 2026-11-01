import pandas as pd

from eph_genero_tecnologia.sector import provisional_sector


def test_caes_merosur_special_divisions_are_mapped():
    result = provisional_sector(pd.Series(["4000", "4501", "4803", "9999", "0019"]))
    assert result.iloc[0] == "Construcción"
    assert result.iloc[1] == "Comercio"
    assert result.iloc[2] == "Comercio"
    assert result.iloc[3] == "Organismos extraterritoriales"
    assert result.iloc[4] == "No clasificado"
