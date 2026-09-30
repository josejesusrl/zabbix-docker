# Dar de baja un equipo

> **Cuándo:** al apagar temporalmente o retirar un equipo.
> **Requisitos:** respaldo reciente antes de cualquier cambio ([AGENTS.md](../../../AGENTS.md), regla 1). Todos los pasos se pueden hacer desde la interfaz web.

- **Temporal** (equipo apagado o en reparación): *Data collection → Hosts* → estado **Disabled**. Se conserva el historial.
- **Definitiva:** antes, revisar qué hosts dependen de él (etiqueta `uplink`, [inventario](../inventario.md)) y reasignar sus dependencias. Después, **Delete**. Se pierde su historial.
- Actualizar el inventario y la topología de la documentación de operación, y regenerar los [mapas de red](../mapas.md#actualizar-los-mapas-después-de-un-alta-una-baja-o-un-cambio-de-padre).
