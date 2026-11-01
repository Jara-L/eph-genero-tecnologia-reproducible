# Etapa 6 — validación final y primeros resultados sectoriales

Esta etapa usa la base derivada `data/processed/eph_harmonized_2025T2_2026T1.csv`, generada por la auditoría de Etapa 5. Los microdatos originales permanecen fuera de Git.

## Universo y reconciliación

La cifra de 79.222 de Etapa 5 corresponde a:

`ESTADO = 1` AND `CH06 > 14` AND CNO con formato válido de cinco dígitos AND CAES con formato válido de cuatro dígitos.

Es decir, “clasificación tecnológica válida” se había usado allí en un sentido amplio de CNO válido. Para resultados tecnológicos estrictos se exige además que el cuarto dígito del CNO sea 1, 2 o 3, que son las tres categorías SIMEL/IATA. También se exige CNO válido, CAES válido y sector CAES asignable; los 13 códigos `00xx` se excluyen de la agrupación sectorial y se reportan aparte.

| Trimestre | Registros originales | Ocupados | Ocupados ≥15 | Tecnología válida estricta | Sector válido | Ambas | Muestra final |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2025-T2 | 46.086 | 20.374 | 20.372 | 19.024 | 20.241 | 18.915 | 18.915 |
| 2025-T3 | 44.946 | 20.066 | 20.058 | 18.767 | 19.837 | 18.587 | 18.587 |
| 2025-T4 | 43.703 | 19.698 | 19.689 | 18.316 | 19.543 | 18.200 | 18.200 |
| 2026-T1 | 43.739 | 19.573 | 19.565 | 18.268 | 19.442 | 18.161 | 18.161 |
| **Total** | **178.474** | **79.711** | **79.684** | **74.375** | **79.063** | **73.863** | **73.863** |

Los porcentajes de validez tienen como denominador el total de ocupados de 15 años y más de cada trimestre. La muestra final estricta corregida de 73.863 es, por tanto, la base de las tablas sectoriales. La cifra amplia 79.222 sigue preservada y auditada, pero no se la interpreta como tecnología categorizada.

Para T4-2025, SIMEL reporta 18.324 observaciones con etiqueta tecnológica. El recuento estricto antes del filtro etario también es 18.324; la diferencia frente a los 18.316 dentro de ocupados de 15 años y más son 8 ocupados de 12–14 años. La muestra sectorial final corregida de T4-2025 es 18.200: se excluyen CAES inválidos, incluidos códigos `9999`, además de los códigos no asignables.

Los 247 casos `CH06=-1` de T4-2025 son no ocupados, no tienen edad válida y no entran en ningún denominador analítico. Se conservan como código original y se excluyen por `CH06 > 14`, de acuerdo con el universo definido; no se eliminan físicamente.

## Rotación e identificadores

El diseño oficial describe `CODUSU` como identificador de vivienda con posibilidad de seguimiento, `NRO_HOGAR` como identificador de hogar y `COMPONENTE` como número de orden de la persona. En la ventana:

| Unidad candidata | Identificadores únicos | En 1 trimestre | En 2 trimestres | Registros en claves repetidas |
|---|---:|---:|---:|---:|
| Vivienda/hogar (`CODUSU|NRO_HOGAR`) | 40.319 | 17.628 | 22.691 | 130.963 |
| Persona candidata (`CODUSU|NRO_HOGAR|COMPONENTE`) | 114.444 | 50.414 | 64.030 | 128.060 |

No aparecen claves candidatas en tres o cuatro trimestres en esta extracción. La coincidencia no se interpreta como identidad individual cierta: puede reflejar rotación, cambios de composición o reutilización/asignación de componentes. Los archivos `repetition_distribution_household.csv` y `repetition_distribution_person_candidate.csv` dejan la distribución auditable.

El estimando agregado recomendado es el promedio temporal de las cuatro estimaciones trimestrales de la población ocupada de 15 años y más. Para ese estimando, `PONDERA/4` en la base apilada equivale a promediar las cuatro poblaciones trimestrales: la suma ponderada de la muestra final es 12.453.768. Esto no convierte las cuatro muestras en una única población ni elimina la dependencia por rotación.

La inferencia posterior debe usar, como mínimo, errores robustos agrupados por vivienda (`CODUSU`) y estratificación/región cuando estén disponibles. El ajuste de libertad efectiva y varianza de la EPH no se reproduce íntegramente con estos microdatos públicos porque no se dispone aquí de todos los estratos, réplicas o factores de expansión para cada estimación. Se informará esta limitación y se hará sensibilidad con errores robustos por vivienda, por trimestre y, si se incorporan variables de diseño oficiales, con el diseño completo.

## Clasificación sectorial

`PP04B_COD` se conserva como texto de cuatro dígitos y se mapea por división CAES-Mercosur 1.0. La tabla auditable completa es `caes_code_sector_mapping_auditable.csv`; no se confunde con `PP04D_COD`, que clasifica ocupaciones y determina la categoría tecnológica.

Los códigos sin correspondencia sectorial son:

| Código | Casos | Ponderación | Trimestres |
|---|---:|---:|---|
| 0019 | 1 | 785 | 2025-T4 |
| 0020 | 2 | 760 | 2025-T4 |
| 0026 | 1 | 5.404 | 2025-T4 |
| 0035 | 2 | 589 | 2025-T3 |
| 0045 | 47 | 26.535 | 2025-T2–2026-T1 |
| 0048 | 78 | 54.184 | 2025-T3, 2026-T1 |
| 0049 | 1 | 204 | 2025-T3 |
| 0056 | 5 | 2.337 | 2025-T3, 2026-T1 |
| 0070 | 1 | 630 | 2025-T3 |
| 0073 | 1 | 821 | 2025-T3 |
| 0081 | 2 | 2.011 | 2025-T3–2025-T4 |
| 0084 | 18 | 3.802 | 2025-T3 |
| 0095 | 12 | 9.784 | 2025-T3 |

Se recomienda mantenerlos como `No clasificado` y excluirlos de tablas sectoriales, con una categoría de sensibilidad que los reincorpore sólo si se confirma una regla oficial. No se asignan arbitrariamente a agricultura, construcción o comercio.

La agrupación principal para descriptivos es la de 20 sectores CAES agregados usada en las tablas. Para modelos se recomienda una versión más agregada, de 8–10 macrosectores, o conservar sólo sectores con celdas suficientes en la interacción sexo × tecnología. Las celdas con pocos casos se encuentran en `tabla_3_sector_sexo_tecnologia.csv`; no se fijó un umbral inferencial definitivo sin revisión científica.

## Primeros resultados descriptivos

Las cinco tablas completas, con conteos no ponderados, totales ponderados y porcentajes ponderados, están en `reports/generated/stage6_results/`:

1. `tabla_1_sector_sexo.csv`: composición sectorial del empleo por sexo; el denominador de cada porcentaje es el total ponderado del sector.
2. `tabla_2_sector_tecnologia.csv`: tecnología dentro de sector; el denominador es el total ponderado del sector.
3. `tabla_3_sector_sexo_tecnologia.csv`: tecnología dentro de sector y sexo; el denominador es el total ponderado del sector × sexo. `tabla_3_brechas_tecnologia_por_sector.csv` calcula mujeres − varones en puntos porcentuales.
4. `tabla_4_educacion_sexo_tecnologia.csv`: educación dentro de sexo × tecnología; el denominador es el total ponderado de sexo × tecnología.
5. `tabla_5_trimestre_sector_tecnologia.csv` y `tabla_5_trimestre_tecnologia.csv`: estructura por trimestre; el denominador es el total ponderado del trimestre.

En el promedio temporal ponderado, la distribución tecnológica por sexo es:

| Sexo | No tecnológica | Operación de máquinas | Sistemas informatizados |
|---|---:|---:|---:|
| Varones | 52,99% | 18,42% | 28,59% |
| Mujeres | 56,79% | 4,61% | 38,60% |

Descriptivamente, las mujeres presentan mayor participación dentro de sistemas informatizados y menor dentro de operación de máquinas, condicionado al universo ocupado, edad y clasificaciones válidas. En la composición sectorial, educación, salud y hogares empleadores son los sectores con mayor proporción femenina; construcción, transporte, energía y agropecuario son predominantemente masculinos. Estas son composiciones condicionales, no probabilidades de inserción laboral ni efectos causales.

Gráficos principales:

- `figura_1_composicion_sectorial_sexo.png`
- `figura_2_tecnologia_por_sector.png`
- `figura_3_brecha_tecnologica_sector.png`

Fueron construidos con fondo blanco, escalas porcentuales comparables y paleta azul; la figura 3 muestra mujeres − varones en puntos porcentuales dentro de cada sector y categoría tecnológica.

## Preparación econométrica, sin estimación

1. **Descomposición descriptiva:** comparar composición sectorial y composición tecnológica por sexo, usando diferencias en puntos porcentuales y Oaxaca-Blinder sólo como extensión descriptiva, nunca como identificación causal automática.
2. **Logit multinomial base:** resultado `technology_category`; covariables sexo, educación, edad y período. Estimando: probabilidades poblacionales condicionales en el universo analítico estricto.
3. **Logit multinomial ampliado:** agregar sector CAES agregado y controles territoriales; reportar probabilidades predichas, no sólo coeficientes.
4. **Interacciones sexo × sector:** incluirlas sólo para sectores con soporte suficiente en las celdas tecnología × sexo; comparar especificaciones agregadas y detalladas.
5. **Resultados:** presentar probabilidades predichas y efectos marginales promedio por sexo, sector y educación, con intervalos compatibles con la estrategia de errores elegida.
6. **Sensibilidad:** T1-2026 solamente, ventana de cuatro trimestres con `PONDERA/4`, exclusión/reincorporación de `00xx` sólo como análisis de sensibilidad, y agrupación sectorial alternativa.

No se estimaron modelos definitivos. Persisten como decisiones pendientes el umbral de tamaño muestral, la especificación final de varianzas y la incorporación de 2025-T1.

## Reproducibilidad y Git

Comandos principales desde la raíz de esta distribución:

```powershell
$env:PYTHONPATH='src'
python projects/mas-alla-educacion/scripts/run_joint_eph_audit.py
python projects/mas-alla-educacion/scripts/run_stage6_results.py
python -m pytest -q
```

`data/raw/`, `data/processed/`, `reports/generated/`, CSV, PNG, ZIP, XLSX y credenciales están excluidos por `.gitignore`. El checkpoint debe versionar sólo scripts, módulos, tests, README y esta documentación.
