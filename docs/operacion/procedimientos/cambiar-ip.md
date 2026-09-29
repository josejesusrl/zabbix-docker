# Cambiar la IP de un equipo

> **Cuándo:** cuando un equipo cambia de IP.
> **Requisitos:** respaldo reciente antes de cualquier cambio ([AGENTS.md](../../../AGENTS.md), regla 1). Todos los pasos se pueden hacer desde la interfaz web.

Las dependencias, el historial y las alertas van ligados al **host**, no a su IP. Cambiar la IP no rompe nada:

1. Respaldo.
2. *Data collection → Hosts* → host → pestaña **Host** → *Interfaces*: nueva IP → **Update**.
3. Si es un MikroTik que envía traps, actualizar también `/snmp set src-address=<nueva IP>`: los traps se asocian por la IP de la interfaz.
4. Si otros equipos filtran por IP la comunicación con Zabbix (comunidades SNMP con `addresses`, `Server=` de agentes), revisar que sigan apuntando a `192.168.0.191`. Solo cambia la IP del equipo monitoreado, no la de Zabbix.
5. Actualizar el inventario de la documentación de operación y **verificar** que el icono SNMP/ZBX vuelve a verde.
