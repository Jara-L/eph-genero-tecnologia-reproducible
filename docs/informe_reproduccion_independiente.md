# Informe final de reproducción independiente

Fecha: 2026-11-01. Distribución independiente derivada del código publicado en `5355f9e`; el repositorio original no fue modificado.

## Entorno

Se creó un entorno virtual separado en `.venv_repro`. Python administrado por `uv` no pudo descargarse por un certificado de la red local, por lo que el entorno aislado utilizó Python 3.13.9 disponible en el equipo, con `site-packages` independiente de Anaconda. Las versiones instaladas fueron:

```text
Python 3.13.9
numpy 2.3.5
pandas 2.3.3
scipy 1.16.3
statsmodels 0.14.5
scikit-learn 1.7.2
matplotlib 3.10.6
openpyxl 3.1.5
patsy 1.0.1
pytest 8.4.2
```

La especificación está en `requirements-public.txt`; las dependencias transitivas se instalaron automáticamente y no deben incluirse en una publicación manual.

## Ejecución desde fuentes originales

Se copiaron temporalmente, en modo solo lectura, los cuatro ZIP EPH desde la carpeta local de microdatos. No se modificaron los originales. El flujo reconstruyó:

- 178.474 registros individuales originales;
- 79.222 registros del universo amplio;
- 73.863 registros del universo estricto final;
- 31.122 hogares analíticos;
- ponderación pooled `PONDERA/4` con suma 12.388.759,25.

La comparación directa entre los ZIP y el CSV armonizado produjo diferencia cero. También se reprodujeron las tablas sectoriales y la identidad algebraica de Kitagawa.

## Modelos multinomiales

Las probabilidades estandarizadas se calcularon sobre las mismas 73.863 filas de referencia y con los mismos pesos para ambos sexos. Las brechas obtenidas fueron:

| Modelo | Maquinaria (pp) | Sistemas informatizados (pp) | Diferencia máxima frente a 9B |
|---|---:|---:|---:|
| M1 | -12,35185 | +2,13939 | 0,000052 pp |
| M2 | -7,42773 | +3,36919 | 0,000034 pp |
| M3 | -7,35972 | +6,32850 | 0,000104 pp |

Los tres modelos convergieron. Las iteraciones fueron M1: 339, M2: 394 y M3: 694; el error máximo de suma de probabilidades fue inferior a `3.4e-16` en los diagnósticos de ajuste y menor que `1e-14` en la tabla final por redondeo numérico.

## Kitagawa y bootstrap

Para 19 sectores, las estimaciones puntuales fueron:

- sistemas informatizados: **+10,008553 pp**;
- maquinaria: **−13,807850 pp**.

El esquema detallado produjo 835 réplicas válidas y 165 fallas por falta de soporte sectorial; el esquema de 11 macrosectores produjo 1.000 réplicas válidas. El bootstrap multinomial generó exactamente 60 réplicas por modelo, con 60/60 convergentes en M1, M2 y M3.

Las 60 réplicas son una sensibilidad exploratoria. No representan una estimación definitiva de la varianza del diseño complejo de la EPH.

## Pruebas

Con los datos procesados y las salidas generadas por el propio pipeline, la suite ejecutada en el entorno independiente fue:

```text
26 passed, 14 warnings
```

Las advertencias provienen de APIs deprecadas de `pyparsing` usadas internamente por Matplotlib; no afectan los resultados numéricos.

## Incidencia corregida

La primera ejecución falló porque el auditor exigía `data/raw/usu_individual_T425.xlsx`, un archivo auxiliar no incluido en las instrucciones y no necesario para procesar los cuatro ZIP. En la distribución independiente se hizo opcional esa comparación: si el XLSX auxiliar está presente se verifica su coincidencia; si no, el pipeline continúa únicamente con los cuatro ZIP documentados.

## Dictamen

La distribución reproduce íntegramente los resultados determinísticos y las estimaciones puntuales M1–M3 de la Etapa 9B, dentro de precisión numérica razonable, y ejecuta los bootstrap implementados con sus semillas y cantidades de réplicas. Antes de publicar deben retirarse el entorno virtual, los ZIP y `reports/generated/` de trabajo, confirmar los metadatos de autoría y aprobar una licencia.
