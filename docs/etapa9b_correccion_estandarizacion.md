# Etapa 9B — Corrección de estandarización e incertidumbre

## Correcciones aplicadas

Se corrigieron tres problemas de la versión externa:

1. Las probabilidades marginales ahora se calculan contrafactualmente sobre las mismas filas de referencia para ambos sexos y con sus ponderadores `PONDERA/4`.
2. El esquema de dummies se define una sola vez sobre la muestra de entrenamiento y se reutiliza en todas las predicciones, incluso después de filtrar un nivel educativo.
3. El bootstrap sectorial utiliza soporte fijo. Las réplicas detalladas que pierden una celda sector×sexo se registran como inválidas y no se combinan con réplicas de un estimando distinto. La sensibilidad macrosectorial tiene soporte completo.

La primera versión de las predicciones econométricas no debe utilizarse. Los coeficientes se conservaron porque superaron las verificaciones de identificación, convergencia, gradiente y estabilidad de inicialización; las probabilidades y brechas fueron regeneradas.

## Soporte sectorial

Con 1.000 réplicas:

| Esquema | Réplicas válidas | Inválidas | Motivo |
|---|---:|---:|---|
| 19 sectores detallados | 835 | 165 | pérdida de soporte sector×sexo |
| 11 macrosectores | 1.000 | 0 | — |

No se imputaron tasas sectoriales. Para los 19 sectores se reporta el estimando definido por soporte completo; para sensibilidad se reporta la agrupación macrosectorial.

Resultados detallados, 835 réplicas válidas:

| Resultado | Brecha pp | IC 95% |
|---|---:|---:|
| Sistemas | 10,01 | 8,90–11,22 |
| Intersectorial, sistemas | −2,81 | −4,06–−1,59 |
| Intrasectorial, sistemas | 12,82 | 11,21–14,42 |
| Máquinas | −13,81 | −14,65–−13,01 |
| Intersectorial, máquinas | −6,08 | −6,67–−5,52 |
| Intrasectorial, máquinas | −7,74 | −8,59–−6,99 |

En la sensibilidad macrosectorial, las brechas son 10,04 pp para sistemas y −13,84 pp para máquinas. El componente intersectorial de sistemas cambia a −1,04 pp y el de máquinas a −5,35 pp; esto muestra que la magnitud del componente depende de la agregación sectorial.

## Estandarización marginal

Para cada modelo se usa una población de referencia común: cada observación analítica elegible se evalúa dos veces, una con sexo varón y otra con sexo mujer. La media se pondera por `PONDERA/4`. Por educación, la referencia común se restringe al nivel educativo correspondiente, pero sigue incluyendo las mismas filas para ambos contrafactuales. Las columnas categóricas permanecen fijas entre entrenamiento y predicción.

Las nuevas brechas agregadas ajustadas y sus bootstrap exploratorios son:

| Modelo | Máquinas, brecha | IC 95% | Sistemas, brecha | IC 95% |
|---|---:|---:|---:|---:|
| M1 | −12,42 pp | −13,14–−11,59 | 2,15 pp | 1,10–3,25 |
| M2 | −7,45 pp | −8,01–−6,62 | 3,41 pp | 2,33–4,15 |
| M3 | −7,37 pp | −7,96–−6,67 | 6,38 pp | 5,40–7,38 |

Se utilizaron 60 réplicas por vivienda para esta sensibilidad multinomial y no hubo fallos. Los intervalos no son errores estándar oficiales de EPH: la pseudomáxima verosimilitud ponderada y el bootstrap por vivienda no incorporan estratos ni unidades primarias del diseño complejo.

## Educación

Las tablas corregidas se encuentran en `brechas_ajustadas_por_educacion.csv`. La estandarización fija las columnas de educación, trimestre y sector antes de filtrar cada nivel. En M1, la brecha de máquinas permanece negativa en todos los niveles; al incorporar sectores, la magnitud se reduce. Las brechas de sistemas aumentan en M2 y especialmente en M3, lo que describe asociaciones condicionales heterogéneas, no retornos causales de la educación.

## Diagnósticos y reproducibilidad

Las matrices finales tienen rangos completos 13/13, 23/23 y 33/33 y números de condición aproximados de 66,4; 66,7 y 115,9. Las inicializaciones alternativas convergieron; las diferencias máximas de coeficientes fueron 0,00021, 0,00012 y 0,00058. Las dummies educativas y sectoriales se generan con el esquema fijo compartido entre ajuste y predicción.

El paquete externo actualizado excluye `multinomial_individual_predictions.csv` y cualquier microdato o predicción fila-a-fila.
