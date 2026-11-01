# Etapa 9 — Validación econométrica y resultados finales 9B

## Estado de la corrección

Esta versión reemplaza las cifras históricas de Etapa 8 que usaban medias de predicciones de los grupos observados. Las probabilidades vigentes son predicciones contrafactuales estandarizadas: las mismas filas de una población de referencia común se evalúan alternativamente con sexo varón y sexo mujer, con ponderación `PONDERA/4`. Los intervalos y resultados educativos de la versión anterior no deben presentarse como vigentes.

No se modificó la metodología econométrica aprobada: M1 incluye sexo, educación, edad centrada, edad al cuadrado y trimestre; M2 agrega macrosectores; M3 agrega interacciones sexo×macrosector. La categoría de resultado de referencia es no tecnológica.

## Brechas marginales corregidas

| Modelo | Máquinas, mujeres−varones (pp) | Sistemas, mujeres−varones (pp) |
|---|---:|---:|
| M1 | −12,3519 | +2,1394 |
| M2 | −7,4277 | +3,3692 |
| M3 | −7,3597 | +6,3286 |

Estas son estimaciones puntuales del ajuste original. Las medias del bootstrap exploratorio de 60 réplicas por vivienda se presentan separadamente en `bootstrap_model_gaps_ci.csv`; no deben confundirse con las estimaciones puntuales ni describirse como 60 inicializaciones alternativas.

## Kitagawa con soporte fijo

La figura y las tablas distinguen la estimación puntual original de la media bootstrap. Se reportan dos estimandos sobre exactamente el mismo universo analítico: 19 sectores detallados, con 835 réplicas válidas de 1.000, y 11 macrosectores, con 1.000 réplicas válidas. Las réplicas detalladas sin soporte positivo sector×sexo se registran como inválidas; no se imputan tasas.

La brecha agregada reproducida es, para el esquema detallado, **+10,0086 pp en sistemas** y **−13,8079 pp en máquinas**. Al reagrupar los mismos registros en 11 macrosectores la brecha agregada se mantiene, dentro de la precisión numérica; cambian únicamente los componentes intersectorial e intrasectorial. `kitagawa_point_estimates.csv` contiene las estimaciones puntuales y `kitagawa_bootstrap_fixed_support_ci.csv` sus medias bootstrap e intervalos.

## Educación y frecuencia del nivel 7

Las denominaciones oficiales usadas en las tablas son: 1 Primario incompleto; 2 Primario completo; 3 Secundario incompleto; 4 Secundario completo; 5 Superior universitario incompleto; 6 Superior universitario completo; 7 Sin instrucción. El nivel 7 se conserva por fidelidad al código EPH, pero tiene baja frecuencia en el universo analítico; por ello sus probabilidades deben interpretarse con cautela.

## Unidades e incertidumbre

`household_id` identifica hogares; `person_candidate_id` identifica personas candidatas. El remuestreo de 9B se hace por `household_id`/vivienda identificada longitudinalmente y conserva sus filas trimestrales. “Vivienda” describe la unidad de remuestreo utilizada; no debe confundirse con el identificador de persona ni con una nueva unidad muestral oficial de la EPH.

Los intervalos son exploratorios: no incorporan estratos ni unidades primarias oficiales. No se presentan como errores estándar de diseño ni como resultados causales.

## Archivos vigentes

- `multinomial_standardized_predictions.csv`: probabilidades estandarizadas por sexo y modelo; no contiene predicciones individuales.
- `probabilidades_por_educacion_sexo_modelo.csv` y `brechas_ajustadas_por_educacion.csv`: resultados por denominación educativa oficial.
- `kitagawa_point_estimates.csv`, `kitagawa_bootstrap_fixed_support_ci.csv` y `kitagawa_bootstrap_fixed_support_replicates.csv`.
- `bootstrap_model_gaps_ci.csv`: medias e intervalos del bootstrap de 60 réplicas, separados de las estimaciones puntuales.
- `figura_1_kitagawa_ic.png` y `figura_2_probabilidades_marginales.png`: figuras finales generadas desde esas tablas.

El paquete académico excluye microdatos y predicciones individuales.
