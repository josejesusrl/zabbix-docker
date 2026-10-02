# Likson KPIs

> **Fichero:** `zabbix_templates/likson_kpis.yaml` · **Catálogo:** [plantillas](../plantillas.md)

**Para:** el host **KPI Likson** (sin interfaz, grupo *Likson KPIs*). Items calculados a partir de otros hosts para el dashboard: clientes conectados (total de APs), APs en línea y totales, y CPU media de EDGE 01, NAS-01 y NAS-03.
Sus fórmulas usan el grupo *Access Points PPPoE Clients* y el ***Host name* técnico** `EDGE 01`, `NAS-01`, `NAS-03`, no el visible: si cambian, actualizar la plantilla. Si un item queda *UNSUPPORTED* con *no input data for function*, el *Host name* no coincide ([solución de problemas](../solucion-de-problemas.md)). Sin triggers.
