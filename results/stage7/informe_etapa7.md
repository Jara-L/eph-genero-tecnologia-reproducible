# Etapa 7 — descomposición de brechas tecnológicas

La auditoría reproduce 79,222 registros del universo amplio y 73,863 del universo estricto. La secuencia completa está en `universe_filter_sequence.csv`.

La descomposición simétrica usa `PONDERA/4` en la ventana agrupada y calcula, para cada resultado, la brecha mujeres − varones como suma exacta de componentes intersectorial e intrasectorial. La identidad se valida en `decomposition_summary.csv`; el error máximo debe ser numérico.

Los 64.030 identificadores candidatos repetidos y 128.060 registros de Etapa 6 corresponden a la EPH completa. Para la muestra analítica estricta, la distribución está en `repetition_distribution_analytical.csv`.

Los 13 códigos `00xx` se auditan en `caes_00xx_incidence_stage7.csv`, sin imputar sectores.

## Sensibilidad

Se estimaron descriptivamente las versiones agrupadas 2025-T2–2026-T1, sólo 2026-T1 y agrupada con macrosectores. No se estimaron intervalos ingenuos: la inferencia recomendada requiere errores agrupados por vivienda, controles por trimestre y sensibilidad a la rotación.

## Interpretación

El componente intersectorial resume cuánto cambiaría la brecha si mujeres y varones conservaran sus tasas sectoriales pero compartieran distribuciones sectoriales; el componente intrasectorial resume diferencias tecnológicas dentro de sectores bajo la distribución sectorial simétrica. No son efectos causales.

## Modelos pendientes

Se preparan modelos multinomiales base, con sector e interacciones sexo × sector. La comparación principal deberá usar probabilidades marginales estandarizadas y brechas predichas, no comparar mecánicamente coeficientes entre modelos por no colapsabilidad. No se ejecutaron estimaciones definitivas.

Pruebas específicas de identidad, denominadores, orden sectorial y ponderación acompañan el código en `tests/`.
