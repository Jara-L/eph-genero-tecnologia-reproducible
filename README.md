# Más allá de la educación: estructura productiva y brechas de género en las ocupaciones tecnológicas argentinas

Repositorio de código reproducible para el artículo sobre estructura productiva, educación y brechas observadas por sexo en las ocupaciones tecnológicas de Argentina.

## Autores y afiliación

- Luciano Andrés Jara Musuruana — [ORCID 0000-0002-0203-180X](https://orcid.org/0000-0002-0203-180X).
- Natalia B. Calcabrini — ORCID y afiliación institucional: por confirmar por la autora.

La afiliación institucional no se completa porque no está comprobada en los metadatos públicos de este repositorio.

## Alcance y datos

El flujo usa las bases oficiales de microdatos de la Encuesta Permanente de Hogares (EPH) del INDEC:

- [Bases y documentos EPH del INDEC](https://www.indec.gob.ar/indec/web/Institucional-Indec-BasesDeDatos-1)
- [Diseño de registro y estructura de la base](https://www.indec.gob.ar/ftp/cuadros/menusuperior/eph/EPH_disenoreg_09.pdf)

La ventana analítica es 2025-T2, 2025-T3, 2025-T4 y 2026-T1. El universo final comprende personas ocupadas de 15 años o más, con CNO y CAES válidos, categoría tecnológica válida y sector CAES asignable. La tecnología se clasifica con el cuarto dígito de `PP04D_COD`: no tecnológica, operación de máquinas y operación de sistemas informatizados. El sector se deriva de `PP04B_COD` mediante la agregación documentada en `src/eph_genero_tecnologia/sector.py`.

La ventana apilada usa `PONDERA/4` para representar el promedio temporal de los cuatro trimestres. Los identificadores públicos se usan para auditar repetición por vivienda/hogar; no se interpreta `COMPONENTE` como identidad individual estable.

## Métodos

El flujo incluye auditoría de fuentes y códigos, armonización individual-hogar, tablas ponderadas, descomposición descriptiva de Kitagawa y modelos multinomiales exploratorios para las tres categorías tecnológicas con probabilidades estandarizadas. Las estimaciones son descriptivas o asociativas, no efectos causales. Los intervalos producidos por bootstrap no son errores oficiales de encuesta.

## Instalación y ejecución

Se requiere Python 3.11–3.13. Desde la raíz, en PowerShell:

```powershell
uv sync
$env:PYTHONPATH = "src"
uv run python projects/mas-alla-educacion/scripts/run_joint_eph_audit.py
uv run python projects/mas-alla-educacion/scripts/run_stage6_results.py
uv run python projects/mas-alla-educacion/scripts/run_stage7_decomposition.py
uv run python projects/mas-alla-educacion/scripts/run_stage8_inference.py
uv run python projects/mas-alla-educacion/scripts/run_stage9_validation.py
uv run pytest -q
```

Descargue manualmente desde INDEC estos ZIP en `data/raw/`:

```text
EPH_usu_2_Trim_2025_xls.zip
EPH_usu_3_Trim_2025_xls.zip
EPH_usu_4_Trim_2025_xls.zip
EPH_usu_1_Trim_2026_xls.zip
```

Las fuentes, los datos derivados y `reports/generated/` están excluidos de Git. El primer script genera el manifiesto y `data/processed/eph_harmonized_2025T2_2026T1.csv`; las etapas siguientes generan tablas y figuras en `reports/generated/`. El código resuelve la raíz desde cada script; no necesita una ruta absoluta de Windows. En otro entorno, defina `PYTHONPATH=src` o instale el paquete editable.

## Resultados esperados y pruebas

La ejecución auditada reprodujo 178.474 registros, 79.222 observaciones del universo amplio y 73.863 del universo estricto final; la comparación entre fuentes originales y CSV procesado dio diferencia cero. La suite automatizada obtuvo **26 pruebas aprobadas** y cubre variables, calidad, sector, etapas 6–9 y denominadores.

## Limitaciones

- Los microdatos no se redistribuyen; deben obtenerse del INDEC.
- La afiliación y el ORCID de Natalia B. Calcabrini requieren confirmación.
- No se dispone aquí de todos los estratos, réplicas o factores para reproducir íntegramente la varianza oficial de la EPH.
- La descomposición depende de la agrupación sectorial y los modelos son sensibles al soporte de las celdas.
- La variable observada es `CH04` (sexo registrado); “género” es el marco sustantivo del artículo.
- La portabilidad con un intérprete CPython independiente de Anaconda permanece pendiente por un bloqueo de certificados TLS; el estado está documentado en `docs/informe_portabilidad.md`.

## Licencia y citación

El código científico de este repositorio se distribuye bajo la licencia [BSD-3-Clause](LICENSE). Los microdatos EPH no se redistribuyen: deben obtenerse directamente del [INDEC](https://www.indec.gob.ar/). La licencia del código no modifica los derechos de terceros sobre los microdatos, las fuentes, los datos derivados ni otros materiales. Para citar el software, consulte [`CITATION.cff`](CITATION.cff). Cite los datos como “Fuente: Instituto Nacional de Estadística y Censos (INDEC)”, indicando período y base EPH.

---

# Beyond education: productive structure and gender gaps in Argentine technology occupations

This repository contains reproducible code for the article on productive structure, education, and observed sex gaps in technology occupations in Argentina.

The project uses official INDEC EPH microdata for 2025-Q2 through 2026-Q1. Download the four ZIP files listed above into `data/raw/`, then run the commands in the Spanish instructions. The pipeline creates ignored processed data and reports. It includes descriptive Kitagawa decomposition and exploratory multinomial models with standardized predictions. Results are descriptive or associational, not causal; official survey variance is not fully reproduced. Public-use microdata are not redistributed.

Author affiliation and Natalia B. Calcabrini’s ORCID remain to be confirmed. The scientific code in this repository is distributed under the [BSD-3-Clause license](LICENSE). The EPH microdata must be obtained from [INDEC](https://www.indec.gob.ar/); the software license does not change third-party rights in the microdata, source materials, derived data, or other materials. Consult [`CITATION.cff`](CITATION.cff) when citing the software.

## Portability status

The portability audit is documented in [`docs/informe_portabilidad.md`](docs/informe_portabilidad.md). The validated target is Python 3.11–3.13. A standalone CPython 3.14.4 is present on the validation machine, but it is outside the declared compatibility range. Downloading standalone CPython 3.13.9 with `uv 0.11.7` failed because the local network certificate was not trusted; TLS verification was not disabled.

The machine has no Python.org 3.13 installation. The audit also found inherited `SSL_CERT_FILE` and `SSL_CERT_DIR` values pointing to Anaconda; these must be corrected before resolving dependencies in a Python.org environment.
