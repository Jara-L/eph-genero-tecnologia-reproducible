# Dictamen de portabilidad

Fecha: 2026-11-01. Proyecto auditado: distribución independiente de código científico. El repositorio original no se utilizó ni modificó durante esta revisión.

## Dictamen

**PARTIAL**

La distribución es reproducible en el entorno previamente validado y contiene código, dependencias directas fijadas, pruebas y resultados agregados. No se certifica todavía la portabilidad completa con un intérprete CPython independiente de Anaconda porque no fue posible instalar un CPython 3.13.9 independiente ni generar un lockfile de `uv` en esta red.

## Evidencia del sistema

- `uv`: `0.11.7`.
- `python` predeterminado: Anaconda Python 3.13.9; `sys.base_prefix` apunta al directorio de instalación de Anaconda.
- CPython independiente encontrado: `3.14.4`, gestionado por uv, con `sys.base_prefix` fuera de Anaconda.
- La distribución declara `requires-python >=3.11,<3.14`; por ello 3.14.4 no se trató como intérprete compatible.

No se encontró una instalación oficial de Python.org 3.13. El registro de Python 3.13 apunta únicamente a Anaconda; `python.exe`, `python3.exe` y `py.exe` bajo `WindowsApps` son alias de Microsoft Store, no una instalación utilizable.

## TLS

Se intentó:

```powershell
$env:UV_SYSTEM_CERTS = "true"
$env:UV_NATIVE_TLS = "true"
uv python install 3.13.9
```

La descarga falló con `invalid peer certificate: UnknownIssuer` al acceder al artefacto oficial de GitHub. No se utilizó `--allow-insecure-host`, no se deshabilitó la verificación TLS y no se alteró el almacén de certificados.

`uv lock --offline` tampoco pudo generar `uv.lock` porque `matplotlib` y demás índices no estaban disponibles en la caché local. El archivo `requirements-public.txt` mantiene las versiones directas documentadas, pero no sustituye a un lockfile transitivo.

## Instalación recomendada desde Python.org

Descargar el instalador oficial de [Python 3.13 para Windows](https://www.python.org/downloads/windows/) y elegir **Windows installer (64-bit)**. En el instalador:

1. seleccionar instalación personalizada para no reemplazar Anaconda;
2. instalar para el usuario actual en una carpeta separada, por ejemplo `%LocalAppData%\\Programs\\Python\\Python313`;
3. activar `pip` y el lanzador `py`, sin agregar Anaconda al `PATH`;
4. verificar con la ruta completa:

```powershell
& "$env:LocalAppData\Programs\Python\Python313\python.exe" --version
```

Después, desde la distribución:

```powershell
$cp = "$env:LocalAppData\Programs\Python\Python313\python.exe"
& $cp -m venv ..\IATA_publicacion_repro_env
& ..\IATA_publicacion_repro_env\Scripts\python.exe -c "import sys; print(sys.executable); print(sys.base_prefix)"
```

`sys.base_prefix` debe apuntar a la instalación Python.org, no a Anaconda. Antes de resolver dependencias, revisar y limpiar únicamente variables heredadas que apunten al entorno Anaconda:

```powershell
Get-ChildItem Env:SSL_CERT_FILE,Env:SSL_CERT_DIR,Env:UV_SYSTEM_CERTS -ErrorAction SilentlyContinue
```

No establecer `SSL_CERT_FILE` ni `SSL_CERT_DIR` a rutas de Anaconda. Mantener la verificación TLS activa y usar `UV_SYSTEM_CERTS=true` solo si la infraestructura de certificados del sistema está correctamente configurada.

## Reproducción científica previamente verificada

La ejecución independiente ya documentada en `docs/informe_reproduccion_independiente.md` produjo desde los cuatro ZIP EPH:

- 178.474 registros originales;
- 73.863 observaciones finales;
- M1, M2 y M3 convergentes;
- 60/60 réplicas multinomiales convergentes por modelo;
- Kitagawa 19 sectores con 835 réplicas válidas;
- las seis brechas marginales dentro de 0,00011 pp de 9B.

Esa ejecución usó un entorno virtual con `site-packages` aislado, pero su intérprete base procedía de Anaconda. En esta auditoría no se repitió la estimación econométrica porque la distribución final ya no contiene microdatos, resultados generados ni un entorno instalado, y el CPython independiente compatible no pudo instalarse sin resolver el problema TLS.

## Condiciones para alcanzar PASS

1. Corregir el certificado raíz/intermedio de la red Windows o proporcionar un mirror HTTPS cuyo certificado sea confiable.
2. Instalar CPython 3.13.9 independiente y demostrar `sys.executable` y `sys.base_prefix` fuera de Anaconda.
3. Ejecutar `uv lock` y conservar `uv.lock` junto al código.
4. Crear un entorno desde ese lockfile, descargar los cuatro ZIP EPH y repetir etapas 5–9.
5. Confirmar nuevamente 26 pruebas, las seis brechas, Kitagawa, convergencia y bootstrap.

La distribución final no contiene `.venv`, microdatos, cachés, credenciales ni archivos personales.
