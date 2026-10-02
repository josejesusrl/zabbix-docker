# Switch port changes by SNMP

> **Fichero:** `zabbix_templates/switch_port_changes.yaml` · **Catálogo:** [plantillas](../plantillas.md)

**Para:** switches cuyos puertos son críticos, de cualquier fabricante. Consulta el estado y la velocidad de todos los puertos Ethernet cada 30 s en una sola lectura SNMP.

| Trigger | Severidad | Cuándo | Se resuelve |
|---|---|---|---|
| Port X: Flapping | High | ≥ `{$PORT.FLAP.COUNT}` (4) cambios de estado en `{$PORT.FLAP.PERIOD}` (10 min) | Solo, cuando cesan los cambios |
| Port X: Disconnected | High | El puerto pasa de conectado a desconectado estando habilitado. Silenciado mientras hay *Flapping* | Al reconectar, o manualmente |
| Port X: Negotiated speed changed | High | Cambia la velocidad con el enlace activo (p. ej. 1000 → 100 Mbps). El título indica ambas velocidades | Manualmente, tras revisar |

| Macro | Defecto | Uso |
|---|---|---|
| `{$PORT.POLL.INTERVAL}` | 30s | Frecuencia de consulta |
| `{$PORT.FLAP.COUNT}` / `{$PORT.FLAP.PERIOD}` | 4 / 10m | Sensibilidad del flapping |
| `{$PORT.IFTYPE.MATCHES}` | `^6$` | Solo puertos Ethernet |
| `{$PORT.IFNAME.NOT_MATCHES}` | `^(<\|wifi\|wlan\|ath\|br[0-9])` | Puertos excluidos: interfaces dinámicas, de radio (su velocidad es la capacidad inalámbrica, que cambia continuamente) y bridges virtuales. En TP-Link: `^(<\|Vlan-interface)` |

Requiere **SNMPv2** (lee `ifXTable`): no sirve para Ubiquiti airOS, que solo responde a SNMPv1. En airOS, el cambio de velocidad de `eth0` lo vigilan sus propias plantillas. Al usarla, poner `{$IFCONTROL}=0` en el host para que el *Link down* de la plantilla del fabricante no duplique los avisos de desconexión. Los cortes de menos de 30 s pueden no detectarse; los repetidos, sí (flapping).
