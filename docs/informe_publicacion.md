# Informe de preparación de la distribución pública

Fecha: 2026-11-01. Esta carpeta es una distribución independiente preparada a partir del commit publicado `5355f9e`; no contiene `.git` y no modifica el repositorio original.

## Incluido

- `src/eph_genero_tecnologia/`: lectura, calidad, variables y clasificación sectorial.
- `projects/mas-alla-educacion/scripts/`: auditoría EPH y etapas 5–9.
- `tests/`: pruebas automatizadas existentes.
- `docs/`: metodología, diccionario, reproducción y correspondencia de resultados.
- `results/`: tablas y figuras agregadas de etapas 6, 7 y 9B.
- `README.md`, `CITATION.cff`, `pyproject.toml` y `requirements-public.txt`.

## Excluido

Se excluyeron `.git`, `archive/original`, notebooks históricos, microdatos, documentos personales, certificados, presentaciones, inventarios locales, `reports/generated` completo, predicciones individuales y salidas de trabajo no necesarias.

## Controles

- Búsqueda de rutas privadas, credenciales, certificados, datos identificatorios y referencias al inventario local en los archivos incluidos.
- Confirmación de que no se copiaron microdatos ni `.git`.
- `26 passed` en la suite local del proyecto original.
- Etapas 5–8 reproducidas desde los cuatro ZIP EPH locales; diferencia cero entre microdatos originales y CSV armonizado.
- La etapa 9 se representa mediante sus resultados agregados 9B validados, pero requiere ejecución integral en entorno limpio antes de afirmar reproducibilidad completa.

## Pendientes materiales

1. Confirmar afiliación institucional y ORCID de Natalia B. Calcabrini.
2. Obtener aprobación de autores para una licencia; no se asignó ninguna.
3. Repetir etapa 9 en clon limpio, generar lockfile y conservar manifiesto de hashes de las cuatro descargas.
4. Revisar derechos de cualquier tabla o figura que se publique junto con el artículo.
