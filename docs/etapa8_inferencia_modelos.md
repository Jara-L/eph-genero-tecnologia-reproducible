# Etapa 8 — Inferencia estadística y modelos multinomiales

## Estado de validación

La lectura directa de los miembros individuales de los cuatro ZIP oficiales reproduce exactamente 178.474 registros, 79.222 registros del universo amplio y 73.863 del universo estricto corregido. No se modificaron los ZIP originales.

La reconciliación de los tres conteos históricos es:

| Conjunto | n | Relación con el conjunto corregido |
|---|---:|---|
| Universo histórico con prefijo sectorial, 74.221 | 74.221 | 73.863 comunes + 358 casos `PP04B_COD=9999` |
| Tecnología estricta válida, 74.017 | 74.017 | 73.863 comunes + 154 códigos `00xx` sin sector asignable |
| Universo sectorial corregido, 73.863 | 73.863 | intersección común |

Los 358 casos excluidos al pasar del conteo histórico al corregido no son fallas tecnológicas: tienen clasificación CNO válida, pero `PP04B_COD=9999`, inválido para CAES. Los 154 casos tecnológicos que no ingresan al universo corregido corresponden a códigos `00xx`; se conservaron en los microdatos y se excluyeron sólo del análisis sectorial por falta de asignación oficial verificable. La cobertura, la frecuencia trimestral y la lista completa se encuentran en `universe_excluded_358_detail.csv` y en los productos de Etapa 7.

Los 13 códigos `00xx` observados se mantienen sin imputación de sector. `9999` tampoco se asigna a un sector. En consecuencia, la clasificación tecnológica y la clasificación sectorial son dimensiones distintas.

## Repetición y dependencia

El bootstrap usa vivienda (`household_id`) como conglomerado y remuestrea la vivienda completa, conservando conjuntamente sus registros de los cuatro trimestres cuando están presentes. En la muestra analítica hay 31.122 viviendas y 73.863 registros. La distribución detallada de viviendas, hogares y candidatos de persona, tanto para la EPH completa como para la muestra analítica, está en `repetition_distribution_full_and_analytic.csv`.

La coincidencia de `CODUSU`, hogar y componente es sólo un identificador candidato: no prueba identidad individual. El procedimiento no reproduce el diseño complejo completo de EPH porque los microdatos públicos utilizados no aportan en esta extracción los estratos y las unidades primarias necesarios para una varianza de encuesta completa. Los intervalos de Kitagawa son, por tanto, intervalos de sensibilidad por conglomerados, no errores estándar oficiales de INDEC.

## Kitagawa e incertidumbre

La descomposición simétrica usa `PONDERA/4`, que corresponde al estimando de razón entre los promedios de numerador y denominador trimestrales cuando se agrupan los cuatro trimestres. Con semilla `20261013` y 300 réplicas por vivienda no hubo réplicas descartadas.

| Resultado | Brecha pp | IC bootstrap 95% | Intersectorial pp | IC 95% | Intrasectorial pp | IC 95% |
|---|---:|---:|---:|---:|---:|---:|
| Sistemas informatizados | 10,01 | 8,94–11,24 | −2,85 | −3,93–−1,78 | 12,91 | 11,38–14,48 |
| Operación de máquinas | −13,81 | −14,70–−13,11 | −6,08 | −6,68–−5,54 | −7,76 | −8,57–−6,99 |

Las cifras puntuales de Etapa 7 fueron +10,01/−2,82/+12,83 para sistemas y −13,81/−6,08/−7,72 para maquinaria. Las pequeñas diferencias de los promedios bootstrap no son nuevas estimaciones puntuales; la identidad matemática se verifica en cada réplica.

La sensibilidad de estimandos muestra diferencias pequeñas entre la razón de promedios y el promedio de porcentajes trimestrales, inferiores a 0,003 puntos porcentuales en los cuatro cruces sexo–resultado. Los resultados publicados de Etapa 7 corresponden a la razón de sumas ponderadas, equivalente a `PONDERA/4` al agrupar.

## Modelos multinomiales

Se implementaron M1 (sexo, educación, edad centrada, edad al cuadrado y trimestre), M2 (M1 más macrosector) y M3 (M2 más interacciones sexo×macrosector). La categoría de referencia es la ocupación no tecnológica; las alternativas son operación de máquinas y operación de sistemas informatizados. La macroclasificación se usa para evitar celdas excesivamente pequeñas; no reemplaza la clasificación CAES detallada para las tablas descriptivas.

La función de verosimilitud multinomial ponderada se programó explícitamente con `scipy.optimize`, normalizando los pesos sólo para mejorar la escala numérica. Esto preserva el máximo de verosimilitud ponderada, pero no produce por sí solo una varianza de encuesta. Las probabilidades se estandarizan marginalmente sobre la población analítica común y se reportan por sexo. Los resultados y diagnósticos están en `multinomial_coefficients.csv` y `multinomial_diagnostics_and_standardized_predictions.csv`.

Los tres ajustes convergieron con `L-BFGS-B`, las probabilidades suman uno y no se observó pérdida de soporte en las categorías. Se consideran todavía resultados exploratorios, no estimaciones inferenciales finales, porque no se incorporó una varianza completa del diseño. No se forzó la convergencia, no se eliminaron sectores para obtener significación y no se reportan valores p. La comparación sustantiva debe basarse en probabilidades marginales y brechas ajustadas, no en cambios mecánicos de coeficientes logit entre modelos por no colapsabilidad.

## Decisión metodológica

La descomposición descriptiva es reproducible y admite una evaluación de incertidumbre razonable como sensibilidad por viviendas. La inferencia definitiva del artículo requiere, antes de interpretar significación, acceder a la información completa del diseño de EPH o justificar un estimador de varianza alternativo. Los modelos multinomiales pueden conservarse como etapa exploratoria una vez resueltos los diagnósticos de convergencia y separación; no se presentan aquí como evidencia causal.

### Productos

- `raw_reproduction.json`
- `universe_reconciliation.csv`
- `repetition_distribution_full_and_analytic.csv`
- `kitagawa_point_estimates.csv`
- `kitagawa_bootstrap_ci.csv`
- `kitagawa_bootstrap_replicates.csv`
- `estimand_sensitivity.csv`
- `multinomial_coefficients.csv`
- `multinomial_diagnostics_and_standardized_predictions.csv`

Todos se regeneran con `projects/mas-alla-educacion/scripts/run_stage8_inference.py` y permanecen fuera de Git mediante las reglas existentes para `reports/generated`.
