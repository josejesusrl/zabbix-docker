# Ubiquiti AirOS 8 wireless by SNMPv1

> **Fichero:** `zabbix_templates/ubiquiti_airos8_wireless.yaml` · **Catálogo:** [plantillas](../plantillas.md)

**Para:** APs Ubiquiti airMAX AC con airOS 8 (LAP-GPS, LiteAP, Rocket AC, Prism…). Se usa **junto con** la oficial *Ubiquiti AirOS by SNMP*, que aporta CPU, memoria, uptime y ping.
**Recoge:** clientes conectados, señal, ruido, CCQ, velocidades, ancho de canal, frecuencia, potencia, airMAX, GPS (fix, satélites, HDOP), tráfico de `eth0` y `ath0` y, por cada cliente, señal, distancia, CCQ, CINR, capacidad, velocidades y tiempo conectado.

| Trigger | Severidad | Cuándo | Se resuelve |
|---|---|---|---|
| AP has no connected clients | Average | Tenía clientes en la última hora y ahora tiene 0 | Al volver a tener clientes |
| High noise floor | Warning | Ruido > `{$UBNT.NOISE.MAX.WARN}` (-80 dBm) durante 15 min | Solo |
| GPS: Weak or lost signal | Warning | < `{$UBNT.GPS.SATS.MIN}` (4) satélites durante 10 min | Solo |
| Client …: Very weak signal | High | Señal del cliente < `{$UBNT.STA.SIGNAL.MIN.CRIT}` durante 5 min (p. ej. lluvia). **Desactivado con 0** (defecto) | Cuando la señal se mantiene 30 min al menos `{$UBNT.STA.SIGNAL.HYST}` (3 dB) por encima del umbral |
| Client …: Weak signal | Warning | Señal del cliente < `{$UBNT.STA.SIGNAL.MIN.WARN}` (-75 dBm) durante 15 min. Silenciado si hay *Very weak signal* | Cuando la señal se mantiene 15 min 3 dB por encima del umbral |
| Client …: Low TX / RX capacity | High | Capacidad airMAX de TX o RX con ese cliente < `{$UBNT.STA.TXCAP.MIN}` / `{$UBNT.STA.RXCAP.MIN}` (Mbps) durante 10 min. **Desactivado con 0** (defecto); se activa por host o por cliente, normalmente en enlaces PTP | Cuando la capacidad se mantiene 10 min por encima del mínimo |
| Interface eth…: Speed changed | High | Cambia la velocidad Ethernet negociada de `eth0` (p. ej. 1000 → 100 Mbps: cable, conector o PoE). Solo se crea para interfaces `eth*` (regla *override* del descubrimiento): en airOS 6 `ath0` reporta una velocidad de radio que no debe vigilarse | Manualmente |

| Macro | Defecto | Uso |
|---|---|---|
| `{$UBNT.NOISE.MAX.WARN}` | -80 | Umbral de ruido |
| `{$UBNT.STA.SIGNAL.MIN.WARN}` | -75 | Umbral de señal de cliente. Por cliente: `{$UBNT.STA.SIGNAL.MIN.WARN:"<nombre del cliente>"}` |
| `{$UBNT.GPS.SATS.MIN}` | 4 | **Poner `0` en APs sin GPS**: devuelven 0 satélites y la alerta saltaría siempre |
| `{$UBNT.IF.MATCHES}` | `^(eth0\|ath0)$` | Interfaces con tráfico |
| `{$UBNT.STA.TXCAP.MIN}` / `{$UBNT.STA.RXCAP.MIN}` | 0 | Capacidad mínima en Mbps (0 = desactivado). Contexto por cliente: `{$UBNT.STA.TXCAP.MIN:"<nombre del cliente>"}` |
| `{$UBNT.STA.SIGNAL.MIN.CRIT}` | 0 | Señal crítica en dBm (0 = desactivado) |
| `{$UBNT.STA.SIGNAL.HYST}` | 3 | dB que la señal debe recuperar por encima del umbral para cerrar el problema. Evita avisos repetidos cuando la señal oscila (lluvia) |

**Items con nombre fijo para dashboards:** *Clients: minimum signal*, *Clients: minimum TX capacity* y *Clients: minimum RX capacity* (items calculados): el peor valor entre los clientes, o el otro extremo en un enlace PTP. Las tablas de dashboard necesitan el mismo nombre de item en todos los hosts.
