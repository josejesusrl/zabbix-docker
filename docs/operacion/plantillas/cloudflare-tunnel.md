# Cloudflare Tunnel by HTTP

> **Fichero:** `zabbix_templates/cloudflared_tunnel.yaml` · **Catálogo:** [plantillas](../plantillas.md)

**Para:** el host **Zabbix server**. Vigila el conector `cloudflared` que publica la web ([acceso externo](../../despliegue/acceso-externo.md)). El Zabbix server lee las métricas Prometheus de `http://cloudflared:2000/metrics` por la red Docker `frontend`, sin agente ni interfaz.

| Trigger | Severidad | Cuándo |
|---|---|---|
| Cloudflared: Tunnel connector not responding | High | Sin métricas durante 5 min: contenedor parado o colgado |
| Cloudflared: Tunnel down, public web not reachable | High | 0 conexiones con Cloudflare durante 3 min (Internet caído, token revocado). Depende del anterior |
| Cloudflared: Tunnel degraded | Warning | Menos de `{$CLOUDFLARED.CONN.MIN}` (4) conexiones durante 15 min. Depende del anterior |

Macros: `{$CLOUDFLARED.METRICS.URL}` (`http://cloudflared:2000`) y `{$CLOUDFLARED.CONN.MIN}` (4). Si cae Internet, las alertas por Telegram y Gmail tampoco salen hasta que vuelva.
