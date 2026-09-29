# Catálogo de plantillas

## Plantillas propias (en `zabbix_templates/`)

### Mimosa C5C by SNMP — `mimosa_c5c.yaml`
**Para:** radios Mimosa C5C (y familia B5/C5) en enlaces PTP, con SNMPv2. Se usa **junto con** la oficial *Network Generic Device by SNMP*, que aporta interfaces con tráfico de 64 bits, ping, disponibilidad SNMP y reinicios, y con *Switch port changes by SNMP* para el puerto Ethernet del radio.
**Recoge:** estado y uptime del enlace, modo (AP/estación), potencia RX/TX total, potencia RX, ruido y SNR por polarización (H/V), velocidad PHY, MCS y EVM por stream, tasa de errores de paquete (PER) TX/RX, frecuencia, ancho de canal, temperatura, firmware y número de serie.

| Trigger | Severidad | Cuándo | Se resuelve |
|---|---|---|---|
| Wireless link is disconnected | High | El enlace radio cae | Al reconectar |
| Wireless link was re-established | Warning | El enlace lleva menos de `{$MIMOSA.LINK.UPTIME.MIN}` s (600) conectado: hubo un corte | Solo, pasados 10 min |
| Very low RX power | High | Potencia RX total < `{$MIMOSA.RX.POWER.MIN.CRIT}` durante 10 min | Solo |
| Low RX power | Warning | < `{$MIMOSA.RX.POWER.MIN.WARN}` durante 10 min. Silenciado si hay crítico | Solo |
| RX chain imbalance | Warning | Diferencia H/V > `{$MIMOSA.CHAIN.DIFF.MAX}` (6 dB) durante 30 min: cable, conector o alineación | Solo |
| Low SNR | Warning | SNR de alguna cadena < `{$MIMOSA.SNR.MIN.WARN}` (12 dB) durante 15 min | Solo |
| High noise | Warning | Ruido > `{$MIMOSA.NOISE.MAX.WARN}` (-85 dBm) durante 15 min: interferencia | Solo |
| High packet error rate | Warning | PER TX o RX > `{$MIMOSA.PER.MAX.WARN}` (10 %) durante 15 min | Solo |
| Low TX PHY rate / Low RX PHY rate | High | Velocidad PHY total (suma de los 2 streams) de ese sentido < `{$MIMOSA.PHY.MIN.WARN}` (200 Mbps) durante 10 min: la modulación cayó y el troncal perdió capacidad | Solo, al recuperarse |
| Temperature is high / critical | Warning / High | > `{$MIMOSA.TEMP.MAX.WARN}` (70 °C) / `{$MIMOSA.TEMP.MAX.CRIT}` (80 °C) durante 5 min | Solo |
| Firmware version has changed | Information | Cambio de firmware (solo registro, no notifica) | Sola |

Los triggers de potencia, SNR, ruido, desequilibrio, PER y velocidad PHY se silencian mientras el enlace está caído. Cada extremo vigila su TX y su RX, así que con los dos hosts se cubren ambos sentidos del enlace desde el emisor y desde el receptor. Se usa la velocidad PHY por sentido y no la velocidad de `wifi0`, que es una sola cifra sin dirección.
**Umbrales de potencia por enlace:** `{$MIMOSA.RX.POWER.MIN.WARN}` ≈ señal de diseño − 6 dB y `CRIT` ≈ diseño − 11 dB. Para `Lk_Trunk_01_A` (diseño -65 dBm): -71 / -76.

### Ubiquiti AirOS 8 wireless by SNMPv1 — `ubiquiti_airos8_wireless.yaml`
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

### Ubiquiti airMAX M (airOS 6) wireless by SNMPv1 — `ubiquiti_airmax_m_airos6_wireless.yaml`
**Para:** equipos airMAX M con airOS 6 (Rocket M5, NanoStation M…). Es la misma plantilla que la de airOS 8, pero **sin** GPS, CINR ni capacidad de cliente, que son exclusivos de AC. Añade **airMAX quality y capacity** del AP y por cliente, que en airMAX M son las mejores medidas de calidad.
Mismos triggers y macros, salvo los de GPS y capacidad (airOS 6 no la publica); incluye el de cambio de velocidad de `eth0`. El CCQ viene en porcentaje directo. No recoge el tiempo de conexión del cliente (limitación de SNMPv1 en airOS 6). Tiene el item fijo *Clients: minimum signal*.

### MikroTik link traps by SNMP — `mikrotik_link_traps.yaml`
**Para:** routers MikroTik, junto con su plantilla oficial de modelo. Alerta **al instante** cuando cae un enlace, a partir del trap `linkDown`.
**Requisitos en el router:** traps configurados y `src-address` igual a la IP del host en Zabbix ([Añadir un router MikroTik](procedimientos/anadir-router-mikrotik.md)).

| Trigger | Severidad | Cuándo | Se resuelve |
|---|---|---|---|
| Interface X(comentario): Link down (SNMP trap) | Average | Llega un `linkDown` con la interfaz habilitada. Si se deshabilita a mano, no alerta | Con el trap `linkUp`, o manualmente |

| Macro | Defecto | Uso |
|---|---|---|
| `{$LINKTRAP.IFALIAS.MATCHES}` | `.+` | Solo interfaces **con comentario** en RouterOS. Para quitar una interfaz, borrar su comentario o ajustar la regex (p. ej. `^(?!.*RESERVED)`) |
| `{$LINKTRAP.IFNAME.NOT_MATCHES}` | `^<` | Excluye interfaces dinámicas (PPPoE, túneles) |

Complementa, no sustituye, el *Link down* por consulta de la plantilla oficial (cada pocos minutos). Si el trap se pierde, la consulta lo detecta. Una misma caída puede generar los dos avisos.

### Switch port changes by SNMP — `switch_port_changes.yaml`
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

### Linux hwmon temperature by Zabbix agent 2 — `linux_hwmon_temperature.yaml`
**Para:** servidores Linux físicos con Agent 2. Descubre cada sensor de temperatura del kernel (CPU, GPU, NVMe…).
**Requisitos en el servidor:** lm-sensors instalado (`sensors-detect`) y los ficheros `zabbix_agentd.d/sensors_hwmon.conf` y `sensors_hwmon.sh` en el directorio `Include` del agente. En el servidor Zabbix ya están.

| Trigger | Severidad | Cuándo |
|---|---|---|
| Temperature X is critical | High | ≥ `{$TEMP.CRIT}` (85 °C) durante 5 min |
| Temperature X is high | Warning | ≥ `{$TEMP.WARN}` (75 °C) durante 5 min. Silenciado si ya hay crítico |
| Temperature X: no data for 30m | Warning | El sensor deja de reportar |

Umbrales por chip: `{$TEMP.CRIT:"nvme"}=70`.

### Likson KPIs — `likson_kpis.yaml`
**Para:** el host **KPI Likson** (sin interfaz, grupo *Likson KPIs*). Items calculados a partir de otros hosts para el dashboard: clientes conectados (total de APs), APs en línea y totales, y CPU media de EDGE 01, NAS-01 y NAS-03.
Sus fórmulas usan el grupo *Access Points PPPoE Clients* y los nombres de host `EDGE 01`, `NAS-01`, `NAS-03`: si cambian, actualizar la plantilla. Sin triggers.

### Cloudflare Tunnel by HTTP — `cloudflared_tunnel.yaml`
**Para:** el host **Zabbix server**. Vigila el conector `cloudflared` que publica la web ([acceso externo](../despliegue/acceso-externo.md)). El Zabbix server lee las métricas Prometheus de `http://cloudflared:2000/metrics` por la red Docker `frontend`, sin agente ni interfaz.

| Trigger | Severidad | Cuándo |
|---|---|---|
| Cloudflared: Tunnel connector not responding | High | Sin métricas durante 5 min: contenedor parado o colgado |
| Cloudflared: Tunnel down, public web not reachable | High | 0 conexiones con Cloudflare durante 3 min (Internet caído, token revocado). Depende del anterior |
| Cloudflared: Tunnel degraded | Warning | Menos de `{$CLOUDFLARED.CONN.MIN}` (4) conexiones durante 15 min. Depende del anterior |

Macros: `{$CLOUDFLARED.METRICS.URL}` (`http://cloudflared:2000`) y `{$CLOUDFLARED.CONN.MIN}` (4). Si cae Internet, las alertas por Telegram y Gmail tampoco salen hasta que vuelva.

## Plantillas oficiales en uso y ajustes necesarios

| Plantilla | Para | Ajustes |
|---|---|---|
| *MikroTik \<modelo\> by SNMP* | Routers MikroTik. Usar la del modelo exacto; si no existe, *Mikrotik by SNMP* | En concentradores PPPoE, excluir sesiones ([Añadir un router MikroTik](procedimientos/anadir-router-mikrotik.md)) |
| *TP-LINK by SNMP* | Switches TP-Link | Con *Switch port changes*: `{$IFCONTROL}=0` |
| *Ubiquiti AirOS by SNMP* | APs Ubiquiti (sistema: CPU, memoria, ping) | En airOS 8, *Firmware version* y *Hardware model name* quedan como no soportados (airOS 8 no publica esos datos). Es normal |
| *Linux by Zabbix agent* | Servidores Linux | Si el agente corre en un contenedor con `/rootfs`: macros de sistemas de archivos ([Añadir un servidor Linux](procedimientos/anadir-servidor-linux.md)) |
| *Docker by Zabbix agent 2* | Servidores con Docker | El agente necesita acceso a `/var/run/docker.sock`. Solo descubre los contenedores en ejecución |
| *Website certificate by Zabbix agent 2* | Caducidad del certificado autofirmado del origen (host Zabbix server); el público lo renueva Cloudflare | `{$CERT.WEBSITE.HOSTNAME}`, `{$CERT.WEBSITE.IP}=127.0.0.1`, `{$CERT.EXPIRY.WARN}=14` |

## Particularidades por tipo de equipo

Resumen de lo que hay que recordar al dar de alta cada tipo de equipo. El detalle está en las secciones anteriores y en los [procedimientos](../README.md#añadir-o-cambiar-equipos).

| Equipo | Particularidad |
|---|---|
| Agent 2 en contenedor (Zabbix server, server-04) | Macros `{$VFS.FS.FSNAME.*}` para ver solo `/rootfs`. Desactivar el checksum de `/etc/passwd` y los usuarios conectados |
| MikroTik | `/snmp src-address` igual a la IP del host en Zabbix, para que los traps se asocien |
| MikroTik concentrador PPPoE | Añadir `\|^<pppoe-` a `{$NET.IF.IFNAME.NOT_MATCHES}` |
| Ubiquiti airOS 8 / airOS 6 | Solo **SNMPv1**. AC sin GPS: `{$UBNT.GPS.SATS.MIN}=0`. airOS 6 usa la variante airMAX M |
| TP-Link | `{$PORT.IFNAME.NOT_MATCHES}=^(<\|Vlan-interface)` y `{$IFCONTROL}=0` con la plantilla de puertos |
| Mimosa C5C (PTP) | SNMPv2. `Network Generic Device by SNMP` + `Mimosa C5C by SNMP` + `Switch port changes by SNMP`. Umbrales de RX según la señal de diseño. El extremo lejano depende del cercano a Zabbix |
| Ubiquiti en enlaces PTP | Umbrales propios de cada enlace como macros de host: `{$UBNT.STA.TXCAP.MIN}` en el AP y `{$UBNT.STA.RXCAP.MIN}` en la estación (Mbps, 0 = desactivado), y la señal. Nombres con `[ ]`: *Host name* sin ellos y `--visible-name` con el nombre exacto |
| Equipos raíz de la topología | Su trigger de disponibilidad depende de *Zabbix server: Interface enp2s0: Link down*, para que una caída de red del servidor no se reporte como caída de toda la red |
| MikroTik NAS con muchas sesiones PPPoE | *Max repetition count* 50 en la interfaz SNMP; desactivar *SNMP walk wireless interfaces* en routers sin radios |
| Problemas de objetos ya no descubiertos o desactivados | Zabbix no los cierra: cerrarlos con comentario (`zbx_close_problems.py`). Cada objeto desactivado a propósito se registra en el [registro](registro.md) |
| Enlaces con problemas largos y conocidos (lluvia) | Etiqueta de host `escalation=off`: la acción de escalada no repite sus *High*. Señal crítica con `{$UBNT.STA.SIGNAL.MIN.CRIT}` y la histéresis `{$UBNT.STA.SIGNAL.HYST}` de la plantilla |
| *Switch port changes* | Requiere SNMPv2 (`ifXTable`): no usar en airOS (SNMPv1), cuyas plantillas ya vigilan la velocidad de `eth0` |
| Cualquier radio con *Switch port changes* | Nunca vigilar interfaces inalámbricas (`wifi*`, `wlan*`, `ath*`): su velocidad es adaptativa. La plantilla ya las excluye por defecto |
