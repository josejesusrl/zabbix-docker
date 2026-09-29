@AGENTS.md

## Recordatorios para Claude Code

- Antes de escribir código para la API de Zabbix, revisa `agents/scripts/` (catálogo en `agents/scripts/README.md`) y reutiliza o amplía esos scripts: genéricos, documentados, SOLID/KISS/DRY (`AGENTS.md`, regla 8).
- Ejecútalos con `printf '%s\n' "$TOKEN" | agents/scripts/run_remote.sh SCRIPT ...` y usa `--dry-run` antes de cualquier escritura. Las escrituras exigen un respaldo de menos de 60 min (regla 1).
- Los cambios en `agents/scripts/` se agrupan en un solo commit al final de la sesión.
