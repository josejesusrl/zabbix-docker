# Crear o modificar una plantilla propia

> **Cuándo:** al crear una plantilla nueva o cambiar una de `zabbix_templates/`.
> **Requisitos:** respaldo reciente antes de cualquier cambio ([AGENTS.md](../../../AGENTS.md), regla 1). Todos los pasos se pueden hacer desde la interfaz web.

1. Editar el YAML en `zabbix_templates/` (reglas de formato en [AGENTS.md](../../../AGENTS.md), regla 6), hacer commit y push, y documentar el cambio en la documentación de operación.
2. Respaldo en el servidor.
3. *Data collection → Templates → Import* → elegir el YAML. Marcar **Update existing** y **Create new**. Para que se eliminen items, triggers o prototipos que ya no están en el YAML, marcar también **Delete missing** en *Items*, *Discovery rules* y *Triggers*.
4. Verificar en un host que la usa: items con datos y sin no soportados nuevos.

En las expresiones de trigger, el número de valores de una función (`#3`) debe ser un número fijo: `#{$MACRO}` no es válido. Al importar, Zabbix descarta sin error los triggers con expresión no válida; `zbx_import_template.py` lo comprueba y avisa.

No editar las plantillas propias desde la interfaz: el cambio se perdería al reimportar el YAML. Las plantillas oficiales tampoco se editan; se ajustan con macros de host.

## Con scripts (opcional)

`zbx_import_template.py` (con `--delete-missing` para eliminar lo que ya no está en el YAML). Ver [agents/scripts/README.md](../../../agents/scripts/README.md).
