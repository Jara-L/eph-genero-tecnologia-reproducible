# Correspondencia entre código y resultados

| Etapa | Script | Resultados incluidos |
|---|---|---|
| 5 | `run_joint_eph_audit.py` | `data/processed/` y manifiesto local; no se distribuyen los datos. |
| 6 | `run_stage6_results.py` | `results/stage6/tabla_*.csv`, `figura_*.png`. |
| 7 | `run_stage7_decomposition.py` | `results/stage7/decomposition_summary.csv`, controles, contribuciones y figuras Kitagawa. |
| 8 | `run_stage8_inference.py` | Parte de los diagnósticos y probabilidades agregadas en `results/stage9/`. |
| 9 / 9B | `run_stage9_validation.py` | Estimaciones puntuales, IC agregados, brechas educativas, diagnósticos y figuras en `results/stage9/`. |

No se incluyen predicciones individuales, microdatos, ZIP de revisión, notebooks históricos ni archivos de inventario local.
