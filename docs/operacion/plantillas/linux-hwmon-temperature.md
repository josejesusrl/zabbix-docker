# Linux hwmon temperature by Zabbix agent 2

> **Fichero:** `zabbix_templates/linux_hwmon_temperature.yaml` · **Catálogo:** [plantillas](../plantillas.md)

**Para:** servidores Linux físicos con Agent 2. Descubre cada sensor de temperatura del kernel (CPU, GPU, NVMe…).
**Requisitos en el servidor:** lm-sensors instalado (`sensors-detect`) y los ficheros `zabbix_agentd.d/sensors_hwmon.conf` y `sensors_hwmon.sh` en el directorio `Include` del agente. En el servidor Zabbix ya están.

| Trigger | Severidad | Cuándo |
|---|---|---|
| Temperature X is critical | High | ≥ `{$TEMP.CRIT}` (85 °C) durante 5 min |
| Temperature X is high | Warning | ≥ `{$TEMP.WARN}` (75 °C) durante 5 min. Silenciado si ya hay crítico |
| Temperature X: no data for 30m | Warning | El sensor deja de reportar |

Umbrales por chip: `{$TEMP.CRIT:"nvme"}=70`.
