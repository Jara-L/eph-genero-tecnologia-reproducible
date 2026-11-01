# Cierre formal de la Etapa 9B

## 1. Objetivos

Este cierre consolida las etapas 7, 8, 9 y 9B del artículo **Más allá de la educación: estructura productiva y brechas de género en las ocupaciones tecnológicas argentinas**. El objetivo es dejar un flujo reproducible para: (i) definir el universo analítico, (ii) describir la composición sectorial de las ocupaciones tecnológicas, (iii) estimar modelos multinomiales exploratorios y (iv) separar descriptivamente los componentes intersectorial e intrasectorial de las brechas.

No se incorporan nuevos modelos ni cambios al estimando ya definido.

## 2. Fuentes y universo analítico

La fuente es la EPH armonizada para 2025-T2, 2025-T3, 2025-T4 y 2026-T1. El flujo parte de 178.474 registros individuales y aplica, en orden, ocupación, edad mínima de 15 años, validez de CNO, validez de CAES, clasificación tecnológica estricta y asignación sectorial.

El universo amplio contiene 79.222 registros; el universo tecnológico estricto, 74.017; y el universo analítico final, 73.863 registros. La reproducción directa desde los cuatro archivos de origen devuelve 73.863 registros estrictos, con diferencia cero respecto del CSV procesado. El universo analítico contiene 31.122 hogares.

La ponderación pooled es `PONDERA/4`, consistente con el promedio de los cuatro trimestres.

## 3. Definición de variables

La categoría tecnológica se construye con el cuarto dígito de CNO: categoría 1, no tecnológica; categoría 2, operación de máquinas; categoría 3, operación de sistemas informatizados. El sexo, educación, trimestre y sector se mantienen como variables categóricas con un esquema de niveles fijado en la muestra de entrenamiento.

La referencia para las predicciones marginales es común a ambos sexos: cada fila elegible se evalúa una vez con `sex=1` y otra con `sex=2`, manteniendo fijas las demás covariables y usando el mismo peso `PONDERA/4`.

## 4. Descomposición sectorial

La descomposición de Kitagawa usa la identidad simétrica:

\[
G = \sum_s (q_{s,f}p_{s,f}-q_{s,m}p_{s,m}) = I_{sectorial}+I_{intra}.
\]

La especificación detallada utiliza 19 sectores y la sensibilidad utiliza 11 macrosectores. En el universo pooled de cuatro trimestres, la descomposición detallada produce una brecha de **+10,01 pp en sistemas** y **−13,81 pp en máquinas**; los componentes intersectoriales son, respectivamente, **−2,82 pp** y **−6,08 pp**, y los intrasectoriales **+12,83 pp** y **−7,72 pp**. Los errores de identidad son numéricamente nulos.

En el bootstrap de soporte fijo se obtuvieron **835 réplicas válidas de 1.000** para 19 sectores. Las 165 restantes se descartaron porque alguna celda sector×sexo perdió soporte positivo; no se imputaron tasas ni se mezclaron con otro estimando. Para 11 macrosectores se obtuvieron 1.000 réplicas válidas.

La clasificación macrosectorial cambia la partición de los componentes, aunque no la brecha agregada: en sistemas el componente intersectorial es aproximadamente −1,04 pp y en máquinas −5,35 pp. Las diferencias reflejan la agregación sectorial, no una nueva estimación causal.

## 5. Especificaciones M1, M2 y M3

- **M1:** sexo, edad centrada, edad al cuadrado, educación y trimestre.
- **M2:** M1 más macrosector.
- **M3:** M2 más interacciones sexo×macrosector.

Los modelos son multinomiales ponderados por pseudomáxima verosimilitud, con categoría no tecnológica como referencia. Se verifican identificación, convergencia, rango completo de las matrices de diseño y ausencia de colinealidad exacta. Las columnas categóricas usadas para predecir son las mismas que las usadas para ajustar.

## 6. Resultados descriptivos, ajustados e inferencia

Los resultados descriptivos corresponden a tasas ponderadas y a la descomposición sectorial; no controlan por covariables. Las estimaciones ajustadas corresponden a probabilidades contrafactuales marginales de M1–M3 sobre la población de referencia común. La inferencia estadística es limitada: los intervalos por vivienda son una aproximación exploratoria y no equivalen a errores estándar oficiales de la EPH.

Las cifras puntuales corregidas, calculadas directamente a partir del ajuste actual y de la referencia común, son:

| Modelo | Máquinas, mujeres−varones | Sistemas, mujeres−varones |
|---|---:|---:|
| M1 | −12,3519 pp | +2,1394 pp |
| M2 | −7,4277 pp | +3,3692 pp |
| M3 | −7,3597 pp | +6,3286 pp |

Las medias del bootstrap exploratorio de 60 réplicas son −12,4238/+2,1527 pp en M1, −7,4453/+3,4106 pp en M2 y −7,3736/+6,3763 pp en M3. La diferencia entre ambas filas de resultados es esperable: una es la estimación puntual del ajuste original y la otra resume la distribución de los ajustes remuestreados.

El bootstrap multinomial de **60 réplicas por vivienda** conserva carácter exploratorio. No debe presentarse como una estimación completa de la varianza del diseño complejo.

## 7. Correcciones materiales

Se corrigieron: (i) la estandarización marginal sobre las mismas filas de referencia para ambos sexos; (ii) el uso consistente de `PONDERA/4`; (iii) la reutilización del esquema categórico completo después de filtrar educación; (iv) la conservación de soporte fijo en la descomposición detallada; y (v) la exclusión de predicciones fila a fila del paquete de revisión.

## 8. Pruebas de reproducibilidad

La suite validada contiene 26 pruebas aprobadas. Verifica el universo de 73.863 registros, las reconciliaciones 74.221/74.017/73.863, la escala `PONDERA/4`, las identidades de Kitagawa, denominadores, soporte, categorías, referencia contrafactual común, suma de probabilidades a uno y reproducibilidad del bootstrap pequeño.

La ejecución completa de Etapas 7 y 8 se reprodujo desde el código y los microdatos locales. La ejecución 9B se corre con semilla fija `20261013`; sus diagnósticos deben conservar rango completo 13/13, 23/23 y 33/33, convergencia de M1–M3 y errores de suma de probabilidades próximos a cero.

## 9. Limitaciones metodológicas

El análisis es asociacional y no identifica efectos causales de educación, sector o sexo. La pseudomáxima verosimilitud ponderada no reemplaza un estimador de encuesta. El bootstrap por vivienda preserva la agrupación longitudinal de las filas observadas, pero no incorpora completamente estratos ni unidades primarias de muestreo de la EPH; por ello sus intervalos son aproximados y exploratorios. La pérdida de soporte en 165 réplicas detalladas impide interpretar ese conjunto como una incertidumbre regularizada sobre todos los remuestreos posibles.

## 10. Estado de validación y tareas para el artículo

La ejecución 9B finalizó sin diferencias materiales respecto de los diagnósticos registrados. Permanecen como tareas editoriales: redactar la sección de datos y métodos, explicar la elección de la clasificación sectorial, presentar por separado resultados descriptivos y ajustados, y formular las limitaciones de inferencia en el texto principal.

No se recomienda iniciar nuevas especificaciones econométricas en esta etapa.
