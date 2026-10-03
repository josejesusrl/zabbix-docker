# ISP gateway fast ping

> **Fichero:** `zabbix_templates/isp_gateway_fast_ping.yaml` · **Catálogo:** [plantillas](../plantillas.md)

**Para:** los gateways de los proveedores de internet (grupo *Proveedores de internet*), **junto con** *ICMP Ping*. Detecta cortes de menos de un minuto: *ICMP Ping* solo comprueba una vez por minuto y avisa tras 3 fallos, así que un corte de 30 s entre dos comprobaciones no se ve (pasó el 2026-10-01 a las 22:56 con Coefi01).

Items: ping de `{$ISP.PING.COUNT}` (3) paquetes cada `{$ISP.PING.INTERVAL}` (**5 s**), y su pérdida.

| Trigger | Severidad | Para | Cuándo |
|---|---|---|---|
| Corte del proveedor: el gateway no responde | High | **Likson** | Pérdida media de más de `{$ISP.CUT.LOSS}` (33 %) en 1 minuto: corte real. Una comprobación aislada fallida (un 8 % del minuto) no lo abre. Se resuelve por debajo de `{$ISP.CUT.LOSS.RECOVERY}` (10 %). Depende de *EDGE 01: Unavailable by ICMP ping* |
| Pérdida intermitente hacia el gateway | Information (no notifica) | Registro | `{$ISP.LOSS.CHECKS}` (3) comprobaciones con pérdida en 5 min |
| Aviso al proveedor: gateway sin respuesta más de 5 min | Information | **Proveedor** | Ninguna comprobación respondió durante 5 minutos seguidos. Etiqueta `aviso_proveedor` |
| Aviso al proveedor: pérdida alta hacia el gateway durante 5 min | Information | **Proveedor** | Pérdida media de `{$ISP.PROVIDER.LOSS}` (50 %) o más durante 5 min. Se resuelve por debajo de `{$ISP.PROVIDER.LOSS.RECOVERY}` (20 %). Depende del anterior |

Los avisos para el proveedor son *Information* para que Likson no reciba el mismo aviso dos veces: Likson ya recibe *Corte del proveedor*. Solo los envía la acción del proveedor ([avisar al proveedor](../procedimientos/avisar-proveedor.md)). Los cortes de pocos segundos no avisan ni a Likson ni al proveedor; quedan registrados en *Latest data* (`Pérdida en ping rápido`).

Criterios del 2026-10-03: avisar a Likson solo de cortes reales (más del 33 % de pérdida en 1 minuto) y al proveedor solo de cortes de más de 5 minutos o de pérdida del 50 % o más durante 5 minutos. La pérdida suelta de 1 paquete de 3 es habitual (unas 30 veces al día).

*ICMP Ping: Unavailable by ICMP ping* del gateway depende de *Corte del proveedor*, para que un corte largo no avise dos veces. El número de comprobaciones de *Corte* es fijo (`#2`): Zabbix no admite una macro en ese parámetro.

