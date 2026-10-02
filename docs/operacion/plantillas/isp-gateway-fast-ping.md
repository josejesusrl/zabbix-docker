# ISP gateway fast ping

> **Fichero:** `zabbix_templates/isp_gateway_fast_ping.yaml` · **Catálogo:** [plantillas](../plantillas.md)

**Para:** los gateways de los proveedores de internet (grupo *Proveedores de internet*), **junto con** *ICMP Ping*. Detecta cortes de menos de un minuto: *ICMP Ping* solo comprueba una vez por minuto y avisa tras 3 fallos, así que un corte de 30 s entre dos comprobaciones no se ve (pasó el 2026-10-01 a las 22:56 con Coefi01).

Items: ping de `{$ISP.PING.COUNT}` (3) paquetes cada `{$ISP.PING.INTERVAL}` (10 s), y su pérdida.

| Trigger | Severidad | Cuándo |
|---|---|---|
| Corte del proveedor: el gateway no responde | High | 2 comprobaciones seguidas sin ninguna respuesta (unos 20 s). Se resuelve con 3 correctas. Depende de *EDGE 01: Unavailable by ICMP ping* |
| Pérdida intermitente hacia el gateway | Warning | `{$ISP.LOSS.CHECKS}` (3) comprobaciones con pérdida en 5 min. Depende del anterior y de EDGE 01 |

*ICMP Ping: Unavailable by ICMP ping* del gateway depende de *Corte del proveedor*, para que un corte largo no avise dos veces. El número de comprobaciones de *Corte* es fijo (`#2`): Zabbix no admite una macro en ese parámetro.

Los dos triggers llevan la etiqueta `aviso_proveedor` con el texto que recibe el proveedor ([avisar al proveedor](../procedimientos/avisar-proveedor.md)).
