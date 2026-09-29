# Añadir un switch con vigilancia de puertos

> **Cuándo:** cuando los puertos de un switch son críticos (desconexiones, flapping, cambios de velocidad).
> **Requisitos:** respaldo reciente antes de cualquier cambio ([AGENTS.md](../../../AGENTS.md), regla 1). Todos los pasos se pueden hacer desde la interfaz web.

1. En el switch: activar SNMP (v2c) con la comunidad de lectura, accesible desde 192.168.0.191.
2. *Create host*: grupo `Routers & Switches Likson`, interfaz **SNMP** (SNMPv2, `{$SNMP_COMMUNITY}`).
3. **Templates:** la del fabricante (p. ej. `TP-LINK by SNMP`) + `Switch port changes by SNMP`.
4. **Macros:** `{$IFCONTROL}` = `0`. En TP-Link, `{$PORT.IFNAME.NOT_MATCHES}` = `^(<|Vlan-interface)`.
5. Dependencias ([Configurar las dependencias de un host](dependencias.md)).
6. **Verificar:** en *Latest data*, items *Port …: Operational status / Negotiated speed* con valores (`up`/`down`, 1000/100 Mbps). Desconectar un puerto no crítico 5 s → *Port X: Disconnected* y luego resuelto.

## Con scripts (opcional)

`zbx_create_snmp_host.py` y `zbx_latest.py --key port.` para verificar. Ver [agents/scripts/README.md](../../../agents/scripts/README.md).
