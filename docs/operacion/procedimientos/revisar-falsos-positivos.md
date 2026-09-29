# Revisar falsos positivos y salud del monitoreo

> **Cuándo:** tras dar de alta equipos, tras cambios de plantillas y periódicamente.
> **Requisitos:** respaldo reciente antes de cualquier cambio ([AGENTS.md](../../../AGENTS.md), regla 1). Todos los pasos se pueden hacer desde la interfaz web.

Conviene hacerlo tras cada alta de equipos y periódicamente:
1. *Monitoring → Problems* con *Show: History* de las últimas 24 h, agrupando por trigger. Un trigger que se abre muchas veces indica umbral mal ajustado o *flapping*. Por API: `agents/scripts/zbx_events.py --hours 24`.
2. *Data collection → Hosts*: iconos de disponibilidad en rojo e items no soportados. Por API: `zbx_host_status.py --details`.
3. Log del server: `docker compose --env-file .env --env-file server.env logs --since 12h zabbix-server | grep -iE "timed out|not supported|failed"`. Muchos *timed out* de un equipo = equipo sobrecargado o lecturas demasiado grandes ([Añadir un router MikroTik](anadir-router-mikrotik.md), NAS).
4. Corregir con los mecanismos de la documentación de operación (macros, dependencias, *overrides*). Desactivar un objeto solo si es inútil por diseño, y registrarlo en el [registro](../registro.md).

## Con scripts (opcional)

`zbx_events.py --hours 24`, `zbx_host_status.py --details`, `zbx_close_problems.py`, `zbx_set_status.py`. Ver [agents/scripts/README.md](../../../agents/scripts/README.md).
