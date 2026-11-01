# Etapa 7 — validación final y descomposición de brechas tecnológicas

## Corrección de universo

La auditoría de esta etapa detectó un error material en la definición estricta de Etapa 6. El total 74.221 había exigido tecnología categorizable y un prefijo sectorial, pero no había vuelto a exigir `caes_valid`; por eso incluyó 358 ocupados con `PP04B_COD=9999`, que el mapa por prefijo trataba superficialmente como `99`.

La definición corregida exige, sin doble conteo:

`ESTADO=1` → `CH06>14` → CNO válido → CAES válido → cuarto dígito CNO ∈ {1,2,3} → sector CAES asignable.

| Paso | Registros | Excluidos del paso anterior |
|---|---:|---:|
| Registros originales | 178.474 | 0 |
| Personas ocupadas | 79.711 | 98.763 |
| Ocupadas de 15 años y más | 79.684 | 27 |
| CNO válido | 79.645 | 39 |
| CAES válido: universo amplio | 79.222 | 423 |
| Tecnología estricta válida | 74.017 | 5.205 |
| Sector asignado: universo estricto | 73.863 | 154 |

Por lo tanto, 79.222 es el universo amplio y 73.863 es el universo estricto corregido. Los 64.030 identificadores candidatos repetidos y sus 128.060 registros asociados corresponden a la EPH completa; para el universo estricto, la distribución se encuentra en `repetition_distribution_analytical.csv`.

Los 13 códigos `00xx` se conservaron, pero no se asignaron a sectores. Además, `9999` se trata como CAES inválido y queda fuera del universo amplio; no debe mapearse por prefijo a organismos extraterritoriales.

## Denominadores

Se verificaron las cinco tablas de Etapa 6. Los denominadores son:

- sector × sexo: total ponderado dentro del sector;
- sector × tecnología: total ponderado dentro del sector;
- sector × sexo × tecnología: total ponderado dentro del sector × sexo;
- educación × sexo × tecnología: total ponderado dentro de sexo × tecnología;
- trimestre × sector × tecnología: total ponderado dentro del trimestre.

Todos los grupos suman 100% dentro de tolerancia numérica. El detalle está en `denominator_checks.csv`.

## Método de descomposición

Para cada categoría tecnológica `k`, se define `p_gs^k` como la proporción ponderada de la categoría dentro del sector `s` para el grupo de sexo `g`, y `q_gs` como la distribución sectorial del grupo `g` dentro del universo estricto. La brecha es `P_mujeres^k − P_varones^k`.

La descomposición simétrica usada es:

`Intersectorial = 1/2 Σ_s (q_mujeres,s − q_varones,s)(p_mujeres,s + p_varones,s)`

`Intrasectorial = 1/2 Σ_s (p_mujeres,s − p_varones,s)(q_mujeres,s + q_varones,s)`

Los ponderadores agrupados son `PONDERA/4`, que representan el promedio de las cuatro estimaciones trimestrales. No se imputan tasas para sectores sin soporte en ambos sexos; en esta extracción se usaron 19 sectores con soporte femenino y masculino. Las celdas pequeñas quedan marcadas en los archivos de soporte y no se eliminan automáticamente.

## Resultados agrupados 2025-T2–2026-T1

| Categoría | Mujeres (%) | Varones (%) | Brecha mujeres−varones (pp) | Intersectorial (pp) | Intrasectorial (pp) |
|---|---:|---:|---:|---:|---:|
| Sistemas informatizados | 38,50 | 28,49 | 10,01 | −2,82 | 12,83 |
| Operación de máquinas | 4,63 | 18,43 | −13,81 | −6,08 | −7,72 |

Las sumas de componentes reproducen la brecha con error menor a `4×10⁻¹⁵` puntos porcentuales.

Para sistemas informatizados, el componente intrasectorial es positivo y domina la brecha agregada; el componente intersectorial es negativo. Las mayores contribuciones intersectoriales negativas provienen de construcción y transporte, mientras que educación, salud y servicios profesionales aportan positivamente. Para maquinaria, ambos componentes son negativos; transporte, comercio e industria manufacturera son contribuyentes relevantes. Estas contribuciones son descriptivas y no efectos causales.

## Sensibilidad

| Ventana / agrupación | Resultado | Brecha pp | Intersectorial pp | Intrasectorial pp |
|---|---|---:|---:|---:|
| Cuatro trimestres | Sistemas | 10,01 | −2,82 | 12,83 |
| Cuatro trimestres | Máquinas | −13,81 | −6,08 | −7,72 |
| 2026-T1 | Sistemas | 9,34 | −1,49 | 10,82 |
| 2026-T1 | Máquinas | −13,49 | −6,26 | −7,23 |
| Cuatro trimestres, macrosectores | Sistemas | 10,01 | −1,04 | 11,05 |
| Cuatro trimestres, macrosectores | Máquinas | −13,81 | −5,35 | −8,46 |

El signo de las brechas es estable. La magnitud relativa de los componentes cambia con la agregación sectorial, por lo que los resultados deben presentarse como una descomposición descriptiva dependiente de la partición elegida.

## Inferencia y modelos pendientes

La rotación impide tratar todas las filas trimestrales como independientes. La estrategia mínima propuesta es varianza robusta agrupada por vivienda (`CODUSU`), con controles por trimestre y región; si se obtienen estratos, conglomerados y réplicas oficiales, se debe repetir con diseño complejo. No se afirma que el agrupamiento por vivienda reproduzca íntegramente la varianza EPH.

Los modelos todavía no se estiman. Se preparan: multinomial base con sexo, educación, edad y período; extensión con macrosector; e interacciones sexo × sector sólo donde exista soporte suficiente. La comparación sustantiva se hará mediante probabilidades marginales estandarizadas y brechas predichas, no mediante comparación mecánica de coeficientes logit entre modelos no colapsables.

## Archivos reproducibles

- `projects/mas-alla-educacion/scripts/run_stage7_decomposition.py`
- `reports/generated/stage7_decomposition/universe_filter_sequence.csv`
- `reports/generated/stage7_decomposition/decomposition_summary.csv`
- `reports/generated/stage7_decomposition/sector_contributions_pooled_4q_sector_provisional.csv`
- `reports/generated/stage7_decomposition/caes_00xx_incidence_stage7.csv`
- `reports/generated/stage7_decomposition/figura_1_componentes_kitagawa.png`
- `reports/generated/stage7_decomposition/figura_2_contribuciones_sectoriales.png`
