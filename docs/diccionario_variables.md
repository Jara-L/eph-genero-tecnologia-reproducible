# Diccionario analítico

Las columnas originales se leen de las bases individual y hogar de la EPH. La armonización conserva los códigos originales y crea estas variables:

| Variable | Fuente | Definición analítica |
|---|---|---|
| `household_id` | `CODUSU`, `NRO_HOGAR` | Identificador candidato de vivienda-hogar, usado para rotación y bootstrap exploratorio. |
| `person_candidate_id` | `household_id`, `COMPONENTE` | Identificador candidato de persona; no se interpreta como identidad longitudinal cierta. |
| `sex` | `CH04` | Sexo registrado: 1 varones, 2 mujeres. |
| `age` | `CH06` | Edad; el universo exige `age > 14`. |
| `education` | `NIVEL_ED` | Nivel educativo categórico de la EPH. |
| `activity_status` | `ESTADO` | Estado de actividad; ocupación: código 1. |
| `weight_person` | `PONDERA` | Factor de expansión individual trimestral. |
| `cno_code` | `PP04D_COD` | Código CNO normalizado a cinco dígitos. |
| `caes_code` | `PP04B_COD` | Código CAES normalizado a cuatro dígitos. |
| `technology_category` | cuarto dígito de CNO | 1 no tecnológica; 2 operación de máquinas; 3 sistemas informatizados. |
| `sector_provisional` | prefijo de CAES | Sector agregado por `sector.py`; códigos `00xx` quedan sin asignar. |
| `source_quarter` | `ANO4`, `TRIMESTRE` | Trimestre de origen. |
| `weight_pooled` | `PONDERA` | `PONDERA/4` para el promedio temporal de cuatro trimestres. |

Universo final: personas ocupadas de 15 años o más, CNO válido, CAES válido, categoría tecnológica válida y sector asignado.
