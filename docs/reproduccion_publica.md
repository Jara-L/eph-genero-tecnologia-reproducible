# Reproducción pública

Descargar desde la página oficial de [bases EPH del INDEC](https://www.indec.gob.ar/indec/web/Institucional-Indec-BasesDeDatos-1) los cuatro archivos XLS comprimidos y guardarlos en `data/raw/` con estos nombres:

```text
EPH_usu_2_Trim_2025_xls.zip
EPH_usu_3_Trim_2025_xls.zip
EPH_usu_4_Trim_2025_xls.zip
EPH_usu_1_Trim_2026_xls.zip
```

El repositorio público no contiene microdatos. El primer script genera `reports/generated/eph_joint_audit/source_manifest.json`, incluyendo tamaño, miembros y SHA-256 de cada fuente local.

## Secuencia

1. `run_joint_eph_audit.py`: inspección, lectura individual/hogar, armonización y CSV procesado.
2. `run_stage6_results.py`: tablas descriptivas y figuras sectoriales.
3. `run_stage7_decomposition.py`: universo, controles de denominadores y Kitagawa descriptivo.
4. `run_stage8_inference.py`: modelos multinomiales y bootstrap exploratorio.
5. `run_stage9_validation.py`: validaciones finales, probabilidades estandarizadas y diagnósticos.
6. `pytest -q`: pruebas unitarias y de etapas.

## Qué está validado

Las etapas 5–8 fueron reproducidas localmente desde los cuatro ZIP oficiales disponibles, con 178.474 filas de origen y 73.863 observaciones en el universo estricto final. La reproducción directa desde ZIP y el CSV armonizado coincidieron.

El paquete de resultados incluido corresponde a salidas agregadas de la validación 9B. La etapa 9 debe volver a ejecutarse en un clon limpio para certificar tiempos, hashes de código y coherencia completa de todas sus salidas; los resultados exportados se distribuyen para revisión, no como prueba de una ejecución integral limpia.

## Limitaciones

La inferencia no reproduce íntegramente el diseño complejo de la EPH: no se incluyen aquí todos los estratos, réplicas ni factores necesarios. El bootstrap agrupado por vivienda es exploratorio. La clasificación tecnológica depende del cuarto dígito CNO y la agregación sectorial depende de la correspondencia CAES documentada.
